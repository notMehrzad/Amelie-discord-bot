import random
import discord
from discord.ext import commands
from discord import app_commands
from database import db, eco
from datetime import timedelta, datetime
from cogs.economy.daily import tdFormatter
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)


class Sudoku:
    """
    The class that represents a sudoku puzzle.
    """

    def __init__(self):
        self.sudo = self.sudoGenerator()

    def sudoGenerator(self):
        sudo: list[list[int]] = []

        sudo.append([])
        sudo.append([])
        jstart = 0
        jend = 3
        for _ in range(2):
            cageNumbers: list[int] = []
            for i in range(2):
                for j in range(jstart, jend):
                    allowedNumbers = [
                        n
                        for n in range(1, 7)
                        if n not in cageNumbers
                        and n not in sudo[i]
                        and n not in [r[j] for r in sudo if sudo.index(r) < i]
                    ]
                    choice = random.choice(allowedNumbers)
                    sudo[i].append(choice)
                    cageNumbers.append(choice)
            jstart += 3
            jend += 3

        self.leftyIndex = (random.randint(0, 1), random.randint(0, 2))
        self.rightyIndex = (random.randint(0, 1), random.randint(3, 5))

        self.lefty = sudo[self.leftyIndex[0]][self.leftyIndex[1]]
        sudo[self.leftyIndex[0]][self.leftyIndex[1]] = 0
        self.righty = sudo[self.rightyIndex[0]][self.rightyIndex[1]]
        sudo[self.rightyIndex[0]][self.rightyIndex[1]] = 0

        return sudo

    def setLefty(self, n: int):
        if n == self.lefty:
            self.sudo[self.leftyIndex[0]][self.leftyIndex[1]] = self.lefty
        else:
            raise ValueError("Incorrect lefty value.")

    def setRighty(self, n: int):
        if n == self.righty:
            self.sudo[self.rightyIndex[0]][self.rightyIndex[1]] = self.righty
        else:
            raise ValueError("Incorrect righty value.")

    def __str__(self):
        sudoStr: list[str] = []
        for i in self.sudo:
            sudoStr.append(
                " ".join(
                    (
                        f"{i[j] if i[j] else "X"}"
                        if j != 3
                        else f"| {i[j] if i[j] else "X"}"
                    )
                    for j in range(6)
                )
            )
        return sudoStr[0] + "\n" + sudoStr[1]


class Work(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help = HelpData(
        category=HelpData.Category.Economy,
        dmOnly=False,
        serverOnly=False,
        subcommands=None,
        permissions=None,
        help=None,
        brief="Works, i guess",
        usage=None,
        aliases=None,
    )

    @commands.command(name="work", **Help.to_kwargs)
    async def work(self, ctx: commands.Context[commands.Bot]):
        # checks the balance and the last work date of the user
        row = await db.fetchone(
            """
            SELECT balance, last_work_date FROM user
            WHERE user_id = ?;
            """,
            (ctx.author.id,),
        )
        # if user has no economy account
        if not row:
            return await ctx.reply(
                "You have no account to work for.\nTry `/daily` to get your first daily and account and try again."
            )

        now = discord.utils.utcnow()

        workDate: datetime | None = (
            datetime.fromisoformat(row["last_work_date"])
            if isinstance(row["last_work_date"], str)
            else row["last_work_date"]
        )
        # if user trys to work within the limited time
        if workDate and workDate + timedelta(minutes=90) > now:
            return await ctx.reply(
                f"You must rest `{tdFormatter(workDate + timedelta(minutes=90) - now)}` to be able to `work` again."
            )

        view = WorkView(ctx, userBalance=row["balance"])
        await view.start()

    @work.error
    async def work_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with work command:")
        await ctx.reply("something went wrong with **work**.")

    # work slash command
    @app_commands.command(name="work", description=Help.brief, extras=Help.extras)
    async def slashWork(self, interaction: discord.Interaction):
        # checks the balance and the last work date of the user
        row = await db.fetchone(
            """
            SELECT balance, last_work_date FROM user
            WHERE user_id = ?;
            """,
            (interaction.user.id,),
        )
        # if user has no economy account
        if not row:
            return await interaction.response.send_message(
                "You have no account to work for.\nTry `/daily` to get your first daily and account and try again.",
                ephemeral=True,
            )

        now = discord.utils.utcnow()

        workDate: datetime | None = (
            datetime.fromisoformat(row["last_work_date"])
            if isinstance(row["last_work_date"], str)
            else row["last_work_date"]
        )
        # if user trys to work within the limited time
        if workDate and workDate + timedelta(minutes=90) > now:
            return await interaction.response.send_message(
                f"You must rest `{tdFormatter(workDate + timedelta(minutes=90) - now)}` to be able to `work` again.",
                ephemeral=True,
            )

        view = WorkView(interaction, userBalance=row["balance"])
        await view.start()

    @slashWork.error
    async def slashWork_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /work command:")
        try:
            await interaction.response.send_message(
                "something went wrong with **work**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **work**.", ephemeral=True
            )


class WorkView(discord.ui.View):
    def __init__(
        self,
        ctx: commands.Context[commands.Bot] | discord.Interaction,
        *,
        userBalance: int,
    ):
        super().__init__(timeout=90)
        if isinstance(ctx, discord.Interaction):
            self.slash = True
            self.interaction = ctx
        else:
            self.slash = False
            self.ctx = ctx
        self.user = self.interaction.user if self.slash else self.ctx.author
        self.userBalance = userBalance
        self.timestamp = discord.utils.utcnow()
        self.sudo = Sudoku()

        n = [i for i in range(1, 7)]
        leftyBtns = [
            n.pop(self.sudo.lefty),
            *random.sample(n, 2),
        ]  # creates random buttons for the left X in sudoku containing the answer
        random.shuffle(leftyBtns)  # shuffles the options
        n = [i for i in range(1, 7)]
        self.rightyBtns = [
            n.pop(self.sudo.righty),
            *random.sample(n, 2),
        ]  # creates random buttons for the right X in sudoku containing the answer
        random.shuffle(self.rightyBtns)  # shuffles the options

        # creates and attachs the left buttons
        for i in leftyBtns:
            button: discord.ui.Button[discord.ui.View] = discord.ui.Button(
                style=discord.ButtonStyle.gray, label=str(i)
            )
            button.callback = self.leftyBtnsCallback(i)
            self.add_item(button)

    async def start(self):
        # sends the initial message
        sudokuEmbed = discord.Embed(
            title="Work ⛏️",
            description=(
                "Solve this Sudoku puzzle to earn your fee." f"\n\n{self.sudo}"
            ),
            color=discord.Color.blurple(),
        )
        if self.slash:
            await self.interaction.response.send_message(embed=sudokuEmbed, view=self)
        else:
            self.msg = await self.ctx.reply(embed=sudokuEmbed, view=self)

    def leftyBtnsCallback(self, value: int):
        async def callback(interaction: discord.Interaction):
            # checks that only the user can interact with the buttons
            if interaction.user.id != self.user.id:
                return await interaction.response.send_message(
                    "You can't work for others.", ephemeral=True
                )

            # if user chooses the wrong option
            if value != self.sudo.lefty:
                return await interaction.response.send_message(
                    "Wrong ! ❌", ephemeral=True
                )

            # removes the current buttons
            for btn in self.children:
                self.remove_item(btn)
            # creates and attachs new buttons
            for i in self.rightyBtns:
                button: discord.ui.Button[discord.ui.View] = discord.ui.Button(
                    style=discord.ButtonStyle.gray, label=str(i)
                )
                button.callback = self.rightyBtnsCallback(i)
                self.add_item(button)

            self.sudo.setLefty(value)  # sets the left X answer
            sudokuEmbed = discord.Embed(
                title="Work ⛏️",
                description=(
                    "Solve this Sudoku puzzle to earn your fee." f"\n\n{self.sudo}"
                ),
                color=discord.Color.blurple(),
            )
            await interaction.response.edit_message(embed=sudokuEmbed, view=self)

        return callback

    def rightyBtnsCallback(self, value: int):
        async def callback(interaction: discord.Interaction):
            # checks that only the user can interact with the buttons
            if interaction.user.id != self.user.id:
                return await interaction.response.send_message(
                    "You can't work for others.", ephemeral=True
                )

            # if user chooses the wrong option
            if value != self.sudo.righty:
                return await interaction.response.send_message(
                    "Wrong ! ❌", ephemeral=True
                )

            self.sudo.setRighty(value)  # sets the right X answer

            # updates the user balance
            await db.execute(
                """
                UPDATE user
                SET balance = ?, last_work_date = ?
                WHERE user_id = ?;
                """,
                (self.userBalance + eco.work, self.timestamp, self.user.id),
            )

            # sends the result
            resultEmbed = discord.Embed(
                title="Work ⛏️",
                description=(
                    "Good Job !"
                    f"\nYou earned **{eco.work}** for working so hard."
                    f"You must rest **{tdFormatter(timedelta(minutes=90))}** to fully recover and be able to work again."
                ),
                color=discord.Color.blurple(),
                timestamp=self.timestamp,
            )
            await interaction.response.edit_message(embed=resultEmbed, view=None)

            self.stop()

        return callback

    async def on_timeout(self):
        # disables buttons on timeout
        for btn in self.children:
            if isinstance(btn, discord.ui.Button):
                btn.disabled = True

        timeoutEmbed = discord.Embed(
            title="Work ⛏️",
            description="⏰ You quited your work too early honey.",
            color=discord.Color.dark_gray(),
            timestamp=self.timestamp,
        )
        try:
            # sends the timeout message
            if self.slash:
                await self.interaction.edit_original_response(
                    embed=timeoutEmbed, view=self
                )
            else:
                await self.msg.edit(embed=timeoutEmbed, view=self)
        # if context message is deleted
        except discord.NotFound:
            pass

        self.stop()  # stops the view upon timeout

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item[discord.ui.View],
    ):
        logger.exception(
            f"❌ something went wrong with work interaction - button: {getattr(item, 'label', 'unknown')}"
        )
        try:
            await interaction.response.send_message(
                "something went wrong with **work**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **work**.", ephemeral=True
            )

        self.stop()  # stops the view upon error


async def setup(bot: commands.Bot):
    await bot.add_cog(Work(bot))
