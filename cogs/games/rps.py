import discord
from discord.ext import commands
from discord import app_commands
import random
from typing import TypedDict
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)

class ChoiceInfo(TypedDict):
    name: str
    beats: str
    emoji: str
choices: list[ChoiceInfo] = [
    {"name": "Rock", "beats": "Scissors", "emoji": "<:susrock:1013833657749864529>"},
    {"name": "Paper", "beats": "Rock", "emoji": "📃"},
    {"name": "Scissors", "beats": "Paper", "emoji": "✂️"}
]

def rpsResult(c1: tuple[discord.abc.User, ChoiceInfo], c2: tuple[discord.abc.User, ChoiceInfo]):
    #tie
    if c1[1]["name"] == c2[1]["name"]:
        return None
    #player 2 wins
    elif c2[1]["beats"] == c1[1]["name"]:
        return c2[0]
    #player 1 wins
    else:
        return c1[0]

class Rps(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help: HelpData = {
        "help": (
            "A game between two people. Both players display one of three symbols: Rock, Paper or Scissors."
            "\n A Rock beats Scissors, a Paper beats Rock, a Scissors beats Paper."
            "\nYou can only play with Amélie herself if you run this game in her dm."
        ),
        "brief": "Traditional *Rock, Paper, Scissors* game.",
        "usage": "<target[*optional*]>",
        "aliases": ["rockpaperscissors"],
        "extras": {"Category": "Games"}
    }

    @commands.command(
            name = "rps",
            help = Help["help"],
            brief = Help["brief"],
            usage = Help["usage"],
            aliases = Help["aliases"],
            extras = Help["extras"]
    )
    async def rps(self, ctx: commands.Context[commands.Bot], user: discord.User | str | None = None):
        #if user mentions an invalid user
        if user and not isinstance(user, discord.abc.User):
            raise commands.BadArgument
        
        #if user mentions itself
        if user and user.id == ctx.author.id:
            return await ctx.reply("You can't play with yourself.")
        
        #if the user runs this command in dm to play with another user
        if not ctx.guild and user and user.id != ctx.me.id:
            return await ctx.reply("You can only play this game with others in a server. (except me!)")
        
        if user and ctx.guild:
            target = ctx.guild.get_member(user.id)
            if not target:
                return await ctx.reply(f"{user.mention} is not a member of this server.")
        else:
            target = None
        
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
            logger.exception(f"❌ something went wrong with rps command:")
            await ctx.reply("something went wrong with **rps**.")

    #rps slash command
    @app_commands.command(
        name = "rps",
        description = Help["brief"],
        extras = Help["extras"]
    )
    @app_commands.describe(user = "The user you want to play rps with.")
    async def slashRps(self, interaction: discord.Interaction, user: discord.User | None = None):
        #if user mentions itself
        if user and user.id == interaction.user.id:
            return await interaction.response.send_message("You can't play with yourself.", ephemeral = True)
        
        #if the user runs this command in dm to play with another user
        if not interaction.guild and user and user.id != interaction.client.application_id:
            return await interaction.response.send_message("You can only play this game with others in a server. (except me!)", ephemeral = True)
        
        if user and interaction.guild:
            target = interaction.guild.get_member(user.id)
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
        self.timestamp = discord.utils.utcnow()
        self.playersChoice: dict[str, ChoiceInfo | None] = {
            "user": None,
            "target": None
        }
        self.state = "targetchoose"
    
        #creates buttons as many as given in choices list
        for choice in choices:
            button: discord.ui.Button[discord.ui.View] = discord.ui.Button(style = discord.ButtonStyle.primary, label = choice["name"], emoji = choice["emoji"])
            button.callback = self.make_callback(choice)
            self.add_item(button)

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
            color = self.embedColor,
            timestamp = self.timestamp
        )
        #sends the initial message
        if self.slash:
            await self.interaction.response.send_message(content = content, embed = startEmbed, view = self)
        else:
            self.msg = await self.ctx.send(content = content, embed = startEmbed, view = self) #saves the message to edit later

    def make_callback(self, choice: ChoiceInfo):
        async def callback(interaction: discord.Interaction):
            #checks if only the user and target can interact with buttons
            if interaction.user.id not in (self.target.id, self.user.id):
                return await interaction.response.send_message("You can't play in this match.", ephemeral = True)
            
            #if user trys to play when it's target's turn
            if not self.botPlay and self.state == "targetchoose" and interaction.user.id != self.target.id:
                if not self.playersChoice["user"]:
                    return await interaction.response.send_message(f"It's currently {self.target.mention}'s turn to play.", ephemeral = True)
                else:
                    return await interaction.response.send_message(f"You've already played your turn. ({self.playersChoice["user"]["emoji"]})", ephemeral = True)
            
            #if target trys to play when it's user's turn
            if self.state == "userchoose" and interaction.user.id != self.user.id:
                if not self.playersChoice["target"]:
                    return await interaction.response.send_message(f"It's currently {self.user.mention}'s turn to play.", ephemeral = True)
                else:
                    return await interaction.response.send_message(f"You've already played your turn. ({self.playersChoice["target"]["emoji"]})", ephemeral = True)
            
            #if bot is the target
            if self.botPlay:
                self.playersChoice["target"] = random.choice(choices) #saves the choice for the bot
                self.state = "userchoose" #bot's turn's over, user's turn starts

            #target's turn
            if self.state == "targetchoose":
                self.playersChoice["target"] = choice #saves the choice for the target
                self.state = "userchoose" #target's turn's over, user's turn starts

                await interaction.response.send_message(f"You played {choice["emoji"]}.", ephemeral = True)

                userchooseEmbed = discord.Embed(
                    title = "Rock, Paper, Scissors !",
                    description = f"{self.target.mention} played their turn.\n\nIt's currently {self.user.mention}'s turn to play.",
                    color = self.embedColor,
                    timestamp = self.timestamp
                )
                if self.slash:
                    await self.interaction.edit_original_response(content = None, embed = userchooseEmbed)
                    await self.interaction.followup.send(f"{self.user.mention}, It's your turn now !")
                else:
                    await self.msg.edit(content = None, embed = userchooseEmbed)
                    await self.msg.reply(f"{self.user.mention}, It's your turn now !")

            #user's turn
            if self.state == "userchoose":
                self.playersChoice["user"] = choice #saves the choice for the user
                self.state = "result"

            #result
            if self.state == "result" and self.playersChoice["target"] and self.playersChoice["user"]:
                winner = rpsResult((self.target, self.playersChoice["target"]), (self.user, self.playersChoice["user"])) #gets the result

                #tie
                if not winner:
                    desc = "**It was a Draw !**"
                    cori = f"{self.user.mention} escaped this time." if self.botPlay else None
                else:
                    #target wins
                    if winner.id == self.target.id:
                        desc = f"**{winner.mention} has Won !**" if not self.botPlay else "**I have Won !**"
                        cori = "huh. not even a single sweat-" if self.botPlay else None
                    #user wins
                    else:
                        desc = f"**{winner.mention} has Won !**"
                        cori = "-ahh. maybe another time." if self.botPlay else None

                resultEmbed = discord.Embed(
                        title = "Rock, Paper, Scissors ! ",
                        description = desc,
                        color = discord.Color.random(),
                        timestamp = self.timestamp
                    ).set_footer(text = cori)\
                    .add_field(name = f"{self.user.display_name} Choice", value = f"{self.playersChoice["user"]["name"]} {self.playersChoice["user"]["emoji"]}", inline = True)\
                    .add_field(name = f"{self.target.display_name} Choice", value = f"{self.playersChoice["target"]["name"]} {self.playersChoice["target"]["emoji"]}", inline = True)\
                    .set_thumbnail(url = winner.display_avatar.url if winner else None)
                #sends the result
                if self.slash:
                    await self.interaction.edit_original_response(embed = resultEmbed, view = None)
                else:
                    await self.msg.edit(embed = resultEmbed, view = None)

                self.stop() #stops the view

        return callback
    
    async def on_timeout(self):
        #disables buttons on timeout
        for btn in self.children:
            if isinstance(btn, discord.ui.Button):
                btn.disabled = True

        if self.botPlay:
            guiltyStr = f"{self.user.mention} didn't make a move.\n*shame on you..*"
        elif self.state == "targetchoose":
            guiltyStr = f"{self.target.mention} didn't seem brave enough to accept the challenge."
        else:
            guiltyStr = f"{self.user.mention} seemed to have more important buisness to do."

        toEmbed = discord.Embed(
            title = "Rock, Paper, Scissors !",
            description = f"⏰ The game has timed out! {guiltyStr}",
            color = discord.Color.dark_gray(),
            timestamp = self.timestamp
        )
        try:
            #sends the timeout message
            if self.slash:
                await self.interaction.edit_original_response(content = None, embed = toEmbed, view = self)
            else:
                await self.msg.edit(content = None, embed = toEmbed, view = self)
        #if context message is deleted
        except discord.NotFound:
            pass

        self.stop() #stops the view upon timeout

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[discord.ui.View]):
        logger.exception(f"❌ something went wrong with rps interaction - button: {getattr(item, 'label', 'unknown')}")
        try:
            await interaction.response.send_message("something went wrong with **rps**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **rps**.", ephemeral = True)
        except Exception:
            pass
            
        self.stop() #stops the view upon error


async def setup(bot: commands.Bot):
    await bot.add_cog(Rps(bot))