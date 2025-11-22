import discord
from discord.ext import commands
from discord import app_commands
import random
from logHandler import loggerSetup

logger = loggerSetup(__name__)

choices = [
    {"name": "Rock", "beats": "Scissors", "emoji": "<:susrock:1013833657749864529>"},
    {"name": "Paper", "beats": "Rock", "emoji": "📃"},
    {"name": "Scissors", "beats": "Paper", "emoji": "✂️"}
]

def rpsResult(c1: str, c2: str):
    #tie
    if c1 == c2:
        return 0
    for choice in choices:
        if choice["name"] == c1:
            return 1 if choice["beats"] == c2 else 2
    return -1

class Rps(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
            name = "rps",
            extras = {"Category": "Games"},
            usage = "<target[*optional*]>",
            brief = "Traditional *Rock, Paper, Scissors* game.",
            help = (
                "A game between two people. Both players display one of three symbols: Rock, Paper or Scissors."
                "\n A Rock beats Scissors, a Paper beats Rock, a Scissors beats Paper."
                "\nYou can only play with Amélie herself if you run this game in her dm."
            )
    )
    async def rps(self, ctx: commands.Context[commands.Bot], user: discord.User | str | None = None):
        #if user mentions an invalid user
        if user and not isinstance(user, discord.abc.User):
            raise commands.BadArgument
        
        #if the user runs this command in dm to play with another user
        if not ctx.guild and user and user.id != ctx.me.id:
            return await ctx.reply("You can only play this game with others in a server. (except me!)")
        
        if user and ctx.guild:
            target = ctx.guild.get_member(user.id)
            if not target:
                return await ctx.reply(f"{user.mention} is now a member of this server.")
        else:
            target = None
        
        #if user wants to play with himself
        if target and target.id == ctx.author.id:
            return await ctx.reply("You can't play with yourself.")
        
        #if user wants to play with a bot except this bot
        if target and target.bot and target.id != ctx.me.id:
            return await ctx.reply("You can't play with bots. (except me!)")
        
        #plays with bot if no target is mentioned or the target is the bot itself
        if not target or target.id == ctx.me.id:
            view = RpsView(ctx, ctx.me, botPlay = True)
        
        else:
            view = RpsView(ctx, target)

        await view.start()
        
    @rps.error
    async def rps_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user mentioned an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("User not found. Please mention a valid user.")
        else:
            logger.error(f"❌ something went wrong with rps command:", exc_info = error)
            await ctx.reply("something went wrong with **rps**.")

    #rps slash command
    @app_commands.command(
        name = "rps",
        description = "Traditional *Rock, Paper, Scissors* game.",
        extras = {"Category": "Games"}
    )
    @app_commands.describe(user = "The user you want to play rps with.")
    async def slashRps(self, interaction: discord.Interaction, user: discord.Member | None = None):
        #if the user runs this command in dm to play with another user
        if not interaction.guild and user and user.id != interaction.client.application_id:
            return await interaction.response.send_message("You can only play this game with others in a server. (except me!)", ephemeral = True)
        
        if user and interaction.guild:
            target = interaction.guild.get_member(user.id)
            if not target:
                return await interaction.response.send_message(f"{user.mention} is now a member of this server.", ephemeral = True)
        else:
            target = None
        
        #if user wants to play with himself
        if target and target.id == interaction.user.id:
            return await interaction.response.send_message("You can't play with yourself.", ephemeral = True)
        
        #if user wants to play with a bot except this bot
        if target and target.bot and target.id != interaction.client.application_id:
            return await interaction.response.send_message("You can't play with bots. (except me!)", ephemeral = True)
        
        #plays with bot if no target is mentioned or the target is the bot itself
        if not target or target.id == interaction.client.application_id:
            if isinstance(interaction.client.user, discord.abc.User):
                view = RpsView(interaction, interaction.client.user, botPlay = True)
                await view.start()
        
        else:
            view = RpsView(interaction, target)
            await view.start()

    @slashRps.error
    async def slashRps_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /rps command:")
        try:
            await interaction.response.send_message("something went wrong with **rps**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **rps**.", ephemeral = True)

class RpsView(discord.ui.View):
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
        self.playerschoice: dict[str, str | None] = {
        "player1": None,
        "player1emoji": None,
        "player2": None,
        "player2emoji": None
    }
    
        #creates buttons as many as given in choices list
        for card in choices:
            btn: discord.ui.Button[discord.ui.View] = discord.ui.Button(style = discord.ButtonStyle.primary, label = card["name"], emoji = card["emoji"])
            btn.callback = self.make_callback(card["name"], card["emoji"])
            self.add_item(btn)

    async def start(self):
        if self.botPlay:
            content = None
            desc = "*You wanna play with ME??\nsounds fine-\nlets start the game then.*"
        
        else:
            content = f"{self.target.mention}, You're challenged to a game of *Rock, Paper, Scissors !* by {self.user.mention}" #notifies the target
            desc = f"It's currently {self.target.mention}'s turn to play."

        startEmbed = discord.Embed(
            title = "Rock, Paper, Scissors !",
            description = desc,
            color = self.embedColor
        )
        if not self.slash:
            self.msg = await self.ctx.send(content = content, embed = startEmbed, view = self)
        else:
            await self.interaction.response.send_message(content = content, embed = startEmbed, view = self)

    def make_callback(self, name: str, emoji: str):
        async def callback(interaction: discord.Interaction):
            #checks if only the user and target can interact with buttons
            if interaction.user.id not in [self.target.id, self.user.id]:
                return await interaction.response.send_message("You can't play in this match.", ephemeral = True)
            
            if self.botPlay and not self.playerschoice["player2"]:
                botChoice = random.choice(choices)
                self.playerschoice["player2"] = botChoice["name"]
                self.playerschoice["player2emoji"] = botChoice["emoji"]

            if interaction.user.id == self.user.id:
                if not self.playerschoice["player2"]:
                    return await interaction.response.send_message(f"You must wait for {self.target.mention} to play first.", ephemeral = True)

                else:
                    self.playerschoice["player1"] = name
                    self.playerschoice["player1emoji"] = emoji

            if interaction.user.id == self.target.id:
                if not self.playerschoice["player2"]:
                    self.playerschoice["player2"] = name
                    self.playerschoice["player2emoji"] = emoji

                    secondPhaseEmbed = discord.Embed(
                        title = "Rock, Paper, Scissors !",
                        description = f"It's currently {self.user.mention}'s turn to play.",
                        color = self.embedColor
                    )
                    if not self.slash:
                        await self.msg.edit(content = None, embed = secondPhaseEmbed)
                    else:
                        await self.interaction.edit_original_response(content = None, embed = secondPhaseEmbed)
                    await interaction.response.send_message(f"{self.user.mention}, It's your turn now!", delete_after = 180)

                else:
                    return await interaction.response.send_message(f"You have already played your turn. It's {self.user.mention}'s turn now", ephemeral = True)

            if self.playerschoice["player1"] and self.playerschoice["player2"]:
                result = rpsResult(self.playerschoice["player1"], self.playerschoice["player2"])

                #checks the result of rps
                if result == 0:
                    winneravatarurl = None
                    desc = "**It was a Draw !**"
                    cori = f"{self.user} escaped this time." if self.botPlay else None
                elif result == 1:
                    winneravatarurl = self.user.display_avatar.url
                    desc = f"**{self.user.mention} has Won !**"
                    cori = "-ahh. maybe another time." if self.botPlay else None
                else:
                    winneravatarurl = self.target.display_avatar.url
                    desc = "**I have Won !**" if self.botPlay else f"{self.target.mention} has Won !"
                    cori = "huh. not even a single sweat-" if self.botPlay else None
            
                #creates the final embed to send the results
                finalEmbed = discord.Embed(
                        title = "Rock, Paper, Scissors ! ",
                        description = desc,
                        color = discord.Color.random()
                    ).set_footer(text = cori)\
                    .add_field(name = f"{self.user.name} Choice", value = f"{self.playerschoice['player1']} {self.playerschoice['player1emoji']}", inline = True)\
                    .add_field(name = f"{self.target.name} Choice", value = f"{self.playerschoice['player2']} {self.playerschoice['player2emoji']}", inline = True)\
                    .set_thumbnail(url = winneravatarurl)
            
                await self.msg.edit(embed = finalEmbed, view = None)
                self.stop()

        return callback
    
    async def on_timeout(self):
        #disables buttons on timeout
        for btn in self.children:
            if isinstance(btn, discord.ui.Button):
                btn.disabled = True

        #player 1 is guilty
        if not self.playerschoice["player1"] and (self.botPlay or self.playerschoice["player2"]):
            guilty = self.user.mention

        #player 2 is guilty
        elif self.playerschoice["player1"]:
            guilty = self.target.mention

        #both players are guilty
        else:
            guilty = f"{self.user.mention} and {self.target.mention}"

        toEmbed = discord.Embed(
            title = "Rock, Paper, Scissors !",
            description = f"⏰ The game has timed out! {guilty} didn't make a move.\n*shame on you..*",
            color = discord.Color.dark_gray()
        )
        try:
            #sends the timeout message
            if not self.slash:
                await self.msg.edit(content = None, embed = toEmbed, view = self)
            else:
                await self.interaction.edit_original_response(content = None, embed = toEmbed, view = self)
        #if context message is deleted
        except discord.NotFound:
            pass

        self.stop() #stops the interaction upon timeout

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[discord.ui.View]):
        logger.exception(f"❌ something went wrong with rps interaction - button: {getattr(item, 'label', 'unknown')}")
        try:
            await interaction.response.send_message("something went wrong with **rps**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **rps**.", ephemeral = True)
        except Exception:
            pass
            
        self.stop() #stops further interaction


async def setup(bot: commands.Bot):
    await bot.add_cog(Rps(bot))