import discord
from discord.ext import commands
import random
import asyncio
from typing import TypedDict

#specifies each card info types
class Card(TypedDict):
    name: str
    beats: str
    emoji: str

#specifies each deck info type
class DeckInfo(TypedDict):
    card: Card
    shown: bool
    match: int

choices: list[Card] = [
    {"name": "Rock", "beats": "Scissors", "emoji": "<:susrock:1013833657749864529>"},
    {"name": "Paper", "beats": "Rock", "emoji": "📃"},
    {"name": "Scissors", "beats": "Paper", "emoji": "✂️"}
]
people = 40 #number of peaople who will vote in the ballotbox

def rpsResult(c1: str, c2: str):
    #tie
    if c1 == c2:
        return 0
    for choice in choices:
        if choice["name"] == c1:
            return 1 if choice["beats"] == c2 else 2
    return -1

class Vrps(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
            name = "vrps",
            aliases = ["voterps"],
            usage = "<target[*optional*]>",
            extras = {"Category": "Games"},
            brief = "It's like rock-paper-scissors, but played with predetermined drawings on cards instead of using the hands.",
            help = (
                "The game is played between two people."
                "\nThe idea is that it's like rock-paper-scissors, but played with predetermined drawings on cards instead of using the hands. Despite the fact that only two are actually playing, the game requires a full class of people to work."
                "\nThe cards are determined by a voting phase, where each of the class members participating (except the players themselves) draw a rock, paper, or scissors symbol on a card, which are all added to a ballot box. The players then draw three cards at random, and select one from their hand to use in a showdown."
                "\nUnlike the traditional game, the player does not usually have all three options; it is more common that they get two of the same move and one different; having all three in one hand is extremely rare. If there is a tie, they play their cards until someone wins the hand."
                "\nYou can only play with Amélie herself if you run this game in her dm."
            )
    )
    async def vrps(self, ctx: commands.Context[commands.Bot], user: discord.User | str | None = None):
        #if user mentions an invalid user
        if user and not isinstance(user, discord.User):
            raise commands.BadArgument
        
        #if user runs the command in dm
        if not ctx.guild and user and user.id != ctx.me.id:
            return await ctx.reply("You can only play this game with others in a server. (except me!)")
        
        if user and ctx.guild:
            target = ctx.guild.get_member(user.id) #fetches the target member from the server, None if not found
            if not target:
                return await ctx.reply(f"{user.mention} is now a member of this server.")
        else:
            target = None
        
        #if users wants to play with himself
        if target and target.id == ctx.author.id:
            return await ctx.reply("You can't play with yourself.")
        
        #if user wants to play with a bot except this bot
        if target and target.bot and target.id != ctx.me.id:
            return await ctx.reply("You can't play with bots. (except me!)")

        #plays with bot if no target is mentioned or the target is the bot itself
        if not target or target.id == ctx.me.id:
            view = ReadyView(ctx, ctx.me, botPlay = True)
        
        #plays with the target
        else:
            view = ReadyView(ctx, target)
            
        await view.start() #starts the ready view

    @vrps.error
    async def vrps_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user mentioned an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("User not found. Please mention a valid user.")
        else:
            print(f"❌ something went wrong with vrps command: {error}")
            await ctx.reply("something went wrong with **vrps**.")

class ReadyView(discord.ui.View):
    def __init__(self, ctx: commands.Context[commands.Bot], target: discord.Member | discord.ClientUser, botPlay: bool = False):
        super().__init__(timeout = 180)
        self.ctx = ctx
        self.target = target
        self.botPlay = botPlay

    #defining ready button        
    @discord.ui.button(label = "Ready", emoji = "✅", style = discord.ButtonStyle.green)
    async def ready(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        if interaction.user.id not in [self.ctx.author.id, self.target.id]:
            return await interaction.response.send_message("You can't play in this game.", ephemeral = True)
        
        #target must get ready if not playing with bot
        if not self.botPlay:
            if interaction.user.id != self.target.id:
                return await interaction.response.send_message(f"{self.target.mention} must get ready to start the game.", ephemeral = True)
            
        #either target or user is ready at this point
        await interaction.response.defer(thinking = False) #defers the response to avoid "This interaction failed" message

        #initializing the vrps view
        view = VrpsView(ctx = self.ctx,
                        target = self.target,
                        msg = self.msg, #stores the message in vrps view to edit later
                        botPlay = self.botPlay,
                        embedColor = self.embedColor) 

        self.stop() #stops the intraction once both players are ready

        await view.start() #starts the vrps view

    async def start(self):
        #user must get ready if playing with bot
        if self.botPlay:
            content = None
            desc = (
                '" *AHAH, oh sweetheart.. I LOVE this game.* "'
                "\n\nClick `Ready` to start the game."
            )
        
        #target must get ready if not playing with bot
        else:
            content = f"{self.target.mention}, You're challenged to a game of *Vote Rock, Paper, Scissors !* by {self.ctx.author.mention}" #notifies the target
            desc = f"{self.target.mention}, Click `Ready` to start the game."

        self.embedColor = discord.Color.random()
        readyEmbed = discord.Embed(
            title = "Vote Rock, Paper, Scissors !",
            description = desc,
            color = self.embedColor
        )
        self.msg = await self.ctx.reply(content = content, embed = readyEmbed, view = self) #sends the initial ready message

    async def on_timeout(self):
        #disables all the buttons upon timeout
        for btn in self.children:
            if isinstance(btn, discord.ui.Button):
                btn.disabled = True

        guilty = self.target.mention if not self.botPlay else self.ctx.author.mention

        timeoutEmbed = discord.Embed(
            title = "Vote Rock, Paper, Scissors !",
            description = f"⏰ The game has timed out! {guilty} didn't get ready.\n*shame on you..*",
            color = discord.Color.dark_gray()
        )
        
        try:
            await self.msg.edit(content = None, embed = timeoutEmbed, view = self) #sends the timeout message

        #if message is already deleted
        except discord.NotFound:
            pass

        self.stop() #stops the interaction upon timeout

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[discord.ui.View]):
        print(f"❌ something went wrong with vrps ready interaction-> error: {error} | item: {getattr(item, "label", "unknown")}")
        try:
            await interaction.response.send_message("something went wrong with **vrps**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **vrps**.", ephemeral = True)
        except Exception:
            pass

        self.stop() #stops further interaction
    
class VrpsView(discord.ui.View):
    def __init__(self, ctx: commands.Context[commands.Bot], target: discord.Member | discord.ClientUser, msg: discord.Message, botPlay: bool = False, embedColor: discord.Color | None = None, userDeck: list[DeckInfo] | None = None, targetDeck: list[DeckInfo] | None = None):
        super().__init__(timeout = 180)
        self.ctx = ctx
        self.target = target
        self.msg = msg
        self.botPlay = botPlay
        self.embedColor = embedColor
        self.final = False
        self.playerschoice: dict[str, str | None] = {
        "player1": None,
        "player2": None,
    }
        #creating the ballotbox for the first time
        if not userDeck or not targetDeck:
            self.ballotbox: list[Card] = []
            #people will fill the ballotbox
            for i in range(people):
                self.ballotbox.append(random.choice(choices))
            random.shuffle(self.ballotbox) #shuffles the ballotbox

        #distributing cards
        self.userDeck: list[DeckInfo] = [{"card": self.ballotbox.pop(), "shown": False, "match": 0} for _ in range(3)] if not userDeck else userDeck
        self.targetDeck: list[DeckInfo] = [{"card": self.ballotbox.pop(), "shown": False, "match": 0} for _ in range(3)] if not targetDeck else targetDeck
        #example player deck:
        #[
        #   {
        #       "card": {"name": "Paper", "beats": "Rock", "emoji": "📃"},
        #       "shown": False
        #   },.....
        #]

        #defining card buttons
        for i in range(len(self.userDeck)):
            btn: discord.ui.Button[discord.ui.View] = discord.ui.Button(emoji = "🎴", style = discord.ButtonStyle.gray, row = 0)
            btn.callback = self.make_callback(deckIndex = i)
            self.add_item(btn)

    #defining info button
    @discord.ui.button(label = "show my deck", style = discord.ButtonStyle.grey, row = 1)
    async def deck(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        if interaction.user.id not in [self.ctx.author.id, self.target.id]:
                return await interaction.response.send_message("You can't play in this game.", ephemeral = True)
        
        #shows users deck info
        if interaction.user.id == self.ctx.author.id:
            info = " | ".join(f"{i + 1}.🎴 -> {c["card"]['emoji']}" if not c["shown"] else f"{i + 1}.🎴 -> (Shown)" for i, c in enumerate(self.userDeck))
            await interaction.response.send_message(info, ephemeral = True)
            
        #shows targets deck info
        elif interaction.user.id == self.target.id:
            info = " | ".join(f"{i + 1}.🎴 -> {c["card"]['emoji']}" if not c["shown"] else f"{i + 1}.🎴 -> (Shown)" for i, c in enumerate(self.targetDeck))
            await interaction.response.send_message(info, ephemeral = True)

    @property
    def userDeckStr(self):
        s = f"{"\u00A0" * 8}".join("🎴" if not c["shown"] else f"{c["card"]["emoji"]} ({c["match"]}th)" for c in self.userDeck)
        f = f"{"\u00A0" * 8}".join(f"{c["card"]["emoji"]} ({c["match"]}th)" if c["match"] != 0 else f"{c["card"]["emoji"]}" for c in self.userDeck)
        return s if not self.final else f
    @property
    def targetDeckStr(self):
        s = f"{"\u00A0" * 8}".join("🎴" if not c["shown"] else f"{c["card"]["emoji"]} ({c["match"]}th)" for c in self.targetDeck)
        f = f"{"\u00A0" * 8}".join(f"{c["card"]["emoji"]} ({c["match"]}th)" if c["match"] != 0 else f"{c["card"]["emoji"]}" for c in self.targetDeck)
        return s if not self.final else f
    @property
    def playersDeckStr(self):
        return f"{self.targetDeckStr}{"\u00A0" * 8}<- {self.target.display_name}\n\n{self.userDeckStr}{"\u00A0" * 8}<- {self.ctx.author.display_name}"
    
    async def start(self):
        votingPhaseEmbed = discord.Embed(
            title = "Vote Rock, Paper, Scissors !",
            description = f"Voting Phase begins now!\n**{people}** people are voting for cards..",
            color = self.embedColor

        )
        await self.msg.edit(content = None, embed = votingPhaseEmbed, view = None) #edits the embed once ready

        await asyncio.sleep(5) #a 5 second delay for making it more realistic

        if self.botPlay:
            desc = (
                "Everyone has voted successfully."
                "\n**Three** cards have been drawn from the Ballot Box for each of us."
                "\n\n*And now.. It's SHOWTIME!!* let's reveal our cards."
            )
        else:
            desc = (
                "Everyone has voted succesfully."
                "\n**Three** cards have been drawn from the Ballot Box for each of you."
                "\n*And now.. It's SHOWTIME!!* reveal your cards."
            )

        matchEmbed = discord.Embed(
            title = "Vote Rock, Paper, Scissors !",
            description = desc + f"\n\n{self.playersDeckStr}",
            color = self.embedColor
        )

        await self.msg.edit(embed = matchEmbed, view = self) #edits the embed to start the match

    def make_callback(self, deckIndex: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id not in [self.ctx.author.id, self.target.id]:
                return await interaction.response.send_message("You can't play in this game.", ephemeral = True)
            
            #the bot makes a random card from its deck to show if playing with bot in the current match
            if self.botPlay and self.playerschoice["player2"] is None:
                botChoiceIndexList = [i for i, c in enumerate(self.targetDeck) if not c["shown"]]
                botChoiceIndex = random.choice(botChoiceIndexList)
                self.playerschoice["player2"] = self.targetDeck[botChoiceIndex]["card"]["name"]
                self.targetDeck[botChoiceIndex]["match"] = 4 - len(botChoiceIndexList) #stores the nth pick
                self.targetDeck[botChoiceIndex]["shown"] = True #stores the chosen card from the bots deck

            #user chooses a card to show
            if interaction.user.id == self.ctx.author.id:
                if self.playerschoice["player1"] is None:
                    if self.userDeck[deckIndex]["shown"]:
                        return await interaction.response.send_message("You have already shown this card before. Choose another card.", ephemeral = True)
                    self.playerschoice["player1"] = self.userDeck[deckIndex]["card"]["name"]
                    self.userDeck[deckIndex]["match"] = 4 - sum(1 for c in self.userDeck if not c["shown"]) #stores the nth pick
                    self.userDeck[deckIndex]["shown"] = True #stores the chosen card from the users deck for the next match
                    await interaction.response.send_message(f"You have shown {self.userDeck[deckIndex]["card"]["emoji"]}", ephemeral = True)

                #if the user has already shown his card in the current match
                else:
                    return await interaction.response.send_message("You have already shown your card in this match.", ephemeral = True)
            
            #target shows a card if not playing wth bot
            elif interaction.user.id == self.target.id:
                if self.playerschoice["player2"] is None:
                    if self.targetDeck[deckIndex]["shown"]:
                        return await interaction.response.send_message("You have already shown this card before. Choose another card.", ephemeral = True)
                    
                    self.playerschoice["player2"] = self.targetDeck[deckIndex]["card"]["name"]
                    self.targetDeck[deckIndex]["match"] = 4 - sum(1 for c in self.targetDeck if not c["shown"]) #stores the nth pick
                    self.targetDeck[deckIndex]["shown"] = True #stores the chosen card from the targets deck for the next match 
                    await interaction.response.send_message(f"You have shown {self.targetDeck[deckIndex]["card"]["emoji"]}", ephemeral = True)

                #if the target has already shown his card in the current match
                else:
                    return await interaction.response.send_message("You have already shown your card in this match.", ephemeral = True)

            #if both players have shown their card in the current match
            if self.playerschoice["player1"] and self.playerschoice["player2"]:
                result = rpsResult(self.playerschoice["player1"], self.playerschoice["player2"]) #getting the result of rps in the current match

                #if not tie, someone wins
                if result != 0:
                    self.final = True
                    if result == 1:
                        winneravatarurl = self.ctx.author.display_avatar.url
                        desc = f"**{self.ctx.author.mention} has Won!**"
                    else:
                        winneravatarurl = self.target.display_avatar.url
                        desc = f"**{self.target.mention} has Won!**" if not self.botPlay else "**I have Won!**"
                    
                    #creating the final embed for results
                    finalEmbed = discord.Embed(
                    title = "Vote Rock, Paper, Scissors !",
                    description = desc + f"\n\n{self.playersDeckStr}",
                    color = self.embedColor
                    ).set_thumbnail(url = winneravatarurl)

                    await self.msg.edit(embed = finalEmbed, view = None) #edits the embed to show the result of the match
                    self.stop() #stops the intraction once one player wins

                #if tie, next match starts
                else:
                    #if no card is left in players' deck to play with (match 3)
                    if all(c["shown"] for c in self.userDeck):
                        finalEmbed = discord.Embed(
                        title = "Vote Rock, Paper, Scissors !",
                        description = "All Three matches ended up with a tie. This game is a draw.\n\n*What are the odds??*" + f"\n\n{self.playersDeckStr}",
                        color = discord.Color.default()
                        )

                        await self.msg.edit(embed = finalEmbed, view = None) #edits the embed to show the final result
                        self.stop() #stops the interaction once the game is over

                    #players still have cards in their deck
                    else:
                        #initializes a new vrps view for the next match
                        view = VrpsView(ctx = self.ctx,
                                        target = self.target,
                                        msg = self.msg,
                                        botPlay = self.botPlay,
                                        embedColor = self.embedColor,
                                        userDeck = self.userDeck,
                                        targetDeck = self.targetDeck)
                        if self.botPlay:
                            desc = "It was a tie ! The game will continue with the remaining cards in our deck.\n"
                        else:
                            desc = "It was a tie ! The game will continue with the remaining cards in your deck.\n"
                        nextMatchEmbed = discord.Embed(
                            title = "Vote Rock, Paper, Scissors !",
                            description = desc + view.playersDeckStr,
                            color = self.embedColor
                        )
                        await self.msg.edit(embed = nextMatchEmbed, view = view) #edits the embed to start another match
                        view.msg = self.msg #stores the message in the new vrps view to edit later
                        self.stop() #stops the current match interaction

        return callback

    async def on_timeout(self):
        #disables all the buttons upon timeout
        for btn in self.children:
            if isinstance(btn, discord.ui.Button):
                btn.disabled = True
        
        #player 1 is guilty
        if not self.playerschoice["player1"] and (self.botPlay or self.playerschoice["player2"]):
            guilty = self.ctx.author.mention

        #player 2 is guilty
        elif self.playerschoice["player1"]:
            guilty = self.target.mention

        #both players are guilty
        else:
            guilty = f"{self.ctx.author.mention} and {self.target.mention}"

        embed = discord.Embed(
            title = "Vote Rock, Paper, Scissors !",
            description = f"⏰ The game has timed out! {guilty} didn't make a move.\n*shame on you..*",
            color = discord.Color.dark_gray()
        )
        
        try:
            await self.msg.edit(content = None, embed = embed, view = self) #sends the timeout message

        #if message is already deleted
        except discord.NotFound:
            pass

        self.stop() #stops the interaction upon timeout

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[discord.ui.View]):
        print(f"❌ something went wrong with vrps interaction -> error: {error} | item: {getattr(item, 'label', 'unknown')}")
        try:
            await interaction.response.send_message("something went wrong with **vrps**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **vrps**.", ephemeral = True)
        except Exception:
            pass
            
        self.stop() #stops further interaction


async def setup(bot: commands.Bot):
    await bot.add_cog(Vrps(bot))