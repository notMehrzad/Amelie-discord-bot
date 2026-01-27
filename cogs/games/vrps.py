import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from typing import TypedDict
from datetime import datetime
from cogs.games.rps import ChoiceInfo, choices, rpsResult
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)

#specifies each deck info type
class DeckInfo(TypedDict):
    card: ChoiceInfo
    shown: bool
    match: int

people = 40 #number of people to vote in the ballotbox

class Vrps(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help: HelpData = {
        "help": (
            "A game between two people. yet needed a whole class-"
            "\nFirst, everyone in the class draws either a Rock, Paper or Scissors on a card. Then they drop those cards into the ballot box so players can't see them."
            "\nPlayers both draw *three* cards from the box, choose just one, and play *Rock, Paper, Scissors !*."
            "\nIf it's a stalemate, both players draw from the remaining two cards and play again. If it's a stalemate all three times, it's a draw."
            "\nThat makes up one game."
            "\nUnlike normal Rock-Paper-Scissors, players don't always show their entire hand. Trying to read each other under such unfair circumstances is the appeal."
            "\nYou can only play with Amélie herself if you run this game in her dm."
        ),
        "brief": "Classic rock-paper-scissors, but played with predetermined drawings on cards.",
        "usage": "<target[*optional*]>",
        "aliases": ["voterps", "voterockpaperscissors"],
        "extras": {"Category": "Games"}
    }

    @commands.command(
            name = "vrps",
            help = Help["help"],
            brief = Help["brief"],
            usage = Help["usage"],
            aliases = Help["aliases"],
            extras = Help["extras"]
    )
    async def vrps(self, ctx: commands.Context[commands.Bot], user: discord.User | str | None = None):
        #if user mentions an invalid user
        if user and not isinstance(user, discord.abc.User):
            raise commands.BadArgument
        
        #if user mentions itself
        if user and user.id == ctx.author.id:
            return await ctx.reply("You can't play with yourself.")
        
        #if user runs the command in dm
        if not ctx.guild and user and user.id != ctx.me.id:
            return await ctx.reply("You can only play this game with others in a server. (except me!)")
        
        if user and ctx.guild:
            target = ctx.guild.get_member(user.id) #fetches the target member from the server, None if not found
            if not target:
                return await ctx.reply(f"{user.mention} is not a member of this server.")
        else:
            target = None
        
        #if user wants to play with a bot except this bot
        if target and target.bot and target.id != ctx.me.id:
            return await ctx.reply("You can't play with bots. (except me!)")

        #plays with bot if no target is mentioned or the target is the bot itself
        if not target or target.id == ctx.me.id:
            view = VrpsView(ctx = ctx, target = ctx.me, botPlay = True)
        
        #plays with the target
        else:
            view = ReadyView(ctx = ctx, target = target)
            
        await view.start()

    @vrps.error
    async def vrps_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user mentioned an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("User not found. Please mention a valid user.")
        else:
            logger.exception(f"❌ something went wrong with vrps command:")
            await ctx.reply("something went wrong with **vrps**.")

    #vrps slash command
    @app_commands.command(
        name = "vrps",
        description = Help["brief"],
        extras = Help["extras"]
    )
    @app_commands.describe(user = "The user you want to play vrps with.")
    async def slashVrps(self, interaction: discord.Interaction, user: discord.User | None = None):
        #if user mentions itself
        if user and user.id == interaction.user.id:
            return await interaction.response.send_message("You can't play with yourself.", ephemeral = True)
        
        #if user runs the command in dm
        if not interaction.guild and user and user.id != interaction.client.application_id:
            return await interaction.response.send_message("You can only play this game with others in a server. (except me!)", ephemeral = True)
        
        if user and interaction.guild:
            target = interaction.guild.get_member(user.id) #fetches the target member from the server, None if not found
            if not target:
                return await interaction.response.send_message(f"{user.mention} is not a member of this server.", ephemeral = True)
        else:
            target = None
        
        #if user wants to play with a bot except this bot
        if target and target.bot and target.id != interaction.client.application_id:
            return await interaction.response.send_message("You can't play with bots. (except me!)", ephemeral = True)

        #plays with bot if no target is mentioned or the target is the bot itself
        if not target or target.id == interaction.client.application_id:
            if isinstance(interaction.client.user, discord.abc.User):
                #initializing the vrps view
                view = VrpsView(
                    ctx = interaction,
                    target = interaction.client.user,
                    botPlay = True,
                )
                await view.start()
        
        #plays with the target
        else:
            view = ReadyView(ctx = interaction, target = target)
            await view.start()

    @slashVrps.error
    async def slashVrps_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /vrps command:")
        try:
            await interaction.response.send_message("something went wrong with **vrps**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **vrps**.", ephemeral = True)

class ReadyView(discord.ui.View):
    def __init__(self, ctx: commands.Context[commands.Bot] | discord.Interaction, target: discord.abc.User, botPlay: bool = False):
        super().__init__(timeout = 180)
        if isinstance(ctx, discord.Interaction):
            self.slash = True
            self.interaction = ctx
        else:
            self.slash = False
            self.ctx = ctx
        self.user = self.interaction.user if self.slash else self.ctx.author
        self.target = target
        self.botPlay = botPlay
        self.embedColor = discord.Color.random()
        self.timestamp = discord.utils.utcnow()
    
    async def start(self):
        content = f"{self.target.mention}, You're challenged to a game of *Vote Rock, Paper, Scissors !* by {self.user.mention}" #notifies the target
        desc = f"{self.target.mention}, Click `Ready` to start the game."
        
        readyEmbed = discord.Embed(
            title = "Vote Rock, Paper, Scissors !",
            description = desc,
            color = self.embedColor,
            timestamp = self.timestamp
        )
        #sends the initial message
        if self.slash:
            await self.interaction.response.send_message(content = content, embed = readyEmbed, view = self)
        else:
            self.msg = await self.ctx.reply(content = content, embed = readyEmbed, view = self) #saves the message to edit later

    #defining ready button        
    @discord.ui.button(label = "Ready", emoji = "✅", style = discord.ButtonStyle.green)
    async def ready(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        #checks if only the user and target can interact with buttons
        if interaction.user.id not in (self.user.id, self.target.id):
            return await interaction.response.send_message("You can't play in this match.", ephemeral = True)
        
        #if user trys to hit ready
        if interaction.user.id != self.target.id:
            return await interaction.response.send_message(f"{self.target.mention} must get ready to start the game.", ephemeral = True)

        #initializing the vrps view
        view = VrpsView(
            ctx = self.interaction if self.slash else self.ctx,
            target = self.target,
            msg = self.msg if not self.slash else None, #stores the message in vrps view to edit later
            botPlay = self.botPlay,
            embedColor = self.embedColor,
            timestamp = self.timestamp
        )

        if self.slash:
            await self.interaction.followup.send(f"{self.user.mention}, {self.target.display_name} has accepted your challenge !")
        else:
            await self.msg.reply(f"{self.user.mention}, {self.target.display_name} has accepted your challenge !")

        self.stop() #stops the ready view once the target is ready

        await view.start() #starts the vrps view

    async def on_timeout(self):
        self.ready.disabled = True #disables ready button

        timeoutEmbed = discord.Embed(
            title = "Vote Rock, Paper, Scissors !",
            description = f"⏰ The game has timed out! {self.target.mention} didn't get ready.\n*shame on you..*",
            color = discord.Color.dark_gray(),
            timestamp = self.timestamp
        )
        try:
            #sends the timeout message
            if self.slash:
                await self.interaction.edit_original_response(content = None, embed = timeoutEmbed, view = self)
            else:
                await self.msg.edit(content = None, embed = timeoutEmbed, view = self)

        #if message is already deleted
        except discord.NotFound:
            pass

        self.stop() #stops the view upon timeout

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[discord.ui.View]):
        logger.exception(f"❌ something went wrong with vrps ready interaction - button: {getattr(item, "label", "unknown")}")
        try:
            await interaction.response.send_message("something went wrong with **vrps**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **vrps**.", ephemeral = True)
        except Exception:
            pass

        self.stop() #stops the view upon error
    
class VrpsView(discord.ui.View):
    def __init__(self, ctx: commands.Context[commands.Bot] | discord.Interaction, target: discord.abc.User, botPlay: bool = False, msg: discord.Message | None = None, embedColor: discord.Color | None = None, timestamp: datetime | None = None):
        super().__init__(timeout = 180)
        if isinstance(ctx, discord.Interaction):
            self.slash = True
            self.interaction = ctx
        else:
            self.slash = False
            self.ctx = ctx
            self.msg = msg
        self.user = self.interaction.user if self.slash else self.ctx.author
        self.target = target
        self.botPlay = botPlay
        self.embedColor = embedColor or discord.Color.random()
        self.timestamp = timestamp or discord.utils.utcnow()
        self.playersChoice: dict[str, ChoiceInfo | None] = {
            "user": None,
            "target": None
        }
        self.ballotbox: list[ChoiceInfo] = [random.choice(choices) for _ in range(people)] #creates the ballot box
        random.shuffle(self.ballotbox) #shuffles the ballotbox

        #distributing cards
        self.userDeck: list[DeckInfo] = [{"card": self.ballotbox.pop(), "shown": False, "match": 0} for _ in range(3)]
        self.targetDeck: list[DeckInfo] = [{"card": self.ballotbox.pop(), "shown": False, "match": 0} for _ in range(3)]
        #example player deck:
        #[
        #   {
        #       "card": {"name": "Paper", "beats": "Rock", "emoji": "📃"},
        #       "shown": False,
        #        "match": 0
        #   },
        #   {
        #       ...
        #   }, ...
        #]

        #defining card buttons
        for i in range(len(self.userDeck)):
            button: discord.ui.Button[discord.ui.View] = discord.ui.Button(emoji = "🎴", style = discord.ButtonStyle.gray, row = 0)
            button.callback = self.make_callback(deckIndex = i)
            self.add_item(button)

    async def start(self):
        votingPhaseEmbed = discord.Embed(
            title = "Vote Rock, Paper, Scissors !",
            description = f"Voting Phase begins now!\n**{people}** people are voting for cards..",
            color = self.embedColor,
            timestamp = self.timestamp
        )
        if not self.slash and self.msg:
            await self.msg.edit(content = None, embed = votingPhaseEmbed, view = None)
        else:
            await self.interaction.edit_original_response(content = None, embed = votingPhaseEmbed, view = None)

        await asyncio.sleep(3) #adds a short delay

        if self.botPlay:
            desc = (
                "Everyone has dropped their votes in the ballot box."
                "\n**Three** cards have been drawn from the Box for each of us."
                "\n\n*And now.. It's SHOWTIME!!* let's do it- *Rock, Paper, Scissors !*"
            )
        else:
            desc = (
                "Everyone has dropped their votes in the ballot box."
                "\n**Three** cards have been drawn from the Box for each of you."
                "\n\n*And now.. It's SHOWTIME!!* choose one card and play *Rock, Paper, Scissors !*"
            )

        matchEmbed = discord.Embed(
            title = "Vote Rock, Paper, Scissors !",
            description = desc + f"\n\n{self.playersDeckStr()}",
            color = self.embedColor,
            timestamp = self.timestamp
        )
        if not self.slash and self.msg:
            await self.msg.edit(embed = matchEmbed, view = self)
        else:
            await self.interaction.edit_original_response(embed = matchEmbed, view = self)

    def userDeckStr(self, user: discord.abc.User, final: bool):
        s = f"{"\u00A0" * 8}".join(
            (
                "🎴"
                if not c["shown"]
                else f"{c["card"]["emoji"]} ({c["match"]}{"st" if c["match"] == 1 else "nd" if c["match"] == 2 else "rd"})"
            )
            for c in (self.userDeck if user.id == self.user.id else self.targetDeck)
        )
        f = f"{"\u00A0" * 8}".join(
            (
                f"{c["card"]["emoji"]} ({c["match"]}{"st" if c["match"] == 1 else "nd" if c["match"] == 2 else "rd"})"
                if c["match"] != 0
                else f"{c["card"]["emoji"]}"
            )
            for c in (self.userDeck if user.id == self.user.id else self.targetDeck)
        )
        return s if not final else f

    def playersDeckStr(self, final: bool = False):
        return f"{self.userDeckStr(self.target, final)}{"\u00A0" * 8}<- {self.target.display_name}\n\n{self.userDeckStr(self.user, final)}{"\u00A0" * 8}<- {self.user.display_name}"

    #defining info button
    @discord.ui.button(label = "show my deck", style = discord.ButtonStyle.grey, row = 1)
    async def deck(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        if interaction.user.id not in (self.user.id, self.target.id):
            return await interaction.response.send_message("You can't play in this match.", ephemeral = True)
        
        #shows users deck info
        if interaction.user.id == self.user.id:
            info = " | ".join(f"{i + 1}.🎴 -> {c["card"]["emoji"]}" if not c["shown"] else f"{i + 1}.🎴 -> (Shown)" for i, c in enumerate(self.userDeck))
            await interaction.response.send_message(info, ephemeral = True)
            
        #shows targets deck info
        if interaction.user.id == self.target.id:
            info = " | ".join(f"{i + 1}.🎴 -> {c["card"]["emoji"]}" if not c["shown"] else f"{i + 1}.🎴 -> (Shown)" for i, c in enumerate(self.targetDeck))
            await interaction.response.send_message(info, ephemeral = True)

    def make_callback(self, deckIndex: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id not in (self.user.id, self.target.id):
                return await interaction.response.send_message("You can't play in this match.", ephemeral = True)
            
            #the bot makes a random card from its deck to show if playing with bot in the current match
            if self.botPlay and not self.playersChoice["target"]:
                botChoiceList = [i for i, c in enumerate(self.targetDeck) if not c["shown"]]
                botChoice = random.choice(botChoiceList)
                self.playersChoice["target"] = self.targetDeck[botChoice]["card"]
                self.targetDeck[botChoice]["match"] = 4 - len(botChoiceList) #stores the nth pick
                self.targetDeck[botChoice]["shown"] = True #stores the chosen card from the bots deck

            #user chooses a card to show
            if interaction.user.id == self.user.id:
                if not self.playersChoice["user"]:
                    if self.userDeck[deckIndex]["shown"]:
                        return await interaction.response.send_message("You have already shown this card before. Choose another card.", ephemeral = True)
                    self.playersChoice["user"] = self.userDeck[deckIndex]["card"]
                    self.userDeck[deckIndex]["match"] = 4 - sum(1 for c in self.userDeck if not c["shown"]) #stores the nth pick
                    self.userDeck[deckIndex]["shown"] = True #stores the chosen card from the users deck for the next match
                    await interaction.response.send_message(f"You have shown {self.userDeck[deckIndex]["card"]["emoji"]}", ephemeral = True)

                #if the user has already shown his card in the current match
                else:
                    return await interaction.response.send_message("You have already shown your card in this match.", ephemeral = True)
            
            #target chooses a card if not playing wth bot
            if interaction.user.id == self.target.id:
                if not self.playersChoice["target"]:
                    if self.targetDeck[deckIndex]["shown"]:
                        return await interaction.response.send_message("You have already shown this card before. Choose another card.", ephemeral = True)
                    
                    self.playersChoice["target"] = self.targetDeck[deckIndex]["card"]
                    self.targetDeck[deckIndex]["match"] = 4 - sum(1 for c in self.targetDeck if not c["shown"]) #stores the nth pick
                    self.targetDeck[deckIndex]["shown"] = True #stores the chosen card from the targets deck for the next match 
                    await interaction.response.send_message(f"You have shown {self.targetDeck[deckIndex]["card"]["emoji"]}", ephemeral = True)

                #if the target has already shown his card in the current match
                else:
                    return await interaction.response.send_message("You have already shown your card in this match.", ephemeral = True)

            #if both players have shown their card in the current match
            if self.playersChoice["target"] and self.playersChoice["user"]:
                winner = rpsResult((self.target, self.playersChoice["target"]), (self.user, self.playersChoice["user"])) #getting the result of rps in the current match

                #someone wins
                if winner:
                    if winner.id == self.target.id:
                        desc = f"**{self.target.mention} has Won!**" if not self.botPlay else "**I have Won!**"
                    else:
                        desc = f"**{self.user.mention} has Won!**"
                    
                    finalEmbed = discord.Embed(
                    title = "Vote Rock, Paper, Scissors !",
                    description = desc + f"\n\n{self.playersDeckStr(final = True)}",
                    color = self.embedColor,
                    timestamp = self.timestamp
                    ).set_thumbnail(url = winner.display_avatar.url)
                    if not self.slash and self.msg:
                        await self.msg.edit(embed = finalEmbed, view = None)
                    else:
                        await self.interaction.edit_original_response(embed = finalEmbed, view = None)

                    self.stop()

                #tie
                else:
                    #if no card is left in players' deck to play with (match 3)
                    if all(c["shown"] for c in self.userDeck):
                        finalEmbed = discord.Embed(
                        title = "Vote Rock, Paper, Scissors !",
                        description = "All Three matches ended in a Draw. This game is a Draw.\n\n*What are the odds??*" + f"\n\n{self.playersDeckStr(final = True)}",
                        color = discord.Color.default(),
                        timestamp = self.timestamp
                        )
                        if not self.slash and self.msg:
                            await self.msg.edit(embed = finalEmbed, view = None)
                        else:
                            await self.interaction.edit_original_response(embed = finalEmbed, view = None)

                        self.stop()

                    #players still have unplayed cards in their deck, a new match begins
                    else:
                        self.playersChoice["target"] = self.playersChoice["user"] = None #resets players' choice for a new match

                        desc = f"It was a Draw ! The game will continue with the remaining cards in {"your" if not self.botPlay else "our"} deck.\n"
                        nextMatchEmbed = discord.Embed(
                            title = "Vote Rock, Paper, Scissors !",
                            description = desc + self.playersDeckStr(),
                            color = self.embedColor,
                            timestamp = self.timestamp
                        )
                        if not self.slash and self.msg:
                            await self.msg.edit(embed = nextMatchEmbed)
                        else:
                            await self.interaction.edit_original_response(embed = nextMatchEmbed)

        return callback

    async def on_timeout(self):
        #disables all the buttons upon timeout
        for btn in self.children:
            if isinstance(btn, discord.ui.Button):
                btn.disabled = True
        
        if not self.botPlay and not self.playersChoice["target"] and not self.playersChoice["user"]:
            guilty = "both players"
        elif self.botPlay or (not self.playersChoice["user"] and self.playersChoice["target"]):
            guilty = self.user.mention
        else:
            guilty = self.target.mention

        embed = discord.Embed(
            title = "Vote Rock, Paper, Scissors !",
            description = f"⏰ The game has timed out! {guilty} didn't make a move.\n*shame on you..*",
            color = discord.Color.dark_gray(),
            timestamp = self.timestamp
        )
        try:
            #sends the timeout message
            if not self.slash and self.msg:
                await self.msg.edit(content = None, embed = embed, view = self)
            else:
                await self.interaction.edit_original_response(content = None, embed = embed, view = self)

        #if message is already deleted
        except discord.NotFound:
            pass

        self.stop() #stops the view upon timeout

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[discord.ui.View]):
        logger.exception(f"❌ something went wrong with vrps interaction - button: {getattr(item, 'label', 'unknown')}")
        try:
            await interaction.response.send_message("something went wrong with **vrps**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **vrps**.", ephemeral = True)
        except Exception:
            pass
            
        self.stop() #stops the view upon error


async def setup(bot: commands.Bot):
    await bot.add_cog(Vrps(bot))