import discord
from discord.ext import commands
from discord import app_commands
from database import eco
from enum import Enum
from cogs.utility.help import HelpData
from core.logHandler import loggerSetup

logger = loggerSetup(__name__)


class Item:
    class Category(Enum):
        Decorative = "decorative"

        def __str__(self):
            return self.name

    class Rarity(Enum):
        common = 1
        uncommon = 2
        rare = 3
        epic = 4
        legendary = 5

        def __int__(self):
            return self.value

    def __init__(
        self,
        *,
        category: Category,
        name: str,
        price: float,
        rarity: Rarity,
        desc: str | None = None,
    ):
        self.category = category
        self.name = name
        self.price = price
        self.rarity = rarity
        self.desc = desc


items = [
    Item(
        category=Item.Category.Decorative,
        name="cookie",
        price=3,
        rarity=Item.Rarity.common,
        desc="A decorative item, no purpose.",
    ),
    Item(
        category=Item.Category.Decorative,
        name="milk",
        price=5,
        rarity=Item.Rarity.common,
        desc="A decorative item, no purpose.",
    ),
]
categorized: dict[str, list[Item]] = {}
for item in items:
    categorized.setdefault(item.category.value, []).append(item)
for category in categorized:
    categorized[category].sort(key=lambda item: item.name)
categorized = dict(
    sorted(categorized.items(), key=lambda item: item[0].lower())
)  # rebuilds the dictionary but sorted keys this time


class Itemshop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help = HelpData(
        category=HelpData.Category.Economy,
        dmOnly=False,
        serverOnly=False,
        subcommands=None,
        permissions=None,
        help=None,
        brief="Shows the Itemshop.",
        usage=None,
        aliases=["is", "items"],
    )

    @commands.command(name="itemshop", **Help.to_kwargs)
    async def itemshop(self, ctx: commands.Context[commands.Bot]):
        categoryEmbeds: list[discord.Embed] = (
            []
        )  # store different embeds for different categories
        for category, itemList in categorized.items():
            # creates a different embed for every each category
            embed = discord.Embed(
                title=category.title(),
                description="\n\n".join(
                    f"{item.name.title()} - {item.price}{eco.currency_postfix} - {item.rarity.name}:\n{item.desc if item.desc else "No description provided for this item."}"
                    for item in itemList
                ),
                color=discord.Color.blurple(),
            ).set_author(name="Itemshop")
            categoryEmbeds.append(embed)

        # if there's only one category and one embed, sends it without without view and buttons
        if len(categoryEmbeds) == 1:
            await ctx.reply(embed=categoryEmbeds[0])

        # sends the view otherwise
        else:
            view = ItemshopView(
                ctx, categoryEmbeds=categoryEmbeds
            )  # initializes the view
            await view.start()

    @itemshop.error
    async def itemshop_error(
        self, ctx: commands.Context[commands.Bot], error: commands.CommandError
    ):
        logger.exception(f"❌ something went wrong with itemshop command:")
        await ctx.reply("something went wrong with **itemshop**.")

    # itemshop slash command
    @app_commands.command(name="itemshop", description=Help.brief, extras=Help.extras)
    async def slashItemshop(
        self, interaction: discord.Interaction, ephemeral: bool = False
    ):
        categoryEmbeds: list[discord.Embed] = (
            []
        )  # store different embeds for different categories
        for category, itemList in categorized.items():
            # creates a different embed for every each category
            embed = discord.Embed(
                title=category.title(),
                description="\n\n".join(
                    f"{item.name.title()} - {item.price}{eco.currency_postfix} - {item.rarity.name}:\n{item.desc if item.desc else "No description provided for this item."}"
                    for item in itemList
                ),
                color=discord.Color.blurple(),
            ).set_author(name="Itemshop")
            categoryEmbeds.append(embed)

        # if there's only one category and one embed, sends it without without view and buttons
        if len(categoryEmbeds) == 1:
            await interaction.response.send_message(
                embed=categoryEmbeds[0], ephemeral=ephemeral
            )

        # sends the view otherwise
        else:
            view = ItemshopView(
                interaction, categoryEmbeds=categoryEmbeds, ephemeral=ephemeral
            )  # initializes the view
            await view.start()

    @slashItemshop.error
    async def slashItemshop_error(
        self, interaction: discord.Interaction, error: Exception
    ):
        logger.exception(f"❌ something went wrong with /itemshop command:")
        try:
            await interaction.response.send_message(
                "something went wrong with **itemshop**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **itemshop**.", ephemeral=True
            )


class ItemshopView(discord.ui.View):
    def __init__(
        self,
        ctx: commands.Context[commands.Bot] | discord.Interaction,
        *,
        categoryEmbeds: list[discord.Embed],
        ephemeral: bool = False,
    ):
        super().__init__(timeout=60)
        if isinstance(ctx, discord.Interaction):
            self.slash = True
            self.interaction = ctx
        else:
            self.slash = False
            self.ctx = ctx
        self.user = self.interaction.user if self.slash else self.ctx.author
        self.categoryEmbeds = categoryEmbeds
        self.EmbedIndex = 0
        self.ephemeral = ephemeral

    async def start(self):
        # sends the itemshop menu from the first category
        if self.slash:
            await self.interaction.response.send_message(
                embed=self.categoryEmbeds[0], view=self, ephemeral=self.ephemeral
            )
        else:
            self.msg = await self.ctx.reply(embed=self.categoryEmbeds[0], view=self)

    # close button
    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, row=0)
    async def close(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't control this Itemshop menu. try `/itemshop` yourself.",
                ephemeral=True,
            )

        # deletes the menu
        if self.slash:
            await self.interaction.delete_original_response()
        else:
            await self.msg.delete()

        self.stop()

    # previous button
    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.grey, row=0)
    async def previous(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't control this Itemshop menu. try `/itemshop` yourself.",
                ephemeral=True,
            )

        self.EmbedIndex = (self.EmbedIndex - 1) % len(
            self.categoryEmbeds
        )  # previous embed

        await interaction.response.edit_message(
            embed=self.categoryEmbeds[self.EmbedIndex]
        )

    # next button
    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.grey, row=0)
    async def next(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't control this Itemshop menu. try `/itemshop` yourself.",
                ephemeral=True,
            )

        self.EmbedIndex = (self.EmbedIndex + 1) % len(self.categoryEmbeds)  # next embed

        await interaction.response.edit_message(
            embed=self.categoryEmbeds[self.EmbedIndex]
        )

    async def on_timeout(self):
        # disables buttons on timeout
        for btn in self.children:
            if isinstance(btn, discord.ui.Button):
                btn.disabled = True

        try:
            # edits the message to remove buttons on timeout
            if self.slash:
                await self.interaction.edit_original_response(view=None)
            else:
                await self.msg.edit(view=None)
        except discord.NotFound:
            pass

        self.stop()  # stops further interaction on timeout

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item[discord.ui.View],
    ):
        logger.exception(
            f"❌ something went wrong with itemshop interaction - button: {getattr(item, 'emoji', 'unknown')}"
        )
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "something went wrong with **itemshop**.", ephemeral=True
            )
        else:
            await interaction.followup.send(
                "something went wrong with **itemshop**.", ephemeral=True
            )

        self.stop()  # stops further interaction on error


async def setup(bot: commands.Bot):
    await bot.add_cog(Itemshop(bot))
