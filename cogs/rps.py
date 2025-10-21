import discord
from discord.ext import commands
import random

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
        
class RpsView(discord.ui.View):
    def __init__(self, ctx: commands.Context, target: discord.Member, botPlay: bool):
        super().__init__(timeout = 180)
        self.ctx = ctx
        self.target = target
        self.msg: discord.Message = None
        self.botPlay = botPlay
        self.userschoices = {
        "player1": None,
        "player1emoji": None,
        "player2": None,
        "player2emoji": None
    }
    
        #creates buttons as many as given in choices list
        for btn in choices:
            button = discord.ui.Button(style = discord.ButtonStyle.primary, label = btn["name"], emoji = btn["emoji"])
            button.callback = self.make_callback(btn["name"], btn["emoji"])
            self.add_item(button)

    def make_callback(self, name, emoji):
        async def callback(interaction: discord.Interaction):
            #checks if only the user and target can interact with buttons
            if interaction.user.id not in [self.target.id, self.ctx.author.id]:
                await interaction.response.send_message("You can't play in this match.", ephemeral = True)
                return
            
            await interaction.response.defer(thinking = False) #defers the interaction to avoid "This interaction failed" message
            
            #plays with bot if no target is given
            if self.botPlay:
                #user choice first since playing with bot
                self.userschoices["player1"] = name
                self.userschoices["player1emoji"] = emoji
                result = rpsResult(self.userschoices["player1"], self.userschoices["player2"])

                #checks the result of rps
                if result == 0:
                    winneravatarurl = None
                    desc = "**It was a Tie!**"
                    cori = f"{self.ctx.author} escaped this time."
                elif result == 1:
                    winneravatarurl = self.ctx.author.display_avatar.url
                    desc = f"**{self.ctx.author.mention} has Won!**"
                    cori = "-ahh. maybe another time."
                elif result == 2:
                    winneravatarurl = self.target.display_avatar.url
                    desc = "**I have Won!**"
                    cori = "huh. not even a single sweat-"
            
            #plays with given target
            else:
                cori = None

                #targets turn first
                if self.userschoices["player2"] is None and interaction.user.id != self.target.id:
                    await interaction.response.send_message(f"You must wait for {self.target.mention} to play his turn first.", ephemeral = True)
                    return
                
                #targets choice
                if self.userschoices["player2"] is None:
                    self.userschoices["player2"] = name
                    self.userschoices["player2emoji"] = emoji

                    embed = discord.Embed(
                    title = "Rock, Paper, Scissors !",
                    description = f"It's currently {self.ctx.author.mention}'s turn to play.",
                    color = discord.Color.random()
                )
                    await self.msg.edit(embed = embed)
                    await interaction.response.send_message(f"{self.ctx.author.mention}, It's your turn now !", delete_after = 180)

                #checks if the target has chosen already
                elif interaction.user.id == self.target.id:
                    await interaction.response.send_message(f"You already made your choice. It's currently {self.ctx.author.mention}'s turn to play.", ephemeral = True)
                    return
                
                #users turn second
                else:
                    #user choice
                    self.userschoices["player1"] = name
                    self.userschoices["player1emoji"] = emoji
                    result = rpsResult(self.userschoices["player1"], self.userschoices["player2"])

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
            
            #creates the final embed to send the results
            finalEmbed = discord.Embed(
                    title = "Rock, Paper, Scissors ! ",
                    description = desc,
                    color = discord.Color.random()
                ).set_footer(text = cori)\
                .add_field(name = f"{self.ctx.author.name} Choice", value = f"{self.userschoices['player1']} {self.userschoices['player1emoji']}", inline = True)\
                .add_field(name = f"{self.target.name} Choice", value = f"{self.userschoices['player2']} {self.userschoices['player2emoji']}", inline = True)\
                .set_thumbnail(url = winneravatarurl)
            
            await self.msg.edit(content = None, embed = finalEmbed, view = None) #edits the first sent message with final embed
            self.stop() #stops further interaction

        return callback
    
    async def on_timeout(self):
        #disables buttons on timeout
        for btn in self.children:
            btn.disabled = True

        guilty = self.ctx.author.mention if self.userschoices["player2"] else self.target.mention

        embed = discord.Embed(
            title = "Rock, Paper, Scissors !",
            description = f"⏰ The game has timed out! {guilty} didn't make a move.\n*shame on you..*",
            color = discord.Color.dark_gray()
        )
        
        try:
            await self.msg.edit(embed = embed, view = self) #sends the timeout message

        #if message is already deleted
        except discord.NotFound:
            pass

        self.stop() #stops further interaction

class Rps(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name = "rps")
    async def rps(self, ctx: commands.Context, target: discord.Member = None):
        if target and target.id == ctx.author.id:
            await ctx.reply("You can't play with yourself.")
            return
        
        if target is not None and target.bot and target != ctx.guild.me:
            await ctx.reply("You can't play with bots. (except me !)")
            return
        
        view = RpsView(ctx, target, botPlay = False)
        #plays with bot, no target's given
        if target in [None, ctx.guild.me]:
            content = None
            target = ctx.guild.me
            view.target = ctx.guild.me
            view.botPlay = True

            #bot makes a random chocie
            botChoice = random.choice(choices)
            view.userschoices["player2"] = botChoice["name"]
            view.userschoices["player2emoji"] = botChoice["emoji"]

            embed = discord.Embed(
                title = "Rock, Paper, Scissors !",
                description = "*You wanna play with ME??\nsounds fine by me-\nlets start the game then.*",
                color = discord.Color.random()
            )
        
        #plays with given target
        else:
            content = f"{target.mention}, You're challenged to a game of *Rock, Paper, Scissors !* by {ctx.author.mention}" #notifies the target
            embed = discord.Embed(
                title = "Rock, Paper, Scissors !",
                description = f"It's currently {target.mention}'s turn to play.",
                color = discord.Color.random()
            )

        msg = await ctx.reply(content = content, embed = embed, view = view) #sends the initial message to begin the rps
        view.msg = msg #stores the sent message to edit later
        
    @rps.error
    async def rps_error(self, ctx: commands.Context, error):
        #if user mentioned an invalid user
        if isinstance(error, commands.MemberNotFound):
            await ctx.reply("Member not found. Please mention a valid user.")
        else:
            print(f"❌ something went wrong with rps command: {error}")
            await ctx.reply("something went wrong with **rps**.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Rps(bot))