import discord
from discord.ext import commands
import random
import asyncio

choices = [
    {"name": "Rock", "beats": "Scissors", "emoji": "<:susrock:1013833657749864529>"},
    {"name": "Paper", "beats": "Rock", "emoji": "📃"},
    {"name": "Scissors", "beats": "Paper", "emoji": "✂️"}
]

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
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout = 180)
        self.ctx = ctx
        self.target: discord.Member = None
        self.botPlay: bool = False
        self.msg: discord.Message = None
        self.userschoices = {
        "player1": None,
        "player1emoji": None,
        "player2": None,
        "player2emoji": None
    }
        #getting 40 random choices
        self.ballotbox = []
        for i in range(40):
            self.ballotbox.append(random.choice(choices))
        
        #distributing cards
        self.user1cards = []
        self.user2cards = []
        for i in range(3):
            card1 = random.choice(self.ballotbox)
            self.ballotbox.remove(card1)
            self.user1cards.append(card1)

            card2 = random.choice(self.ballotbox)
            self.ballotbox.remove(card2)
            self.user2cards.append(card2)
        
        #defining deck buttons
        for i in range(3):
            btn = discord.ui.Button(label = "🎴", style = discord.ButtonStyle.gray)
            btn.callback = self.make_callback(i)
            self.add_item(btn)

    def make_callback(self, index: float):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id not in [self.ctx.author.id, self.target.id]:
                await interaction.response.send_message("You can't play in this match.", ephemeral = True)
                return
            
            if interaction.user.id == self.ctx.author.id:
                if self.userschoices["player1"] is None:
                    self.userschoices["player1"] = self.user1cards[index]
                else:
                    await interaction.response.send_message("You already have shown your card.", ephemeral = True)
            
            elif interaction.user.id == self.target.id:
                if self.userschoices["player2"] is None:
                    self.userschoices["player2"] = self.user2cards[index]
                else:
                    await interaction.response.send_message("You already have shown your card.", ephemeral = True)

            if self.userschoices["player1"] and self.userschoices["player2"]:
                result = rpsResult(self.userschoices["player1"]["name"], self.userschoices["player2"]["name"])

                #checks the result of rps
                if result == 0:
                    winneravatarurl = None
                    desc = "**It was a Tie!**"
                elif result == 1:
                    winneravatarurl = self.ctx.author.display_avatar.url
                    desc = f"**{self.ctx.author.mention} has Won!**"
                elif result == 2:
                    winneravatarurl = self.target.display_avatar.url
                    desc = "**I have Won!**"

                finalEmbed = discord.Embed(
                    title = "Vote Rock, Paper, Scissors !",
                    description = desc,
                    color = discord.Color.random()
                ).set_thumbnail(url = winneravatarurl)

                await self.msg.edit(embed = finalEmbed, view = None)
                self.stop()

        return callable
        
    @discord.ui.button(label = "show my deck", emoji = "🃏", style = discord.ButtonStyle.grey)
    async def deck(self, interaction: discord.Interaction):
        if interaction.user.id not in [self.ctx.author.id, self.target.id]:
            await interaction.response.send_message("You can't play in this match.", ephemeral = True)
            return
        
        #shows users deck
        if interaction.user.id == self.ctx.author.id:
            info = ""
            for i in range(3):
                info += f" {i + 1}: {self.user1cards[i]["name"]}{self.user1cards[i]["emoji"]} |"
            await interaction.response.send_message(info, ephemeral = True)

        #shows targets deck
        elif interaction.user.id == self.target.id:
            info = ""
            for i in range(3):
                info += f" {i + 1}: {self.user2cards[i]["name"]}{self.user2cards[i]["emoji"]} |"
            await interaction.response.send_message(info, ephemeral = True)

class ReadyVeiw(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout = 180)
        self.ctx = ctx
        self.target: discord.Member = None
        self.botPlay: bool = False
        self.msg: discord.Message = None
        
    @discord.ui.button(label = "Ready", emoji = "✅", style = discord.ButtonStyle.green)
    async def ready(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.ctx.author.id, self.target.id]:
            await interaction.response.send_message("You can't play in this match.", ephemeral = True)
            return
        
        #target must click ready
        if not self.botPlay:
            if interaction.user.id != self.target.id:
                await interaction.response.send_message(f"{self.target.mention} must get ready first.")
                return
            
        self.stop()
        
        
        embed = discord.Embed(
            title = "Vote Rock, Paper, Scissors !",
            description = "`Voting Phase begins now !`\n*40* people are voting for cards ..."

        )
        
        await self.msg.edit(content = None, embed = embed, view = None)
        await asyncio.sleep(5)

        if self.botPlay:
            desc = (
                "Everyone voted succesfully."
                "\nAnd 3 cards are drawned for each one of us to play from the ballotbox."
                "\n`And now.. It'sss SHOWTIME !! let's show the card we want to play against each other now.`"
            )
        else:
            desc = (
                "Everyone voted succesfully."
                "\nAnd 3 cards are drawned for each one of you to play from the ballotbox."
                "\n`And now.. It'sss SHOWTIME !! let's show the card you want to play against each other now.`"
            )

        embed = discord.Embed(
            title = "Vote Rock, Paper, Scissors !",
            description = desc,
            color = discord.Color.random()
        )
        view = VrpsView(self.ctx)
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
        
        view = ReadyVeiw(ctx)
        #plays with bot
        if target in [None, ctx.guild.me]:
            target = ctx.guild.me
            view.target = target
            view.botPlay = True
            content = None
            desc = "`You want to play this game with me??\nhuh. I dare you..`\nget ``ready`` to begin."
        
        #plays with the target
        else:
            view.target = target
            content = f"{target.mention}, You're challenged to a game of *Vote Rock, Paper, Scissors !* by {ctx.author.mention}" #notifies the target
            desc = f"{target.mention} must get ``ready`` for game to begin."

        embed = discord.Embed(
            title = "Vote Rock, Paper, Scissors !",
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