import discord
from discord.ext import commands
from discord import app_commands
import random
from typing import TypedDict
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)

class ScoreBoard(TypedDict):
    user: int
    userRecord: list[int]
    userBusted: None | int
    target: int
    targetRecord: list[int]
    targetBusted: None | int

class LimitDice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help: HelpData = {
        "help": "",
        "brief": "",
        "usage": "<target[*optional*]>",
        "aliases": ["lm"],
        "extras": {"Category": "Games"}
    }

    @commands.command(
            name = "limitdice",
            help = Help["help"],
            brief = Help["brief"],
            usage = Help["usage"],
            aliases = Help["aliases"],
            extras = Help["extras"]
    )
    async def limitdice(self, ctx: commands.Context[commands.Bot], user: discord.User | str | None = None):
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
            view = LimitDiceVeiw(ctx, ctx.me, botPlay = True)
        
        else:
            view = LimitDiceVeiw(ctx, target)

        await view.start()

    @limitdice.error
    async def limitdice_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user mentioned an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("User not found. Please mention a valid user.")
        else:
            logger.exception(f"❌ something went wrong with limitdice command:")
            await ctx.reply("something went wrong with **limitdice**.")

    #limitdice slash command
    @app_commands.command(
        name = "limitdice",
        description = Help["brief"],
        extras = Help["extras"]
    )
    @app_commands.describe(user = "The user you want to play Limit Dice with.")
    async def slashLimitdice(self, interaction: discord.Interaction, user: discord.User | None = None):
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
                view = LimitDiceVeiw(interaction, interaction.client.user, botPlay = True)
                await view.start()
        
        else:
            view = LimitDiceVeiw(interaction, target)
            await view.start()

    @slashLimitdice.error
    async def slashLimitdice_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /limitdice command:")
        try:
            await interaction.response.send_message("something went wrong with **limitdice**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **limitdice**.", ephemeral = True)

class LimitDiceVeiw(discord.ui.View):
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
        self.playersScore: ScoreBoard = {
            "user": 0,
            "userRecord": [],
            "userBusted": None,
            "target": 0,
            "targetRecord": [],
            "targetBusted": None
        }
        self.state = "target_roll"
        self.match = 1

    async def start(self):
        if self.botPlay:
            content = None
            desc = "*limit dice..\nI love this game. shall we start?*\nI already rolled my die."
        
        else:
            content = f"{self.target.mention}, You're challenged to a game of *Limit Dice* by {self.user.mention}." #notifies the target
            desc = f"It's currently {self.target.mention}'s turn to roll the dice."

        startEmbed = discord.Embed(
            title = "Limit Dice",
            description = desc,
            color = self.embedColor,
            timestamp = self.timestamp
        )
        if not self.slash:
            self.msg = await self.ctx.send(content = content, embed = startEmbed, view = self)
        else:
            await self.interaction.response.send_message(content = content, embed = startEmbed, view = self)

    #defines roll button
    @discord.ui.button(label = "roll" , style = discord.ButtonStyle.green, row = 0)
    async def roll(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        #checks if only the user and target can interact with buttons
        if interaction.user.id not in (self.target.id, self.user.id):
            return await interaction.response.send_message("You can't play in this match.", ephemeral = True)
        
        #if user trys to roll when it's target's turn
        if not self.botPlay and self.state == "target_roll" and interaction.user.id != self.target.id:
            return await interaction.response.send_message(f"It's {self.target.mention}'s turn to roll the die.", ephemeral = True)
        
        #if target trys to roll when it's user's turn
        if self.state == "user_roll" and interaction.user.id != self.user.id:
            return await interaction.response.send_message(f"It's {self.user.mention}'s turn to roll the die.", ephemeral = True)
        
        #if bot is the target
        if self.botPlay:
            botDie = random.randint(1, 6) if 6 not in self.playersScore["targetRecord"] else None #rolls a die for the bot if 6 is not rolled yet
            if botDie:
                self.playersScore["targetRecord"].append(botDie) #saves for the record

                #if rolls a 6, busted
                if botDie == 6:
                    self.playersScore["target"] = 0
                    self.playersScore["targetBusted"] = len(self.playersScore["targetRecord"])

                #adds the score otherwise
                else:
                    self.playersScore["target"] += 1
            
            self.state = "user_roll" #ends bots's roll turn, user's roll turn begins
        
        #target's turn
        if self.state == "target_roll":
            targetDie = random.randint(1, 6) if 6 not in self.playersScore["targetRecord"] else None #rolls a die for the target if 6 is not rolled yet
            if targetDie:
                self.playersScore["targetRecord"].append(targetDie) #saves for the record

                #if rolls a 6, busted
                if targetDie == 6:
                    self.playersScore["target"] = 0
                    self.playersScore["targetBusted"] = len(self.playersScore["targetRecord"])
                    rollStatus = f"You rolled a **{targetDie}!**\nYou got busted and your score has been reset to 0."

                #adds the score otherwise
                else:
                    self.playersScore["target"] += 1
                    rollStatus = f"You rolled a **{targetDie}**.\nYour current score: {self.playersScore["target"]}"
            else:
                rollStatus = "You gain no more score due to being busted."
            
            await interaction.response.send_message(rollStatus, ephemeral = True) #notifys the target of the result
            if self.match == 1:
                await interaction.followup.send(f"{self.user.mention}, It's your turn now !") #notifys the user that the target accepted the game

            userRollEmbed = discord.Embed(
                title = "Limit Dice",
                description = (
                    f"{self.target.mention} has rolled their die."
                    f"\n\nIt's currently {self.user.mention}'s turn to roll the die."
                ),
                color = self.embedColor,
                timestamp = self.timestamp
            )
            if self.slash:
                await self.interaction.response.edit_message(content = None, embed = userRollEmbed)
            else:
                await self.msg.edit(content = None, embed = userRollEmbed)

            self.state = "user_roll" #ends target's roll turn, user's roll turn begins

        #user's turn
        elif self.state == "user_roll":
            self.roll.disabled = True #disables roll button

            userDie = random.randint(1, 6) if not self.playersScore["userBusted"] else None #rolls a die for the user if 6 is not rolled yet
            if userDie:
                self.playersScore["userRecord"].append(userDie) #saves for the record

                #if rolls a 6, busted
                if userDie == 6:
                    self.playersScore["user"] = 0
                    self.playersScore["userBusted"] = len(self.playersScore["userRecord"])
                    rollStatus = f"You rolled a **{userDie}!**\nYou got busted and your score has been reset to 0."

                #adds the score otherwise
                else:
                    self.playersScore["user"] += 1
                    rollStatus = f"You rolled a **{userDie}**.\nYour current score: {self.playersScore["target"]}"
            else:
                rollStatus = "You gain no more score due to being busted."

            await interaction.response.send_message(rollStatus, ephemeral = True) #notifys the user of the result

            #ends the game if more than 10 matches are played
            if self.match == 10:
                return await self.endMatch(tenMatchLimit = True)
            
            if self.botPlay:
                desc = (
                    "Amazing. The decision phase begins now."
                    "\nWe must now decide either to **proceed** and bring even more fun to this game, or **stand** and SHOWDOWN our scores !"
                    "\nI made my choice already."
                )
            else:
                desc = (
                    "Now that both sides rolled their die, the decision phase begins."
                    "\nYou must decide either to **proceed** or **stand**."
                    "\nIf any of you decides to stand, scores will be locked and showdown phase begins after."
                    f"\n\nIt's currently {self.target.mention}'s turn to decide."
                )
            targetDecideEmbed = discord.Embed(
                title = "Limit Dice",
                description = desc,
                color = self.embedColor,
                timestamp = self.timestamp
            )
            if self.slash:
                await self.interaction.edit_original_response(embed = targetDecideEmbed)
            else:
                await self.msg.edit(embed = targetDecideEmbed)

            self.proceed.disabled = self.stand.disabled = False #enables decision buttons, decision phase begins

            self.state = "target_decide" #ends user's roll turn, target's decide turn begins

    #defines proceed button
    @discord.ui.button(label = "proceed" , style = discord.ButtonStyle.blurple, row = 1, disabled = True)
    async def proceed(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        #checks if only the user and target can interact with buttons
        if interaction.user.id not in (self.target.id, self.user.id):
            return await interaction.response.send_message("You can't play in this match.", ephemeral = True)
        
        #if user trys to decide when it's target's turn
        if not self.botPlay and self.state == "target_decide" and interaction.user.id != self.target.id:
            return await interaction.response.send_message(f"It's {self.target.mention}'s turn to decide.", ephemeral = True)
        
        #if target trys to decide when it's user's turn
        if self.state == "user_decide" and interaction.user.id != self.user.id:
            return await interaction.response.send_message(f"It's {self.user.mention}'s turn to decide.", ephemeral = True)
        
        #if bot is the target
        if self.botPlay:
            pass

            self.state = "user_decide" #ends bot's decide turn, user's decide turn begins
        
        #target's turn
        if self.state == "target_decide":
            userDecideEmbed = discord.Embed(
                title = "Limit Dice",
                description = (
                    f"{self.target.mention} will **Proceed**. 🔄️"
                    f"\n\nIt's currently {self.user.mention}'s turn to decide."
                ),
                color = self.embedColor,
                timestamp = self.timestamp
            )
            if self.slash:
                await self.interaction.edit_original_response(embed = userDecideEmbed)
            else:
                await self.msg.edit(embed = userDecideEmbed)

            self.state = "user_decide" #ends target's decide turn, user's decide turn begins

        #user's turn
        elif self.state == "user_decide":
            self.proceed.disabled = self.stand.disabled = True #disables decision buttons
            self.match += 1 #increase the match number

            nextmatchstr = f"\n\nIt's currently {self.target.mention}'s turn to roll the die." if not self.botPlay else "I've rolled my die already."
            decisionResultEmbed = discord.Embed(
                title = "Limit Dice",
                description = (
                    f"{self.target.mention if not self.botPlay else "I"} will **Proceed**. 🔄️"
                    f"\n{self.user.mention} will **Proceed**. 🔄️"
                    f"\nRound {self.match} begins."
                ) + nextmatchstr,
                color = self.embedColor,
                timestamp = self.timestamp
            )
            if self.slash:
                await self.interaction.edit_original_response(embed = decisionResultEmbed)
            else:
                await self.msg.edit(embed = decisionResultEmbed)

            self.roll.disabled = False #enables roll button for a new match

            self.state = "target_roll" #ends user's decide turn, match continues with target's roll turn

    #defines stand button
    @discord.ui.button(label = "stand" , style = discord.ButtonStyle.gray, row = 2, disabled = True)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        #checks if only the user and target can interact with buttons
        if interaction.user.id not in (self.target.id, self.user.id):
            return await interaction.response.send_message("You can't play in this match.", ephemeral = True)
        
        #if user trys to decide when it's target's turn
        if not self.botPlay and self.state == "target_decide" and interaction.user.id != self.target.id:
            return await interaction.response.send_message(f"It's {self.target.mention}'s turn to decide.", ephemeral = True)
        
        #if target trys to decide when it's user's turn
        if self.state == "user_decide" and interaction.user.id != self.user.id:
            return await interaction.response.send_message(f"It's {self.user.mention}'s turn to decide.", ephemeral = True)
        
        #if bot is the target
        if self.botPlay:
            pass

            self.state = "user_decide" #ends bot's decide turn, user's decide turn begins
        
        self.stand.disabled = self.proceed.disabled = True #disables stand and proceed button

        self.state = "result" #decision phase ends, showdown phase begins
        await self.endMatch(stand = interaction.user)

    async def endMatch(self, stand: discord.abc.User | None = None, tenMatchLimit: bool = False):
        #draw
        if self.playersScore["target"] == self.playersScore["user"]:
            winner = None
        #target wins
        elif self.playersScore["target"] > self.playersScore["user"]:
            winner = self.target
        #user wins
        else:
            winner = self.user

        #stand string
        standStr = (
            f"{stand.mention} **Stands**. 🔒"
            "\nScores are locked and it's time to SHOWDOWN !"
        ) if stand else ""

        #10 match limit string
        matchLimitStr = (
            "10 matches have been played."
            "\nScores are locked and it's time to SHOWDOWN !"
        ) if tenMatchLimit else ""

        #winner string
        if winner:
            winnerStr = (
                f"\n\n**{winner.mention} has WON !!**"
                f"\nWith a result of `{max(self.playersScore["target"], self.playersScore["user"])} > {min(self.playersScore["target"], self.playersScore["user"])}`"
            )
        else:
            winnerStr = (
                f"\n\nIt's a DRAW !!"
                f"\nWith a result of `{self.playersScore["target"]} = {self.playersScore["user"]}`"
            )

        #busted string
        if self.playersScore["targetBusted"] and self.playersScore["userBusted"]:
            bustedStr = f"\n\nBoth {self.target.mention} and {self.user.mention} were busted from match {self.playersScore["targetBusted"]} and {self.playersScore["userBusted"]} actually."
        elif self.playersScore["targetBusted"]:
            bustedStr = f"\n\n{self.target.mention} was busted from match {self.playersScore["targetBusted"]} actually."
        elif self.playersScore["userBusted"]:
            bustedStr = f"\n\n{self.user.mention} was busted from match {self.playersScore["userBusted"]} actually."
        else:
            bustedStr = ""

        #if draw, a rematch begins
        if not winner:
            #resets stats for a rematch
            self.playersScore["target"] = self.playersScore["user"] = 0
            self.playersScore["targetRecord"] = self.playersScore["userRecord"] = []
            self.playersScore["targetBusted"] = self.playersScore["userBusted"] = None

            rematchStr = "Another match has begun to determine the winner." + (f"\nIt's currently {self.target.mention}'s turn to roll the die." if not self.botPlay else "I've rolled my die already.") #rematch string
            resultEmbed = discord.Embed(
                title = "Limit Dice",
                description = standStr + matchLimitStr + winnerStr + bustedStr + rematchStr,
                color = self.embedColor,
                timestamp = self.timestamp,
            )
            if self.slash:
                await self.interaction.edit_original_response(embed = resultEmbed)
            else:
                await self.msg.edit(embed = resultEmbed)
            
            self.roll.disabled = False #enables roll button

            self.state = "target_roll"
            
        #results
        else:
            resultEmbed = discord.Embed(
                title = "Limit Dice",
                description = standStr + matchLimitStr + winnerStr + bustedStr,
                color = self.embedColor,
                timestamp = self.timestamp,
            ).set_thumbnail(url = winner.display_avatar.url)
            if self.slash:
                await self.interaction.edit_original_response(embed = resultEmbed, view = None)
            else:
                await self.msg.edit(embed = resultEmbed, view = None)

            self.stop() #stops the view

    async def on_timeout(self):
        #disables buttons on timeout
        for btn in self.children:
            if isinstance(btn, discord.ui.Button):
                btn.disabled = True

        if self.botPlay:
            if self.state in ("target_roll", "user_roll"):
                guiltyStr = f"{self.user.mention} didn't roll their die. Pathetic."
            else:
                guiltyStr = f"{self.user.mention} couldn't decide a simple decision."
        elif self.state == "target_roll":
            guiltyStr = f"{self.target.mention} didn't roll their die. Pathetic."
        elif self.state == "target_decide":
            guiltyStr = f"{self.target.mention} couldn't decide a simple decision."
        elif self.state == "user_roll":
            guiltyStr = f"{self.user.mention} didn't roll their die. Pathetic."
        else:
            guiltyStr = f"{self.user.mention} couldn't decide a simple decision."

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
        logger.exception(f"❌ something went wrong with limitdice interaction - button: {getattr(item, 'label', 'unknown')}")
        try:
            await interaction.response.send_message("something went wrong with **limitdice**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **limitdice**.", ephemeral = True)
        except Exception:
            pass
            
        self.stop() #stops the view upon error


async def setup(bot: commands.Bot):
    await bot.add_cog(LimitDice(bot))