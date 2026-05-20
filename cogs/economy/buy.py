"""The `buy` command. It allows the users to but different items from the itemshop."""

import discord
from discord import app_commands
from discord.ext import commands

from core.database import execute, fetchone
from cogs.economy.itemshop import items
from core.help import *
from core.logHandler import loggerSetup

logger = loggerSetup(__name__)


class Buy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help = HelpData(
        category=CommandCategory.ECONOMY,
        dmOnly=False,
        serverOnly=False,
        subcommands=None,
        permissions=None,
        help=None,
        brief="Buys an Item from the Itemshop.",
        usage="<item_name> <quantity[*optional*]>",
        aliases=None,
    )

    @commands.command(name="buy", **Help.kwargs)
    async def buy(
        self,
        ctx: commands.Context[commands.Bot],
        item: str | None,
        quantity: int | str = 1,
    ):
        # trys to fetch user's balance
        row = await fetchone(
            """
            SELECT balance FROM user
            WHERE user_id = ?;
            """,
            (ctx.author.id,),
        )
        # if user has not account
        if not row:
            return await ctx.reply(
                "You have no account to but anything for it. Try `/daily` to claim your first daily and create an account."
            )

        # if user doesn't enter any item name
        if not item:
            return await ctx.reply("You must enter the Item name you want to buy.")

        # checks if entered item is available
        match = None
        for i in items:
            if i.name == item.lower():
                match = i
        if not match:
            return await ctx.reply(f"{item} is not a valid Item. See `/itemshop`.")

        # if user doesn't enter a valid quantity
        if not isinstance(quantity, int):
            return await ctx.reply("Enter a valid quantity.")

        # if user's balance is lower than the price
        if row["balance"] < (match.price * quantity):
            return await ctx.reply(
                f"Your current balance is lower than the amount that this amount of {match.name} will cost."
            )

        # updates user's balance
        await execute(
            """
            UPDATE user
            SET balance = ?
            WHERE user_id = ?;
            """,
            (row["balance"] - (match.price * quantity), ctx.author.id),
        )

        row = await fetchone(
            """
            SELECT quantity FROM inventory
            WHERE user_id = ? AND item_name = ?;
            """,
            (ctx.author.id, match.name),
        )
        # if user already has the item in the inventory, updates quantity
        if row:
            await execute(
                """
                UPDATE inventory
                SET quantity = ?
                WHERE user_id = ? AND item_name = ?;
                """,
                (row["quantity"] + quantity, ctx.author.id, match.name),
            )

        # adds the item to user's inventory otherwise
        else:
            await execute(
                """
                INSERT INTO inventory (user_id, item_name, quantity)
                VALUES (?, ?, ?);
                """,
                (ctx.author.id, match.name, quantity),
            )

        await ctx.reply(f"You have bought {quantity} {match.name} successfully.")

    @buy.error
    async def buy_error(
        self, ctx: commands.Context[commands.Bot], error: commands.CommandError
    ):
        logger.exception(f"❌ something went wrong with buy command:")
        await ctx.reply("something went wrong with **buy**.")

    # buy slash command
    @app_commands.command(name="buy", description=Help.brief, extras=Help.extras)
    @app_commands.describe(
        item="The Item to buy.", quantity="The amount of Item to buy."
    )
    async def slashBuy(
        self, interaction: discord.Interaction, item: str, quantity: int = 1
    ):
        # trys to fetch user's balance
        row = await fetchone(
            """
            SELECT balance FROM user
            WHERE user_id = ?;
            """,
            (interaction.user.id,),
        )
        # if user has not account
        if not row:
            return await interaction.response.send_message(
                "You have no account to but anything for it. Try `/daily` to claim your first daily and create an account.",
                ephemeral=True,
            )

        # if user doesn't enter any item name
        if not item:
            return await interaction.response.send_message(
                "You must enter the Item name you want to buy.", ephemeral=True
            )

        # checks if entered item is available
        match = None
        for i in items:
            if i.name == item.lower():
                match = i
        if not match:
            return await interaction.response.send_message(
                f"{item} is not a valid Item. See `/itemshop`.", ephemeral=True
            )

        # if user's balance is lower than the price
        if row["balance"] < (match.price * quantity):
            return await interaction.response.send_message(
                f"Your current balance is lower than the amount that this amount of {match.name} will cost.",
                ephemeral=True,
            )

        # updates user's balance
        await execute(
            """
            UPDATE user
            SET balance = ?
            WHERE user_id = ?;
            """,
            (row["balance"] - (match.price * quantity), interaction.user.id),
        )

        row = await fetchone(
            """
            SELECT quantity FROM inventory
            WHERE user_id = ? AND item_name = ?;
            """,
            (interaction.user.id, match.name),
        )
        # if user already has the item in the inventory, updates quantity
        if row:
            await execute(
                """
                UPDATE inventory
                SET quantity = ?
                WHERE user_id = ? AND item_name = ?;
                """,
                (row["quantity"] + quantity, interaction.user.id, match.name),
            )

        # adds the item to user's inventory otherwise
        else:
            await execute(
                """
                INSERT INTO inventory (user_id, item_name, quantity)
                VALUES (?, ?, ?);
                """,
                (interaction.user.id, match.name, quantity),
            )

        await interaction.response.send_message(
            f"You have bought {quantity} {match.name} successfully."
        )

    @slashBuy.error
    async def slashBuy_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /buy command:")
        try:
            await interaction.response.send_message(
                "something went wrong with **buy**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **buy**.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Buy(bot))
