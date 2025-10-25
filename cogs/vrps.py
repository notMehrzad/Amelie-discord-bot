import discord
from discord.ext import commands
import random
import asyncio

choices = [
    {"name": "Rock", "beats": "Scissors", "emoji": "<:susrock:1013833657749864529>"},
    {"name": "Paper", "beats": "Rock", "emoji": "📃"},
    {"name": "Scissors", "beats": "Paper", "emoji": "✂️"}
]
people = 40 #number of peaople who will vote in the ballotbox

def rpsResult(c1, c2):
    #tie
    if c1 == c2:
        return 0
    for choice in choices:
        #user 1 wins
        if c1 == choice["name"] and c2 == choice["beats"]:
            return 1
        #user 2 wins
        elif c2 == choice["name"] and c1 == choice["beats"]:
            return 2
        
#game main view class
class VrpsView(discord.ui.View):
    def __init__(self, ctx: commands.Context, target:discord.Member, userDeck: list[dict[str, dict[str, str] | bool | int]] | None = None, targetDeck: list[dict[str, dict[str, str] | bool | int]] | None = None):
        super().__init__(timeout = 180)
        self.ctx = ctx
        self.target = target
        self.botPlay: bool = False
        self.embedColor: discord.Color | None = None
        self.msg: discord.Message | None = None
        self.playerschoice: dict[str, str | None] = {
        "player1": None,
        "player2": None,
    }
        #creating the ballotbox for the first time
        if not userDeck or not targetDeck:
            self.ballotbox: list[dict[str, str]] = []
            #people will fill the ballotbox
            for i in range(people):
                self.ballotbox.append(random.choice(choices))
            random.shuffle(self.ballotbox) #shuffles the ballotbox

        #distributing cards
        self.userDeck: list[dict[str, dict[str, str] | bool | int]] = [{"card": self.ballotbox.pop(), "shown": False, "match": 0} for _ in range(3)] if not userDeck else userDeck
        self.targetDeck: list[dict[str, dict[str, str] | bool | int]] = [{"card": self.ballotbox.pop(), "shown": False, "match": 0} for _ in range(3)] if not targetDeck else targetDeck
        #example player deck:
        #[
        #   {
        #       "card": {"name": "Paper", "beats": "Rock", "emoji": "📃"},
        #       "shown": False
        #   },.....
        #]

        self.userDeckStr = "       ".join("🎴" if not c["shown"] else f"{c["card"]["emoji"]} {c["match"]}" for c in self.userDeck)
        self.targetDeckStr = "       ".join("🎴" if not c["shown"] else f"{c["card"]["emoji"]} {c["match"]}" for c in self.targetDeck)
        self.playersDeckStr = f"{self.targetDeckStr} <- {self.target.display_name}\n{self.userDeckStr} <- {self.ctx.author.display_name}"

        #defining card buttons
        for i in range(len(self.userDeck)):
            btn = discord.ui.Button(emoji = "🎴", style = discord.ButtonStyle.gray, row = 0)
            btn.callback = self.make_callback(deckIndex = i)
            self.add_item(btn)
        
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
                await interaction.response.send_message("You can't play in this game.", ephemeral = True)
                return
            
            #the bot makes a random card from its deck to show if playing with bot in the current match
            if self.botPlay and self.playerschoice["player2"] is None:
                botChoiceIndexList = [i for i, c in enumerate(self.targetDeck) if not c["shown"]]
                botChoiceIndex = random.choice(botChoiceIndexList)
                self.playerschoice["player2"] = self.targetDeck[botChoiceIndex]["card"]["name"]
                self.targetDeck[botChoiceIndex]["shown"] = True #stores the chosen card from the bots deck 

            #user chooses a card to show
            if interaction.user.id == self.ctx.author.id:
                if self.playerschoice["player1"] is None:
                    self.playerschoice["player1"] = self.userDeck[deckIndex]["card"]["name"]
                    self.userDeck[deckIndex]["shown"] = True #stores the chosen card from the users deck for the next match
                    await interaction.response.send_message(f"You have shown {self.userDeck[deckIndex]["card"]["emoji"]}", ephemeral = True)

                #if the user has already shown his card in the current match
                else:
                    await interaction.response.send_message("You have already shown your card in this match.", ephemeral = True)
                    return
            
            #target shows a card if not playing wth bot
            elif interaction.user.id == self.target.id:
                if self.playerschoice["player2"] is None:
                    self.playerschoice["player2"] = self.targetDeck[deckIndex]["card"]["name"]
                    self.targetDeck[deckIndex]["shown"] = True #stores the chosen card from the targets deck for the next match
                    await interaction.response.send_message(f"You have shown {self.targetDeck[deckIndex]["card"]["emoji"]}", ephemeral = True)

                #if the target has already shown his card in the current match
                else:
                    await interaction.response.send_message("You have already shown your card in this match.", ephemeral = True)
                    return

            #if both players have shown their card in the current match
            if self.playerschoice["player1"] and self.playerschoice["player2"]:
                result = rpsResult(self.playerschoice["player1"], self.playerschoice["player2"]) #getting the result of rps in the current match

                #checks the result of rps in the current match
                if result != 0:
                    if result == 1:
                        winneravatarurl = self.ctx.author.display_avatar.url
                        desc = f"**{self.ctx.author.mention} has Won!**"
                    elif result == 2:
                        winneravatarurl = self.target.display_avatar.url
                        desc = f"**{self.target.mention} has Won!**" if not self.botPlay else "**I have Won!**"
                    
                    #creating the final embed for results
                    finalEmbed = discord.Embed(
                    title = "Vote Rock, Paper, Scissors !",
                    description = desc,
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
                        description = "All Three matches ended up with a tie. This game is a draw.\n\n*What are the odds??*",
                        color = discord.Color.default()
                        )

                        await self.msg.edit(embed = finalEmbed, view = None) #edits the embed to show the final result
                        self.stop() #stops the interaction once the game is over

                    #players still have cards in their deck
                    else:
                        #initializes a new vrps view for the next match
                        view = VrpsView(ctx = self.ctx, target = self.target, userDeck = self.userDeck, targetDeck = self.targetDeck)
                        view.botPlay = self.botPlay
                        view.embedColor = self.embedColor
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
    
    #defining info button
    @discord.ui.button(label = "show my deck", style = discord.ButtonStyle.grey, row = 1)
    async def deck(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.ctx.author.id, self.target.id]:
                await interaction.response.send_message("You can't play in this game.", ephemeral = True)
                return
        
        #shows users deck info
        if interaction.user.id == self.ctx.author.id:
            info = " | ".join(f"{i + 1}.🎴 -> {c["card"]['emoji']}" if not c["shown"] else f"{i + 1}.🎴 -> (Shown)" for i, c in enumerate(self.userDeck))
            await interaction.response.send_message(info, ephemeral = True)
            
        #shows targets deck info
        elif interaction.user.id == self.target.id:
            info = " | ".join(f"{i + 1}.🎴 -> {c["card"]['emoji']}" if not c["shown"] else f"{i + 1}.🎴 -> (Shown)" for i, c in enumerate(self.targetDeck))
            await interaction.response.send_message(info, ephemeral = True)

    async def on_timeout(self):
        #disables all the buttons upon timeout
        for btn in self.children:
            btn.disabled = True
        
        if not self.playerschoice["player1"] and self.botPlay:
            guilty = self.ctx.author.mention
        elif not self.playerschoice["player1"] and not self.playerschoice["player2"]:
            guilty = f"{self.ctx.author.mention} and {self.target.mention}"
        elif not self.playerschoice["player2"]:
            guilty = self.target.mention

        embed = discord.Embed(
            title = "vote Rock, Paper, Scissors !",
            description = f"⏰ The game has timed out! {guilty} didn't make a move.\n*shame on you..*",
            color = discord.Color.dark_gray()
        )
        
        try:
            await self.msg.edit(content = None, embed = embed, view = self) #sends the timeout message

        #if message is already deleted
        except discord.NotFound:
            pass

        self.stop() #stops the interaction upon timeout

    async def on_error(self, interaction: discord.Interaction, error, item: discord.ui.Button):
        print(f"❌ something went wrong with vrps vrps interaction-> error: {error} | item: {item.label}")
        try:
            await interaction.response.send_message("something went wrong with **vrps**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **vrps**.", ephemeral = True)
            
        self.stop() #stops further interaction

class ReadyView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout = 180)
        self.ctx = ctx
        self.target: discord.Member = None
        self.botPlay: bool = False

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

    #defining ready button        
    @discord.ui.button(label = "Ready", emoji = "✅", style = discord.ButtonStyle.green)
    async def ready(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.ctx.author.id, self.target.id]:
            await interaction.response.send_message("You can't play in this game.", ephemeral = True)
            return
        
        #target must get ready if not playing with bot
        if not self.botPlay:
            if interaction.user.id != self.target.id:
                await interaction.response.send_message(f"{self.target.mention} must get ready to start the game.", ephemeral = True)
                return 
            
        #either target or user is ready at this point
        await interaction.response.defer(thinking = False) #defers the response to avoid "This interaction failed" message

        view = VrpsView(ctx = self.ctx, target = self.target) #initializing the vrps view
        view.botPlay = self.botPlay
        view.embedColor = self.embedColor
        view.msg = self.msg #stores the message in vrps view to edit later

        self.stop() #stops the intraction once both players are ready

        await view.start() #starts the vrps view

    async def on_timeout(self):
        #disables all the buttons upon timeout
        for btn in self.children:
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

    async def on_error(self, interaction: discord.Interaction, error, item: discord.ui.Button):
        print(f"❌ something went wrong with vrps ready interaction-> error: {error} | item: {item.label}")
        try:
            await interaction.response.send_message("something went wrong with **vrps**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **vrps**.", ephemeral = True)
            
        
        self.stop() #stops further interaction

class Vrps(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name = "vrps")
    async def vrps(self, ctx: commands.Context, target: discord.Member = None):
        #if users wants to play with himself
        if target and target.id == ctx.author.id:
            await ctx.reply("You can't play with yourself.")
            return
        
        #if user wants to play with a bot except this bot
        if target and target.bot and target != ctx.guild.me:
            await ctx.reply("You can't play with bots. (except me!)")
            return
        
        view = ReadyView(ctx) #initializing the ready view

        #plays with bot if no target is mentioned or the target is the bot itself
        if target in [None, ctx.guild.me]:
            target = view.target = ctx.guild.me
            view.botPlay = True
        
        #plays with the target
        else:
            view.target = target
            
        await view.start() #starts the ready view

    @vrps.error
    async def vrps_error(self, ctx: commands.Context, error):
        #if user mentioned an invalid user
        if isinstance(error, commands.MemberNotFound):
            await ctx.reply("Member not found. Please mention a valid user.")
        else:
            print(f"❌ something went wrong with vrps command: {error}")
            await ctx.reply("something went wrong with **vrps**.")
    

async def setup(bot: commands.Bot):
    await bot.add_cog(Vrps(bot))