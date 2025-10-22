import discord
from discord.ext import commands
import random
import asyncio

choices = [
    {"name": "Rock", "beats": "Scissors", "emoji": "<:susrock:1013833657749864529>"},
    {"name": "Paper", "beats": "Rock", "emoji": "📃"},
    {"name": "Scissors", "beats": "Paper", "emoji": "✂️"}
]
people = 40

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
        

class VrpsView(discord.ui.View):
    def __init__(self, ctx: commands.Context, userDeck: list = None, targetDeck: list = None):
        super().__init__(timeout = 180)
        self.ctx = ctx
        self.target: discord.Member = None
        self.botPlay: bool = False
        self.msg: discord.Message = None
        self.userschoices = {
        "player1": None,
        "player1index": None,
        "player1emoji": None,
        "player2": None,
        "player2index": None,
        "player2emoji": None
    }
        #getting 40 random choices
        self.ballotbox = []
        for i in range(people):
            self.ballotbox.append(random.choice(choices))
        random.shuffle(self.ballotbox)

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
            
            #bot shows a random card if playing with bot
            if self.botPlay and self.userschoices["player2"] is None:
                botChoiceIndex = random.randrange(len(self.targetDeck))
                self.userschoices["player2emoji"] = self.targetDeck[botChoiceIndex]["emoji"]
                self.userschoices["player2"] = self.targetDeck.pop(botChoiceIndex)["name"]

            #user shows a card
            if interaction.user.id == self.ctx.author.id:
                if self.userschoices["player1"] is None:
                    self.userschoices["player1emoji"] = self.userDeck[deckIndex]["emoji"]
                    self.userschoices["player1"] = self.userDeck.pop(deckIndex)["name"]
                    await interaction.response.send_message(f"You have shown {self.userschoices["player1emoji"]}", ephemeral = True)
                else:
                    await interaction.response.send_message("You already have shown your card in this match.", ephemeral = True)
                    return
            
            #target shows a card if not playing wth bot
            elif interaction.user.id == self.target.id:
                if self.userschoices["player2"] is None:
                    self.userschoices["player2emoji"] = self.targetDeck[deckIndex]["emoji"]
                    self.userschoices["player2"] = self.targetDeck.pop(deckIndex)["name"]
                    await interaction.response.send_message(f"You have shown {self.userschoices["player2emoji"]}", ephemeral = True)
                else:
                    await interaction.response.send_message("You already have shown your card in this match.", ephemeral = True)
                    return

            #if both players have shown their card
            if self.userschoices["player1"] and self.userschoices["player2"]:
                result = rpsResult(self.userschoices["player1"], self.userschoices["player2"])

                #checks the result of rps
                if result != 0:
                    if result == 1:
                        winneravatarurl = self.ctx.author.display_avatar.url
                        desc = f"**{self.ctx.author.mention} has Won!**"
                    elif result == 2:
                        winneravatarurl = self.target.display_avatar.url
                        desc = f"**{self.target.mention} have Won!**"
                    
                    finalEmbed = discord.Embed(
                    title = "Vote Rock-Paper-Scissors !",
                    description = desc,
                    color = discord.Color.random()
                    ).set_thumbnail(url = winneravatarurl)

                    await self.msg.edit(embed = finalEmbed, view = None)
                    self.stop()

                #if tie
                else:
                    if not self.userDeck or not self.targetDeck:
                        desc = "**All three matches ended with a tie. it's a draw game.**"

                        finalEmbed = discord.Embed(
                        title = "Vote Rock-Paper-Scissors !",
                        description = desc,
                        color = discord.Color.random()
                        )

                        await self.msg.edit(embed = finalEmbed, view = None)
                        self.stop()

                    else:
                        #resets users choices
                        self.userschoices = {k: None for k in self.userschoices}

                        #defines a new vrps button deck
                        view = VrpsView(self.ctx, self.userDeck, self.targetDeck)
                        view.target = self.target
                        view.botPlay = True if self.botPlay else False
                        embed = discord.Embed(
                            title = "Vote Rock-Paper-Scissors !",
                            description = "It was a tie !\n\nplay with another card with your remaining cards.",
                            color = discord.Color.random()
                        )
                        await self.msg.edit(embed = embed, view = view)
                        view.msg = self.msg
                        self.stop()

        return callback
        
    @discord.ui.button(label = "show my deck", emoji = "ℹ️", style = discord.ButtonStyle.grey)
    async def deck(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.ctx.author.id, self.target.id]:
                await interaction.response.send_message("You can't play in this match.", ephemeral = True)
                return
        
        info = "your deck:\n"
        #shows users deck
        if interaction.user.id == self.ctx.author.id:
            for i, c in enumerate(self.userDeck):
                info = " | ".join(f"{i + 1}.🎴 -> {c['emoji']}" for i, c in enumerate(self.userDeck))
            await interaction.response.send_message(info, ephemeral = True)
            
        #shows targets deck
        elif interaction.user.id == self.target.id:
            info = " | ".join(f"{i + 1}.🎴 -> {c['emoji']}" for i, c in enumerate(self.targetDeck))
            await interaction.response.send_message(info, ephemeral = True)     

class ReadyView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout = 180)
        self.ctx = ctx
        self.target: discord.Member = None
        self.botPlay: bool = False
        self.msg: discord.Message = None
        
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

        self.stop()
        
        embed = discord.Embed(
            title = "Vote Rock-Paper-Scissors !",
            description = "Voting Phase begins now !\n**40** people are voting for cards ..."

        )
        
        await self.msg.edit(content = None, embed = embed, view = None)
        await asyncio.sleep(5)

        if self.botPlay:
            desc = (
                "Everyone voted succesfully."
                "\nAnd **3** cards are drawned for each one of us to play from the ballotbox."
                "\n*And now.. It's SHOWTIME !!* let's show the card we want to play against each other now."
            )
        else:
            desc = (
                "Everyone voted succesfully."
                "\nAnd **3** cards are drawned for each one of you to play from the ballotbox."
                "\n*And now.. It's SHOWTIME !!* let's show the card you want to play against each other now."
            )

        embed = discord.Embed(
            title = "Vote Rock-Paper-Scissors !",
            description = desc,
            color = discord.Color.random()
        )
        view = VrpsView(self.ctx)
        view.target = self.target
        view.botPlay = True if self.botPlay else False
        await self.msg.edit(embed = embed, view = view)
        view.msg = self.msg

class Vrps(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name = "vrps")
    async def vrps(self, ctx: commands.Context, target: discord.Member = None):
        if target and target.id == ctx.author.id:
            await ctx.reply("You can't play with yourself.")
            return
        
        if target and target.bot and target != ctx.guild.me:
            await ctx.reply("You can't play with bots. (except me !)")
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
            content = f"{target.mention}, You're challenged to a game of *Vote Rock-Paper-Scissors* by {ctx.author.mention}" #notifies the target
            desc = f"{target.mention}, Click `Ready` to start the game."

        embed = discord.Embed(
            title = "Vote Rock-Paper-Scissors !",
            description = desc,
            color = discord.Color.random()
        )
        msg = await ctx.reply(content = content, embed = embed, view = view) #sends the initial message
        view.msg = msg #stores the sent message to edit later

    @vrps.error
    async def gamble_error(self, ctx: commands.Context, error):
        #if user mentioned an invalid user
        if isinstance(error, commands.MemberNotFound):
            await ctx.reply("Member not found. Please mention a valid user.")
        else:
            print(f"❌ something went wrong with vrps command: {error}")
            await ctx.reply("something went wrong with **vrps**.")
    

async def setup(bot: commands.Bot):
    await bot.add_cog(Vrps(bot))