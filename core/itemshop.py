"""Contains the core logic of item shop system."""

from __future__ import annotations

__all__ = ["ITEMS"]

from enum import Enum
from typing import final, override

from core.bank import Account, AccountDoesntExistError, get_account


@final
class Item:
    """Represents an item shop item."""

    class Category(Enum):
        """The  class for different item categories."""

        DECORATIVE = "DECORATIVE"

        @override
        def __str__(self) -> str:
            return self.value

    class Rarity(Enum):
        """The class for different item rarities."""

        COMMON = 1
        UNCOMMON = 2
        RARE = 3
        EPIC = 4
        LEGENDARY = 5

        def __int__(self) -> int:
            return self.value

        @override
        def __str__(self) -> str:
            return self.name

    def __init__(
        self,
        *,
        category: Category,
        name: str,
        price: float,
        rarity: Rarity,
        desc: str | None = None,
    ) -> None:
        """Initialize item.

        Args:
            category (Category): The category of the item.
            name (str): The name of the item.
            price (float): The item price.
            rarity (Rarity): The rarity of the item.
            desc (str | None, optional): The item description. Defaults to None.

        """
        self.category = category
        self.name = name
        self.price = price
        self.rarity = rarity
        self.desc = desc

    @override
    def __str__(self) -> str:
        return self.name


# items available to buy from item shop
_ITEMS: tuple[Item, ...] = (
    Item(
        category=Item.Category.DECORATIVE,
        name="cookie",
        price=3,
        rarity=Item.Rarity.COMMON,
        desc="A decorative item, no purpose.",
    ),
    Item(
        category=Item.Category.DECORATIVE,
        name="milk",
        price=5,
        rarity=Item.Rarity.COMMON,
        desc="A decorative item, no purpose.",
    ),
)


def get_items() -> dict[str, list[Item]]:
    """Get the available items to but from the item shop.

    Returns:
        dict[str, list[Item]]: A dictionary with different item categories as keys and
            related items in a list as their values.

    """
    categorized_items: dict[str, list[Item]] = {}
    for item in _ITEMS:
        categorized_items.setdefault(item.category.value, []).append(item)
    for category in categorized_items:  # noqa: PLC0206
        categorized_items[category].sort(key=lambda item: item.name)
    # Return dictionay but with sorted keys.
    return dict(
        sorted(categorized_items.items(), key=lambda item: item[0].lower()),
    )


ITEMS = get_items()


async def buy(account: Account | int, item: Item, quantity: int) -> None:
    if isinstance(account, int):
        acc = await get_account(account)
        if acc:
            account = acc

        else:
            raise AccountDoesntExistError

    await account.withdraw(
        item.price * quantity,
        reason=f"Bought {quantity} {item.name}.",
    )
