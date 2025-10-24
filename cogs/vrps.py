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
    def __init__(self, ctx: commands.Context, userDeck: list = None, targetDeck: list = None):
        super().__init__(timeout = 180)
        self.ctx = ctx
        self.target: discord.Member = None
        self.botPlay: bool = False
        self.msg: discord.Message = None
        self.embedColor: discord.Color = None
        self.userschoices = {
        "player1": None,
        "player1emoji": None,
        "player2": None,
        "player2emoji": None
    }
        #people will fill the ballotbox
        self.ballotbox = []
        for i in range(people):
            self.ballotbox.append(random.choice(choices))
        random.shuffle(self.ballotbox) #shuffles the ballotbox

        #distributing cards
        self.userDeck = [self.ballotbox.pop() for _ in range(3)] if not userDeck else userDeck
        self.targetDeck = [self.ballotbox.pop() for _ in range(3)] if not targetDeck else targetDeck

        #defining deck buttons
        for i in range(len(self.userDeck)):
            btn = discord.ui.Button(label = "🎴", style = discord.ButtonStyle.gray)
            btn.callback = self.make_callback(i)
            self.add_item(btn)

    def make_callback(self, deckIndex: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id not in [self.ctx.author.id, self.target.id]:
                await interaction.response.send_message("You can't play in this game.", ephemeral = True)
                return
            
            #the bot makes a random card from its deck to show if playing with bot in the current match
            if self.botPlay and self.userschoices["player2"] is None:
                botChoiceIndex = random.randrange(len(self.targetDeck))
                self.userschoices["player2emoji"] = self.targetDeck[botChoiceIndex]["emoji"]
                self.userschoices["player2"] = self.targetDeck.pop(botChoiceIndex)["name"] #removes the chosen card from the bots deck

            #user chooses a card to show
            if interaction.user.id == self.ctx.author.id:
                if self.userschoices["player1"] is None:
                    self.userschoices["player1emoji"] = self.userDeck[deckIndex]["emoji"]
                    self.userschoices["player1"] = self.userDeck.pop(deckIndex)["name"] #removes the chosen card from the users deck
                    await interaction.response.send_message(f"You have shown {self.userschoices['player1emoji']}", ephemeral = True)

                #if the user has already shown his card in the current match
                else:
                    await interaction.response.send_message("You have already shown your card in this match.", ephemeral = True)
                    return
            
            #target shows a card if not playing wth bot
            elif interaction.user.id == self.target.id:
                if self.userschoices["player2"] is None:
                    self.userschoices["player2emoji"] = self.targetDeck[deckIndex]["emoji"]
                    self.userschoices["player2"] = self.targetDeck.pop(deckIndex)["name"] #removes the chosen card from the targets deck
                    await interaction.response.send_message(f"You have shown {self.userschoices['player2emoji']}", ephemeral = True)

                #if the target has already shown his card in the current match
                else:
                    await interaction.response.send_message("You have already shown your card in this match.", ephemeral = True)
                    return

            #if both players have shown their card in the current match
            if self.userschoices["player1"] and self.userschoices["player2"]:
                result = rpsResult(self.userschoices["player1"], self.userschoices["player2"]) #getting the result of rps in the current match

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
                    title = "Vote Rock-Paper-Scissors !",
                    description = desc,
                    color = self.embedColor
                    ).set_thumbnail(url = winneravatarurl)

                    await self.msg.edit(embed = finalEmbed, view = None) #edits the embed to show the result of the match
                    self.stop() #stops the intraction once one player wins

                #if tie, next match starts
                else:
                    #if no card is left in players' deck to play with (match 3)
                    if not self.userDeck or not self.targetDeck:
                        finalEmbed = discord.Embed(
                        title = "vote Rock, Paper, Scissors !",
                        description = "All Three matches ended up with a tie. This game is a draw.\n\n*What are the odds??*",
                        color = discord.Color.default()
                        )

                        await self.msg.edit(embed = finalEmbed, view = None) #edits the embed to show the final result
                        self.stop() #stops the interaction once the game is over

                    #players still have cards in their deck
                    else:
                        #resets players' choice
                        self.userschoices = {k: None for k in self.userschoices}

                        #defines a new vrps button deck
                        view = VrpsView(self.ctx, self.userDeck, self.targetDeck)
                        view.target = self.target
                        view.botPlay = True if self.botPlay else False
                        view.embedColor = self.embedColor
                        embed = discord.Embed(
                            title = "vote Rock, Paper, Scissors !",
                            description = "It was a tie !\n\nThe game will continue with the remaining cards in your deck.",
                            color = self.embedColor
                        )
                        await self.msg.edit(embed = embed, view = view) #edits the embed to start another match
                        view.msg = self.msg #stores the message to edit later
                        self.stop() #stops the current match interaction to start another

        return callback
    
    #defining info button
    @discord.ui.button(label = "show my deck", style = discord.ButtonStyle.grey)
    async def deck(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.ctx.author.id, self.target.id]:
                await interaction.response.send_message("You can't play in this game.", ephemeral = True)
                return
        
        info = "your deck:\n"
        #shows users deck info
        if interaction.user.id == self.ctx.author.id:
            for i, c in enumerate(self.userDeck):
                info = " | ".join(f"{i + 1}.🎴 -> {c['emoji']}" for i, c in enumerate(self.userDeck))
            await interaction.response.send_message(info, ephemeral = True)
            
        #shows targets deck info
        elif interaction.user.id == self.target.id:
            info = " | ".join(f"{i + 1}.🎴 -> {c['emoji']}" for i, c in enumerate(self.targetDeck))
            await interaction.response.send_message(info, ephemeral = True)

    async def on_timeout(self):
        #disables all the buttons upon timeout
        for btn in self.children:
            btn.disabled = True
        
        guilty = self.target.mention if not self.userschoices["player2"] and not self.botPlay else self.ctx.author.mention
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

    async def on_error(self, interaction: discord.Interaction, error, item):
        print(f"❌ something went wrong with vrps vrps interaction-> error: {error} | item: {item}")
        await interaction.response.send_message("something went wrong with **vrps**.")
        self.stop() #stops further interaction

class ReadyView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout = 180)
        self.ctx = ctx
        self.target: discord.Member = None
        self.botPlay: bool = False
        self.msg: discord.Message = None
        self.embedColor: discord.Color = None

    #defining ready button        
    @discord.ui.button(label = "Ready", emoji = "✅", style = discord.ButtonStyle.green)
    async def ready(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.ctx.author.id, self.target.id]:
            await interaction.response.send_message("You can't play in this game.", ephemeral = True)
            return
        
        #target must click ready if not playing with bot
        if not self.botPlay:
            if interaction.user.id != self.target.id:
                await interaction.response.send_message(f"{self.target.mention} must get ready to start the game.", ephemeral = True)
                return 
        
        await interaction.response.defer(thinking = False) #defers the response to avoid "This interaction failed" message
        embed = discord.Embed(
            title = "vote Rock, Paper, Scissors !",
            description = f"Voting Phase begins now!\n**{people}** people are voting for cards ..."

        )
        await self.msg.edit(content = None, embed = embed, view = None) #edits the embed once ready
        await asyncio.sleep(5) #a 5 second delay for making it more realistic

        if self.botPlay:
            desc = (
                "Everyone has voted successfully."
                "\n**Three** cards have been drawn from the Ballot Box for each of us."
                "\n\n*And now.. It's SHOWTIME!!* let's reveal our cards now."
            )
        else:
            desc = (
                "Everyone has voted succesfully."
                "\n**Three** cards have been drawn from the Ballot Box for each of you."
                "\n*And now.. It's SHOWTIME!!* reveal your cards now."
            )

        userDeckEmbed = "  ".join("🎴" for c in self.userDeck)
        targetDeckEmbed = "  ".join("🎴" for c in self.targetDeck)

        embed = discord.Embed(
            title = "vote Rock, Paper, Scissors !",
            description = desc,
            color = self.embedColor
        )
        view = VrpsView(self.ctx)
        view.target = self.target
        view.botPlay = True if self.botPlay else False
        await self.msg.edit(embed = embed, view = view) #edit the embed once everyone has voted
        view.msg = self.msg #stores the message to edit later

        self.stop() #stops the intraction with ready view once both players are ready

    async def on_timeout(self):
        #disables all the buttons upon timeout
        for btn in self.children:
            btn.disabled = True

        guilty = self.target.mention if not self.botPlay else self.ctx.author.mention

        embed = discord.Embed(
            title = "vote Rock, Paper, Scissors !",
            description = f"⏰ The game has timed out! {guilty} didn't get ready.\n*shame on you..*",
            color = discord.Color.dark_gray()
        )
        
        try:
            await self.msg.edit(content = None, embed = embed, view = self) #sends the timeout message

        #if message is already deleted
        except discord.NotFound:
            pass

        self.stop() #stops the interaction upon timeout

    async def on_error(self, interaction: discord.Interaction, error, item):
        print(f"❌ something went wrong with vrps ready interaction-> error: {error} | item: {item}")
        await interaction.response.send_message("something went wrong with **vrps**.")
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
        
        #if user wants to play with a bot
        if target and target.bot and target != ctx.guild.me:
            await ctx.reply("You can't play with bots. (except me!)")
            return
        
        view = ReadyView(ctx)
        #plays with bot
        if target in [None, ctx.guild.me]:
            target = ctx.guild.me
            view.target = target
            view.botPlay = True
            content = None
            desc = (
                '" *AHAH, oh sweetheart.. I LOVE this game.* "'
                "\n\nClick `Ready` to start the game."
            )
        
        #plays with the target
        else:
            view.target = target
            content = f"{target.mention}, You're challenged to a game of *vote Rock, Paper, Scissors !* by {ctx.author.mention}" #notifies the target
            desc = f"{target.mention}, Click `Ready` to start the game."

        embedColor = discord.Color.random()
        view.embedColor = embedColor
        embed = discord.Embed(
            title = "vote Rock, Paper, Scissors !",
            description = desc,
            color = embedColor
        )
        msg = await ctx.reply(content = content, embed = embed, view = view) #sends the initial message
        view.msg = msg #stores the sent message to edit later

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