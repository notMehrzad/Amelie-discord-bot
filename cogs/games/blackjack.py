import discord
from discord.ext import commands
from discord import app_commands
from database import db, Session
import random
import asyncio
from cogs.utility.help import HelpData
from core.logHandler import loggerSetup

logger = loggerSetup(__name__)

betLimit = (100, 300)


class Card:
    def __init__(self, rank: int | str, suit: str):
        ranks = (2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K", "A")
        suits = ("H", "C", "D", "S")
        symbols = {"H": "♥️", "C": "♣️", "D": "♦️", "S": "♠️"}
        if rank not in ranks or suit not in suits:
            raise ValueError

        self.rank = rank
        self.suit = suit
        self.symbol = symbols[suit]


class BjHand:
    def __init__(self, card: list[Card], dealers: bool = False):
        self.cards = card
        self.holeCard = True if dealers else False

    def isBlackjack(self):
        return True if len(self.cards) == 2 and self.value == 21 else False

    def isBusted(self):
        return True if self.value > 21 else False

    @property
    def value(self):
        value = 0
        aces = 0
        for card in self.cards:
            if card.rank == "A":
                value += 11
                aces += 1
            elif card.rank in ("K", "Q", "J", 10):
                value += 10
            else:
                value += int(card.rank)

        while value > 21 and aces > 0:
            value -= 10
            aces -= 1

        return value

    def addCard(self, card: Card):
        self.cards.append(card)
        self.holeCard = False

    def __str__(self):
        if not self.holeCard:
            return "   ".join(f"{card.rank}{card.symbol}" for card in self.cards)
        else:
            return f"{self.cards[0].rank}{self.cards[0].symbol}   🎴"


def handStr(dealerHand: BjHand, playerHand: BjHand):
    return str(dealerHand) + "\n\n" + str(playerHand)


def deck_creator(shoe: int = 1, shuffle: bool = True):
    deck: list[Card] = []
    ranks = (2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K", "A")
    suits = ("H", "C", "D", "S")

    # creates the deck
    for _ in range(shoe):
        for rank in ranks:
            for suit in suits:
                deck.append(Card(rank, suit))

    # shuffles the deck
    if shuffle:
        random.shuffle(deck)

    return deck


class Blackjack(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help = HelpData(
        category=HelpData.Category.Games,
        dmOnly=False,
        serverOnly=False,
        subcommands=None,
        permissions=None,
        help=None,
        brief="The traditional BlackJack game.",
        usage="<bet_amount[*optional*]>",
        aliases=["bj"],
    )

    @commands.command(name="blackjack", **Help.to_kwargs)
    async def blackjack(
        self, ctx: commands.Context[commands.Bot], bet: int | str | None = None
    ):
        # if player bets
        if bet:
            # if user enters an invalid bet
            if not isinstance(bet, int):
                return await ctx.reply("Enter a valid integer bet amount.")

            # if player has an active session
            if (ctx.author.id, Session.Types.gambling) in Session.sessions:
                return await ctx.reply(
                    "You have an open gambling session somewhere. Finish that one first and try again."
                )

            # if bet is lower than limit
            if bet < 100:
                return await ctx.reply(
                    "The minimum bet limit for this game is **100**."
                )
            # if bet is higher than limit
            elif bet > 300:
                return await ctx.reply(
                    "The maximum bet limit for this game is **300**."
                )

            # trys to fetch user's balance
            row = await db.fetchone(
                """
                SELECT balance FROM user
                WHERE user_id = ?;
                """,
                (ctx.author.id,),
            )
            # if user doesn't have an account
            if not row:
                return await ctx.reply(
                    "You have no balance account ! Try `/daily` to claim your first daily reward and get your balance account."
                )

            if bet > row["balance"]:
                return await ctx.reply(
                    f"Your desired bet is higher than your current balance. Try `balance` to see your balance."
                )

        Session(
            userId=ctx.author.id, type=Session.Types.gambling
        )  # opens a gambling session for the user
        view = blackjackView(
            ctx, bet if isinstance(bet, int) else 0
        )  # initializes the view
        await view.start()

    @blackjack.error
    async def blackjack_error(
        self, ctx: commands.Context[commands.Bot], error: commands.CommandError
    ):
        try:
            Session.sessions[
                (ctx.author.id, Session.Types.gambling)
            ].close()  # ends the session upon error
        except KeyError:
            pass

        logger.exception(f"❌ something went wrong with blackjack command:")
        await ctx.reply("something went wrong with **blackjack**.")

    # blackjack slash command
    @app_commands.command(name="blackjack", description=Help.brief, extras=Help.extras)
    @app_commands.describe(
        bet="The amount you want to set your initial bet. (max: 300/min: 100)"
    )
    async def slashBlackjack(
        self, interaction: discord.Interaction, bet: int | None = None
    ):
        # if player bets
        if bet:
            # if player has an active session
            if (interaction.user.id, Session.Types.gambling) in Session.sessions:
                return await interaction.response.send_message(
                    "You have an open gambling session somewhere. Finish that one first and try again.",
                    ephemeral=True,
                )

            # if bet is lower than limit
            if bet < 100:
                return await interaction.response.send_message(
                    "The minimum bet limit for this game is **100**.", ephemeral=True
                )
            # if bet is higher than limit
            elif bet > 300:
                return await interaction.response.send_message(
                    "The maximum bet limit for this game is **300**.", ephemeral=True
                )

            # trys to fetch user's balance
            row = await db.fetchone(
                """
                SELECT balance FROM user
                WHERE user_id = ?;
                """,
                (interaction.user.id,),
            )
            # if user doesn't have an account
            if not row:
                return await interaction.response.send_message(
                    "You have no balance account ! Try `/daily` to claim your first daily reward and get your balance account.",
                    ephemeral=True,
                )

            if bet > row["balance"]:
                return await interaction.response.send_message(
                    f"Your desired bet is higher than your current balance. Try `balance` to see your balance.",
                    ephemeral=True,
                )

        Session(
            userId=interaction.user.id, type=Session.Types.gambling
        )  # opens a gambling session for the user
        view = blackjackView(
            interaction, bet if isinstance(bet, int) else 0
        )  # initializes the view
        await view.start()

    @slashBlackjack.error
    async def slashBlackjack_error(
        self, interaction: discord.Interaction, error: Exception
    ):
        try:
            Session.sessions[
                (interaction.user.id, Session.Types.gambling)
            ].close()  # ends the session upon error
        except KeyError:
            pass

        logger.exception(f"❌ something went wrong with /blackjack command:")
        try:
            await interaction.response.send_message(
                "something went wrong with **blackjack**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **blackjack**.", ephemeral=True
            )


class blackjackView(discord.ui.View):
    def __init__(
        self,
        ctx: commands.Context[commands.Bot] | discord.Interaction,
        bet: int,
    ):
        super().__init__(timeout=180)
        if isinstance(ctx, discord.Interaction):
            self.slash = True
            self.interaction = ctx
        else:
            self.slash = False
            self.ctx = ctx
        self.user = self.interaction.user if self.slash else self.ctx.author
        self.bet = bet
        self.outcome = 0
        self.insurance = None
        self.timestamp = discord.utils.utcnow()
        self.embedColor = discord.Color.random()
        self.session = Session.sessions[(self.user.id, Session.Types.gambling)]

        for button in self.children:
            self.remove_item(button)

    async def setBet(self, bet: int, firstBet: bool = False):
        if bet != 0:
            row = await db.fetchone(
                """
                SELECT balance FROM user
                WHERE user_id = ?;
                """,
                (self.user.id,),
            )
            if row:
                if firstBet:
                    await db.execute(
                        """
                        UPDATE user
                        SET balance = ?
                        WHERE user_id = ?;
                        """,
                        (row["balance"] - bet, self.user.id),
                    )
                else:
                    await db.execute(
                        """
                        UPDATE user
                        SET balance = ?
                        WHERE user_id = ?;
                        """,
                        (row["balance"] - (bet - self.bet), self.user.id),
                    )

                self.bet = bet

    @property
    def insuranceStr(self):
        if self.insurance == True:
            if self.dealerHand.isBlackjack():
                return "You accepted the insurance and I got a BlackJack ! You Won the insurance."
            else:
                return "You accepted the insurance and I got not a BlackJack ! You Lost the insurance."
        elif self.insurance == False:
            return "You refused the insurance."

        else:
            return ""

    async def start(self):
        await self.setBet(self.bet, firstBet=True)

        initialEmbed = discord.Embed(
            title="BlackJack 🖤",
            description=(
                f"The BlackJack starts with **{self.bet}** in the pot !"
                "\nAs your Dealer, I may distribute our cards in a sec.."
            ),
            timestamp=self.timestamp,
            color=self.embedColor,
        )
        # sends the initial message
        if self.slash:
            await self.interaction.response.send_message(embed=initialEmbed)
        else:
            self.msg = await self.ctx.reply(embed=initialEmbed)

        self.deck = deck_creator(shoe=6)  # creates a 6-deck shoe
        # distributes the initial 2 cards
        self.playerHand = BjHand([self.deck.pop() for _ in range(2)])
        self.dealerHand = BjHand([self.deck.pop() for _ in range(2)], dealers=True)

        await asyncio.sleep(3)  # a short delay

        # dealer must peek the hole card
        if self.dealerHand.cards[0].rank in ("A", "K", "Q", "J", 10):
            # if the face up card is an ace, dealer offers insurance first
            if self.dealerHand.cards[0].rank == "A":
                await self.insuranceOffer()
            # skips the insurance otherwise
            else:
                await self.holePeek()
        else:
            await self.playersTurn()

    async def insuranceOffer(self):
        # adds the related buttons
        self.add_item(self.refuse)
        self.add_item(self.accept)

        insuranceEmbed = discord.Embed(
            title="BlackJack 🖤",
            description=(
                "Cards have been distributed and it seems like my first card is an ACE !"
                "\nI'm offering you an Insurance (a side bet) with a cost of the half amount your bet before I peek over my hole card."
                "\nIf I peek my hole card and turns out I got BlackJack, you'll win an amount equal to your bet."
                "\nIf I get not BlackJack, you'll lose half of your bet.\n"
            )
            + handStr(self.dealerHand, self.playerHand),
        )
        if self.slash:
            await self.interaction.edit_original_response(
                embed=insuranceEmbed, view=self
            )
        else:
            await self.msg.edit(embed=insuranceEmbed, view=self)

    @discord.ui.button(label="refuse", style=discord.ButtonStyle.red)
    async def refuse(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't play in this match.", ephemeral=True
            )

        self.refuse.disabled = self.accept.disabled = True
        self.remove_item(self.accept)
        self.remove_item(self.refuse)

        self.insurance = False  # doesn't take the insurance
        await self.holePeek()

    @discord.ui.button(label="accept", style=discord.ButtonStyle.green)
    async def accept(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't play in this match.", ephemeral=True
            )

        self.refuse.disabled = self.accept.disabled = True
        self.remove_item(self.accept)
        self.remove_item(self.refuse)

        self.insurance = True  # takes the insurance for the player
        await self.holePeek()

    async def holePeek(self):
        # if player took the insurance
        if self.insurance == True:
            # if dealer got blackjack
            if self.dealerHand.isBlackjack():
                self.outcome += self.bet
            else:
                self.outcome -= self.bet / 2

        # if dealer got blackjack, match comes to an end
        if self.dealerHand.isBlackjack():
            self.dealerHand.holeCard = False  # reveals the hole card

            # if player got blackjack too
            if self.playerHand.isBlackjack():
                resultEmbed = discord.Embed(
                    title="BlackJack 🖤",
                    description=self.insuranceStr
                    + "\n\nWe both got BlackJack ! It's a push.\n\n"
                    + handStr(self.dealerHand, self.playerHand),
                    timestamp=self.timestamp,
                    color=self.embedColor,
                )
            else:
                self.outcome -= self.bet

                resultEmbed = discord.Embed(
                    title="BlackJack 🖤",
                    description=self.insuranceStr
                    + "\n\nI got BlackJack ! I won this whole darling...\n\n"
                    + handStr(self.dealerHand, self.playerHand),
                    timestamp=self.timestamp,
                    color=self.embedColor,
                )

            await self.payout()

            if self.slash:
                await self.interaction.edit_original_response(
                    embed=resultEmbed, view=None
                )
            else:
                await self.msg.edit(embed=resultEmbed, view=None)

            self.stop()

        # player's turn otherwise
        else:
            await self.playersTurn()

    async def playersTurn(self):
        # if player got blackjack, the match comes to an end
        if self.playerHand.isBlackjack():
            self.outcome += 1.2 * self.bet

            await self.payout()

            self.dealerHand.holeCard = False  # reveals the hole card

            resultEmbed = discord.Embed(
                title="BlackJack 🖤",
                description=self.insuranceStr
                + "\n\nYou got a BlackJack ! You Won this match.\n\n"
                + handStr(self.dealerHand, self.playerHand),
                timestamp=self.timestamp,
                color=self.embedColor,
            )
            if self.slash:
                await self.interaction.edit_original_response(
                    embed=resultEmbed, view=None
                )
            else:
                await self.msg.edit(embed=resultEmbed, view=None)

            self.stop()

        else:
            self.add_item(self.hit)
            self.add_item(self.stand)
            self.add_item(self.surrender)
            if self.playerHand.value in (9, 10, 11):
                self.add_item(self.doubledown)

            playerActionEmbed = discord.Embed(
                title="BlackJack 🖤",
                description=self.insuranceStr
                + (
                    "\n\nSince Neither of us got BlackJack, It's your turn now to decide what to do.\n\n"
                )
                + handStr(self.dealerHand, self.playerHand),
                timestamp=self.timestamp,
                color=self.embedColor,
            )
            if self.slash:
                await self.interaction.edit_original_response(
                    embed=playerActionEmbed, view=self
                )
            else:
                await self.msg.edit(embed=playerActionEmbed, view=self)

    @discord.ui.button(label="hit", style=discord.ButtonStyle.gray)
    async def hit(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't play in this match.", ephemeral=True
            )

        self.surrender.disabled = self.doubledown.disabled = (
            True  # disables surrender and double down buttons
        )
        self.playerHand.addCard(self.deck.pop())  # adds a card to player's hand

        # if player busts, match comes to an end
        if self.playerHand.isBusted():
            self.outcome -= self.bet

            await self.payout()

            self.dealerHand.holeCard = False  # reveals the hole card

            resultEmbed = discord.Embed(
                title="BlackJack 🖤",
                description=self.insuranceStr
                + ("\n\nYou Hit and Bust ! You lost..\n\n")
                + handStr(self.dealerHand, self.playerHand),
                timestamp=self.timestamp,
                color=self.embedColor,
            )
            if self.slash:
                await self.interaction.edit_original_response(
                    embed=resultEmbed, view=None
                )
            else:
                await self.msg.edit(embed=resultEmbed, view=None)

            self.stop()
        else:
            hitEmbed = discord.Embed(
                title="BlackJack 🖤",
                description=self.insuranceStr
                + ("\n\nYou Hit.\n\n")
                + handStr(self.dealerHand, self.playerHand),
                timestamp=self.timestamp,
                color=self.embedColor,
            )
            if self.slash:
                await self.interaction.edit_original_response(embed=hitEmbed, view=self)
            else:
                await self.msg.edit(embed=hitEmbed, view=self)

    @discord.ui.button(label="stand", style=discord.ButtonStyle.gray)
    async def stand(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't play in this match.", ephemeral=True
            )

        await self.dealersTurn()

    @discord.ui.button(label="double down", style=discord.ButtonStyle.blurple)
    async def doubledown(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't play in this match.", ephemeral=True
            )

        await self.setBet(2 * self.bet)

        self.playerHand.addCard(self.deck.pop())  # adds the final card for the player

        # if player busts, match comes to an end
        if self.playerHand.isBusted():
            self.outcome -= self.bet

            await self.payout()

            self.dealerHand.holeCard = False  # reveals the hole card

            resultEmbed = discord.Embed(
                title="BlackJack 🖤",
                description=self.insuranceStr
                + ("\n\nYou Doubled Down and Bust ! You lost it so bad..\n\n")
                + handStr(self.dealerHand, self.playerHand),
                timestamp=self.timestamp,
                color=self.embedColor,
            )
            if self.slash:
                await self.interaction.edit_original_response(
                    embed=resultEmbed, view=None
                )
            else:
                await self.msg.edit(embed=resultEmbed, view=None)

            self.stop()
        else:
            await self.dealersTurn()

    @discord.ui.button(label="surrender", style=discord.ButtonStyle.red)
    async def surrender(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't play in this match.", ephemeral=True
            )

        self.outcome -= self.bet / 2

        await self.payout()

        self.dealerHand.holeCard = False  # reveals the hole card

        surrenderEmbed = discord.Embed(
            title="BlackJack 🖤",
            description=self.insuranceStr
            + ("\n\nYou surrendered and forfeit half of your bet.\n\n")
            + handStr(self.dealerHand, self.playerHand),
            timestamp=self.timestamp,
            color=self.embedColor,
        )
        if self.slash:
            await self.interaction.edit_original_response(
                embed=surrenderEmbed, view=None
            )
        else:
            await self.msg.edit(embed=surrenderEmbed, view=None)

        self.stop()

    async def dealersTurn(self):
        self.dealerHand.holeCard = False  # reveals the hole card

        dealerTurnEmbed = discord.Embed(
            title="BlackJack 🖤",
            description=self.insuranceStr
            + ("\n\nIt's now my turn to play the hole card.\n\n")
            + handStr(self.dealerHand, self.playerHand),
            timestamp=self.timestamp,
            color=self.embedColor,
        )
        if self.slash:
            await self.interaction.edit_original_response(
                embed=dealerTurnEmbed, view=None
            )
        else:
            await self.msg.edit(embed=dealerTurnEmbed, view=None)

        await asyncio.sleep(3)  # a short delay

        # while dealer has <=16, it hits
        while self.dealerHand.value <= 16:
            dealerHitEmbed = discord.Embed(
                title="BlackJack 🖤",
                description=self.insuranceStr
                + (f"\n\nI got {self.dealerHand.value}. I must Hit.\n\n")
                + handStr(self.dealerHand, self.playerHand),
                timestamp=self.timestamp,
                color=self.embedColor,
            )
            if self.slash:
                await self.interaction.edit_original_response(embed=dealerHitEmbed)
            else:
                await self.msg.edit(embed=dealerHitEmbed)

            await asyncio.sleep(2)  # a short delay

            self.dealerHand.addCard(self.deck.pop())  # adds a card to dealer's hand
            # if dealer busts, match comes to an end
            if self.dealerHand.isBusted():
                self.outcome += self.bet

                await self.payout()

                resultEmbed = discord.Embed(
                    title="BlackJack 🖤",
                    description=self.insuranceStr
                    + f"\n\nI got {self.dealerHand.value}. I Bust ! You Won the match.\n\n"
                    + handStr(self.dealerHand, self.playerHand),
                    timestamp=self.timestamp,
                    color=self.embedColor,
                )
                if self.slash:
                    await self.interaction.edit_original_response(
                        embed=resultEmbed, view=None
                    )
                else:
                    await self.msg.edit(embed=resultEmbed, view=None)

                self.stop()
                return

        # showdown
        if self.dealerHand.value == self.playerHand.value:
            resultEmbed = discord.Embed(
                title="BlackJack 🖤",
                description=self.insuranceStr
                + (f"\n\nWe have equal scores ! This match is a push.\n\n")
                + handStr(self.dealerHand, self.playerHand),
                timestamp=self.timestamp,
                color=self.embedColor,
            )
            if self.slash:
                await self.interaction.edit_original_response(
                    embed=resultEmbed, view=None
                )
            else:
                await self.msg.edit(embed=resultEmbed, view=None)

        elif self.playerHand.value > self.dealerHand.value:
            self.outcome += self.bet

            resultEmbed = discord.Embed(
                title="BlackJack 🖤",
                description=self.insuranceStr
                + (f"\n\nYou have a higher score ! You Won.\n\n")
                + handStr(self.dealerHand, self.playerHand),
                timestamp=self.timestamp,
                color=self.embedColor,
            )
            if self.slash:
                await self.interaction.edit_original_response(
                    embed=resultEmbed, view=None
                )
            else:
                await self.msg.edit(embed=resultEmbed, view=None)
        else:
            self.outcome -= self.bet

            resultEmbed = discord.Embed(
                title="BlackJack 🖤",
                description=self.insuranceStr
                + (f"\n\nI have a higher score ! You lost.\n\n")
                + handStr(self.dealerHand, self.playerHand),
                timestamp=self.timestamp,
                color=self.embedColor,
            )
            if self.slash:
                await self.interaction.edit_original_response(
                    embed=resultEmbed, view=None
                )
            else:
                await self.msg.edit(embed=resultEmbed, view=None)

        await self.payout()
        self.stop()

    async def payout(self):
        self.session.close()  # ends the session

        if self.outcome != 0:
            # fetches user's balance
            row = await db.fetchone(
                """
                SELECT balance from user
                WHERE user_id = ?;
                """,
                (self.user.id,),
            )
            if row:
                # updates user balance based on the outcome and returns the bet
                await db.execute(
                    """
                    UPDATE user
                    SET balance = ?
                    WHERE user_id = ?;
                    """,
                    (row["balance"] + self.bet + self.outcome, self.user.id),
                )

    async def on_timeout(self):
        self.outcome -= self.bet / 2

        await self.payout()

        # disables buttons on timeout
        for btn in self.children:
            if isinstance(btn, discord.ui.Button):
                btn.disabled = True

        # sends the timeout message
        toEmbed = discord.Embed(
            title="BlackJack 🖤",
            description="⏰ Game timeout. which results in surrendering and forfeiting half amount of bet.",
            timestamp=self.timestamp,
            color=self.embedColor,
        )
        try:
            if self.slash:
                await self.interaction.edit_original_response(embed=toEmbed, view=self)
            else:
                await self.msg.edit(embed=toEmbed, view=self)
        except discord.NotFound:
            pass

        self.stop()  # stops the interaction upon timeout

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item[discord.ui.View],
    ):
        self.session.close()  # ends the session upon error

        # fetches user's balance
        row = await db.fetchone(
            """
            SELECT balance FROM user
            WHERE user_id = ?;
            """,
            (self.user.id,),
        )
        if row:
            # returns back the bet
            await db.execute(
                """
                UPDATE user
                SET balance = ?
                WHERE user_id = ?;
                """,
                (row["balance"] + self.bet, self.user.id),
            )

        logger.exception(
            f"❌ something went wrong with blackjack interaction - button: {getattr(item, 'label', 'unknown')}"
        )
        try:
            await interaction.response.send_message(
                "something went wrong with **blackjack**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **blackjack**.", ephemeral=True
            )
        except Exception:
            pass

        self.stop()  # stops the interaction upon error


async def setup(bot: commands.Bot):
    await bot.add_cog(Blackjack(bot))
