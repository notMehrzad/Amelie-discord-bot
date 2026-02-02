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
    userRecord: list[int | str]
    userBusted: None | int
    target: int
    targetRecord: list[int | str]
    targetBusted: None | int

class LimitDice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help: HelpData = {
        "help": (
            "A game between two players; All about luck and will."
            "\nBoth players take turns rolling their die. and they can't see each other's hand."
            "\nAny roll from **one to five** worths **1 point**."
            "\nThey can then keep rolling to increase their score."
            "\n**If anyone rolls a six, their final score is 0** and they can't gain any more points at that time."
            "\nIf anyone feels they'll roll a six, they can declare \"Stop.\" and so their score is frozen in place."
            "\nIf both players stop or roll a six, the top scorer wins."
            "\n\nHowever, rolling a six doesn't mean an instant loss! you can keep rolling that die."
            "\nYou won't gain any more points but your opponent will think you're still racking them up."
            "\n\nIf your opponent keep rolling their die, never stopping.., it'll make you wonder if they rolled a six or not."
            "\nShould you stop or not? You'll need to think about that, all the way to your Limits, in this **test of Willpower!**"
        ),
        "brief": "A two-player dice game of luck, bluffing, and willpower where rolling a six can change everything.",
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

            await self.botRoll()
        
        else:
            content = f"{self.target.mention}, You're challenged to a game of *Limit Dice* by {self.user.mention}." #notifies the target
            desc = f"It's currently {self.target.mention}'s turn to roll the dice."

        startEmbed = discord.Embed(
            title = "Limit Dice 🎲",
            description = desc,
            color = self.embedColor,
            timestamp = self.timestamp
        )
        if self.slash:
            await self.interaction.response.send_message(content = content, embed = startEmbed, view = self)
        else:
            self.msg = await self.ctx.send(content = content, embed = startEmbed, view = self)

    async def botRoll(self):
        #bot's turn, if bot is the target
        if self.botPlay:
            if self.state == "target_roll":
                #if not busted yet
                if not self.playersScore["targetBusted"]:
                    botDie = random.randint(1, 6) #rolls a die for the bot
                    self.playersScore["targetRecord"].append(botDie) #saves the die for the record

                    #if rolls a 6, busted
                    if botDie == 6:
                        self.playersScore["target"] = 0
                        self.playersScore["targetBusted"] = len(self.playersScore["targetRecord"])

                        #if the user is busted too, match ends
                        if self.playersScore["userBusted"]:
                            return await self.endMatch(bothBusted = True)

                    #adds the score otherwise
                    else:
                        self.playersScore["target"] += 1
                    
                self.state = "user_roll" #ends bots's roll turn, user's roll turn begins
            elif self.state == "target_last_roll":
                botDie = random.randint(1, 6) #rolls a die for the bot for the last time
                self.playersScore["targetRecord"].append(botDie) #saves the die for the record

                #if rolls a 6, busted
                if botDie == 6:
                    self.playersScore["target"] = 0
                    self.playersScore["targetBusted"] = len(self.playersScore["targetRecord"])

                #adds the score otherwise
                else:
                    self.playersScore["target"] += 1

                await self.endMatch() #ends the match

    #defines roll button
    @discord.ui.button(label = "roll" , style = discord.ButtonStyle.green, row = 0)
    async def roll(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        #checks if only the user and target can interact with buttons
        if interaction.user.id not in (self.target.id, self.user.id):
            return await interaction.response.send_message("You can't play in this match.", ephemeral = True)
        
        #if user trys to roll when it's target's turn
        if self.state == "target_roll" and interaction.user.id != self.target.id:
            return await interaction.response.send_message(f"It's {self.target.mention}'s turn to roll the die.", ephemeral = True)
        
        #if target trys to roll when it's user's turn
        if self.state == "user_roll" and interaction.user.id != self.user.id:
            return await interaction.response.send_message(f"It's {self.user.mention}'s turn to roll the die.", ephemeral = True)
        
        #if user trys to roll when it's target's last roll phase
        if self.state == "target_last_roll" and interaction.user.id != self.target.id:
            return await interaction.response.send_message(f"You stopped before and your score is frozen in place.\nIt's currently {self.target.mention}'s turn to roll for the last time.", ephemeral = True)

        #if target trys to roll when it's user's last roll phase
        if self.state == "user_last_roll" and interaction.user.id != self.user.id:
            return await interaction.response.send_message(f"You stopped before and your score is frozen in place.\nIt's currently {self.user.mention}'s turn to roll for the last time.", ephemeral = True)

        #target's turn
        if self.state == "target_roll":
            #if not busted yet
            if not self.playersScore["targetBusted"]:
                targetDie = random.randint(1, 6) #rolls a die for the target
                self.playersScore["targetRecord"].append(targetDie) #saves the die for the record

                #if rolls a 6, busted
                if targetDie == 6:
                    self.playersScore["target"] = 0
                    self.playersScore["targetBusted"] = len(self.playersScore["targetRecord"])

                    #if the user is busted too, match ends
                    if self.playersScore["userBusted"]:
                        return await self.endMatch(bothBusted = True)
                    else:
                        rollStatus = f"You rolled a **{targetDie}!**\nYour score is reset to 0 and you gain no more point from now on."

                #adds the score otherwise
                else:
                    self.playersScore["target"] += 1
                    rollStatus = f"You rolled a **{targetDie}**.\nYour current score: {self.playersScore["target"]}"
            else:
                rollStatus = "You gain no more points."
            
            await interaction.response.send_message(rollStatus, ephemeral = True) #sends the roll result to the target

            if self.match == 1:
                await interaction.followup.send(f"{self.user.mention}, It's your turn now !") #notifys the user that the target accepted the game

            userRollEmbed = discord.Embed(
                title = "Limit Dice 🎲",
                description = (
                    f"{self.target.mention} has rolled their die."
                    f"\n\nIt's currently {self.user.mention}'s turn to roll."
                ),
                color = self.embedColor,
                timestamp = self.timestamp
            )
            if self.slash:
                await self.interaction.edit_original_response(content = None, embed = userRollEmbed)
            else:
                await self.msg.edit(content = None, embed = userRollEmbed)

            self.state = "user_roll" #ends target's roll turn, user's roll turn begins

        #user's turn
        elif self.state == "user_roll":
            self.roll.disabled = True #disables roll button

            #if not busted yet
            if not self.playersScore["userBusted"]:
                userDie = random.randint(1, 6) #rolls a die for the user
                self.playersScore["userRecord"].append(userDie) #saves the die for the record

                #if rolls a 6, busted
                if userDie == 6:
                    self.playersScore["user"] = 0
                    self.playersScore["userBusted"] = len(self.playersScore["userRecord"])

                    #if the target is busted too, match ends
                    if self.playersScore["targetBusted"]:
                        return await self.endMatch(bothBusted = True)
                    else:
                        rollStatus = f"You rolled a **{userDie}!**\nYour score is reset to 0 and you gain no more point from now on."

                #adds the score otherwise
                else:
                    self.playersScore["user"] += 1
                    rollStatus = f"You rolled a **{userDie}**.\nYour current score: {self.playersScore["target"]}"
            else:
                rollStatus = "You gain no more points."

            await interaction.response.send_message(rollStatus, ephemeral = True) #sends the roll result to the user
            
            if self.botPlay:
                desc = (
                    "Amazing. The decision phase begins now."
                    "\nWe must now decide either to **Roll** again and bring even more fun to this game, or **Stop** and freeze our score !"
                    "\n\nI made my choice already."
                )
            else:
                desc = (
                    "Now that both sides rolled their die, the decision phase begins."
                    "\nYou must decide either to **Roll** or **Stop**."
                    "\nIf both of you stop, showdown phase begins."
                    f"\n\nIt's currently {self.target.mention}'s turn to decide."
                )
            targetDecideEmbed = discord.Embed(
                title = "Limit Dice 🎲",
                description = desc,
                color = self.embedColor,
                timestamp = self.timestamp
            )
            if self.slash:
                await self.interaction.edit_original_response(embed = targetDecideEmbed)
            else:
                await self.msg.edit(embed = targetDecideEmbed)

            self.proceed.disabled = self.stopbtn.disabled = False #enables decision buttons, decision phase begins

            self.state = "target_decide" #ends user's roll turn, target's decide turn begins
        
        #target's last roll turn
        elif self.state == "target_last_roll":
            self.roll.disabled = True #disables roll button

            targetDie = random.randint(1, 6) #rolls a die for the target for the last time
            self.playersScore["userRecord"].append(targetDie) #saves for the record

            #if rolls a 6, busted
            if targetDie == 6:
                self.playersScore["user"] = 0
                self.playersScore["userBusted"] = len(self.playersScore["userRecord"])
                rollStatus = f"You rolled a **{targetDie}!**\nYour score is reset to 0."

            #adds the score otherwise
            else:
                self.playersScore["user"] += 1
                rollStatus = f"You rolled a **{targetDie}**.\nYour current score: {self.playersScore["target"]}"

            await interaction.response.send_message(rollStatus, ephemeral = True) #notifys the user of the result

            await self.endMatch()

        #user's last roll turn
        elif self.state == "user_last_roll":
            self.roll.disabled = True #disables roll button

            userDie = random.randint(1, 6) #rolls a die for the user for the last time
            self.playersScore["userRecord"].append(userDie) #saves for the record

            #if rolls a 6, busted
            if userDie == 6:
                self.playersScore["user"] = 0
                self.playersScore["userBusted"] = len(self.playersScore["userRecord"])
                rollStatus = f"You rolled a **{userDie}!**\nYour score is reset to 0."

            #adds the score otherwise
            else:
                self.playersScore["user"] += 1
                rollStatus = f"You rolled a **{userDie}**.\nYour current score: {self.playersScore["target"]}"

            await interaction.response.send_message(rollStatus, ephemeral = True) #notifys the user of the result

            await self.endMatch()

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
        
        #bot's turn, if bot is the target
        if self.state == "target_decide" and self.botPlay:
            pass

            self.state = "user_decide" #ends bot's decide turn, user's decide turn begins
        
        #target's turn
        if self.state == "target_decide":
            userDecideEmbed = discord.Embed(
                title = "Limit Dice 🎲",
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
            self.proceed.disabled = self.stopbtn.disabled = True #disables decision buttons

            #if target stopped, user last roll phase begins
            if "stop" in self.playersScore["targetRecord"]:
                if not self.playersScore["userBusted"]:
                    userProceedEmbed = discord.Embed(
                        title = "Limit Dice 🎲",
                        description = (
                            f"{self.target.mention if not self.botPlay else "I"} {"Stops" if not self.botPlay else "Stop"} !🤚"
                            f"\n{self.user.mention} Proceeds !🔄️"
                            f"\n\n{self.user.mention} hasn't rolled a six yet so it's their turn to roll for the last time."
                        ),
                        color = self.embedColor,
                        timestamp = self.timestamp
                    )
                    if self.slash:
                        await self.interaction.edit_original_response(embed = userProceedEmbed)
                    else:
                        await self.msg.edit(embed = userProceedEmbed)

                #if user is busted, match ends
                else:
                    return await self.endMatch()

                self.roll.disabled = False #enables roll button for the last time

                self.state = "user_last_roll" #ends user's decide turn, user's last roll turn begins

            #if target proceeded, another match begins
            else:
                self.match += 1 #increase the match number

                bothProceedEmbed = discord.Embed(
                    title = "Limit Dice 🎲",
                    description = (
                        f"{self.target.mention if not self.botPlay else "I"} {"Proceeds" if not self.botPlay else "Proceed"} !🔄️"
                        f"\n{self.user.mention} Proceeds !🔄️"
                        f"\nRound {self.match} begins."
                        f"\n\nIt's currently {self.target.mention}'s turn to roll their die." if not self.botPlay else "I've rolled my die already."
                    ),
                    color = self.embedColor,
                    timestamp = self.timestamp
                )
                if self.slash:
                    await self.interaction.edit_original_response(embed = bothProceedEmbed)
                else:
                    await self.msg.edit(embed = bothProceedEmbed)

                self.roll.disabled = False #enables roll button for a new match

                self.state = "target_roll" #ends user's decide turn, another match with target's roll turn begins
                if self.botPlay:
                    await self.botRoll()

    #defines stand button
    @discord.ui.button(label = "stop" , style = discord.ButtonStyle.gray, row = 2, disabled = True)
    async def stopbtn(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        #checks if only the user and target can interact with buttons
        if interaction.user.id not in (self.target.id, self.user.id):
            return await interaction.response.send_message("You can't play in this match.", ephemeral = True)
        
        #if user trys to decide when it's target's turn
        if not self.botPlay and self.state == "target_decide" and interaction.user.id != self.target.id:
            return await interaction.response.send_message(f"It's {self.target.mention}'s turn to decide.", ephemeral = True)
        
        #if target trys to decide when it's user's turn
        if self.state == "user_decide" and interaction.user.id != self.user.id:
            return await interaction.response.send_message(f"It's {self.user.mention}'s turn to decide.", ephemeral = True)
        
        #bot's turn, if bot is the target
        if self.state == "target_decide" and self.botPlay:
            self.playersScore["targetRecord"].append("stop")

            self.state = "user_decide" #ends bot's decide turn, user's decide turn begins

        #target's turn
        if self.state == "target_decide":
            self.playersScore["targetRecord"].append("stop")

            targetStopEmbed = discord.Embed(
                title = "Limit Dice 🎲",
                description = (
                    f"{self.target.mention} Stops !🤚"
                    f"\n\nIt's currently {self.user.mention}'s turn to decide."
                ),
                color = self.embedColor,
                timestamp = self.timestamp
            )
            if self.slash:
                await self.interaction.edit_original_response(embed = targetStopEmbed)
            else:
                await self.msg.edit(embed = targetStopEmbed)

            self.state = "user_decide" #ends target's decide turn, user's decide turn begins

        #users's turn
        elif self.state == "user_decide":
            self.stopbtn.disabled = self.proceed.disabled = True #disables decision buttons

            self.playersScore["userRecord"].append("stop")

            #if target stopped, match ends
            if "stop" in self.playersScore["targetRecord"]:
                return await self.endMatch(bothStopped = True)

            #if target proceeded, target last roll phase begins
            else:
                if not self.playersScore["targetBusted"]:
                    userStopEmbed = discord.Embed(
                        title = "Limit Dice 🎲",
                        description = (
                            f"{self.target.mention if not self.botPlay else "I"} {"Proceeds" if not self.botPlay else "Proceed"} !🔄️"
                            f"\n{self.user.mention} Stops !🤚"
                            f"\n\n{self.target.mention} hasn't rolled a six yet so it's their turn to roll for the last time."
                        ),
                        color = self.embedColor,
                        timestamp = self.timestamp
                    )
                    if self.slash:
                        await self.interaction.edit_original_response(embed = userStopEmbed)
                    else:
                        await self.msg.edit(embed = userStopEmbed)

                #if target is busted, match ends
                else:
                    return await self.endMatch()
                
                self.roll.disabled = False #enables roll button for the last time

                self.state = "target_last_roll" #ends user's decide turn, target's last roll turn begins
                if self.botPlay:
                    await self.botRoll()
            
    async def endMatch(self, bothBusted: bool = False, bothStopped: bool = False):
        #draw
        if self.playersScore["target"] == self.playersScore["user"]:
            winner = None
        #target wins
        elif self.playersScore["target"] > self.playersScore["user"]:
            winner = self.target
        #user wins
        else:
            winner = self.user

        if bothBusted:
            bothBustedStr = "Both players rolled 6 !\n\n" if not self.botPlay else "We both rolled 6 !\n\n"
        else:
            bothBustedStr = ""
        if bothStopped:
            bothStoppedStr = "Both players stopped ! and..\n\n" if not self.botPlay else "We both stopped ! and..\n\n"
        else:
            bothStoppedStr = ""

        #winner string
        if winner:
            winnerStr = (
                f"**{winner.mention} has WON !!**"
                f"\nWith a result of `{max(self.playersScore["target"], self.playersScore["user"])} > {min(self.playersScore["target"], self.playersScore["user"])}`"
            )

            rematchStr = ""
        else:
            winnerStr = (
                f"It's a DRAW !!"
                f"\nWith a result of `{self.playersScore["target"]} = {self.playersScore["user"]}`"
            )

            rematchStr = (
                    "\n\nAnother match has begun to determine the winner."
                    f"\nIt's currently {self.target.mention}'s turn to roll the die." if not self.botPlay else "\nI rolled my die already."
                ) #rematch string
        
        #busted string
        if self.playersScore["targetBusted"] and self.playersScore["userBusted"]:
            bustedStr = f"\n\nBoth {self.target.mention if not self.botPlay else "I"} and {self.user.mention} were busted from match {self.playersScore["targetBusted"]} and {self.playersScore["userBusted"]} actually."
        elif self.playersScore["targetBusted"]:
            bustedStr = f"\n\n{self.target.mention if not self.botPlay else "I"} was busted from match {self.playersScore["targetBusted"]} actually."
        elif self.playersScore["userBusted"]:
            bustedStr = f"\n\n{self.user.mention} was busted from match {self.playersScore["userBusted"]} actually."
        else:
            bustedStr = ""

        resultEmbed = discord.Embed(
            title = "Limit Dice 🎲",
            description = bothBustedStr + bothStoppedStr + winnerStr + rematchStr + bustedStr,
            color = self.embedColor,
            timestamp = self.timestamp,
        )
        if self.slash:
            await self.interaction.edit_original_response(embed = resultEmbed)
        else:
            await self.msg.edit(embed = resultEmbed)

        #if draw, rematch
        if not winner:
            #resets stats for a rematch
            self.playersScore["target"] = self.playersScore["user"] = 0
            self.playersScore["targetRecord"] = self.playersScore["userRecord"] = []
            self.playersScore["targetBusted"] = self.playersScore["userBusted"] = None

            self.roll.disabled = False #enables roll button

            self.state = "target_roll" #a new match begins with target's roll turn
            if self.botPlay:
                await self.botRoll()
        else:
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
            title = "Limit Dice 🎲",
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