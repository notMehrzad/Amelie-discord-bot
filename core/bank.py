"""This file contains the core structure of the Bank system.
It contains all the logic such as required classes and related functions to do various operations
such as depositing, withdrawing, transfering balance and etc.

Also, it should be note that the logic in this module is only and only made for Amelie's developers' workspace ease
and no real user should be able to work, interact or see any of the operations, messages or raised errors bellow.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from database import db
from logHandler import loggerSetup

# currency information
CURRENCY_NAME = "Cookie"
CURRENCY_ICON = "<:1lvl:1027191671328354304>"  # discord emoji
CURRENCY_STR = CURRENCY_ICON + " " + CURRENCY_NAME + "s"

# bank account table
ACCOUNT_TABLE = """
    CREATE TABLE IF NOT EXISTS bank_accounts (
        user_id INTEGER PRIMARY KEY NOT NULL,
        balance INTEGER NOT NULL,
        created_at INTEGER NOT NULL,
        last_daily_date INTEGER,
        last_work_date INTEGER
    );
    """
# bank transaction table
TRANSACTION_TABLE = """
    CREATE TABLE IF NOT EXISTS bank_transactions (
        transaction_id TEXT PRIMARY KEY NOT NULL,
        type TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        date INTEGER NOT NULL,
        reciever_id INTEGER,
        reason TEXT
    );
    """

logger = loggerSetup(__name__)
__all__ = [
    "BankErrors",
    "AccountExists",
    "AccountDoesntExist",
    "InsufficientBalance",
    "TransactionTypes",
    "Transaction",
    "Account",
    "get_account",
    "create_account",
    "balance_transfer",
    "delete_account",
]


class BankErrors(Exception):
    """The base class for all bank exceptions."""

    pass


class AccountExists(BankErrors):
    """When trying to create an account for a user who aleardy has one."""

    pass


class AccountDoesntExist(BankErrors):
    """When trying to do an operation on an account that doesn't exist."""

    pass


class InsufficientBalance(BankErrors):
    """When trying to transfer an amount of balance that is insufficient."""

    pass


class TransactionTypes(Enum):
    """The class for possible transaction types."""

    Deposit = "Deposit"
    Withdraw = "Withdraw"
    Transfer = "Transfer"
    BalanceSet = "BalanceSet"

    def __str__(self) -> str:
        return self.value


class Transaction:
    "The class representing a bank transaction."

    def __init__(
        self,
        *,
        type: TransactionTypes,
        user_id: int,
        amount: int,
        reciever_id: int | None = None,
        reason: str | None = None,
    ):
        """Initiates the instance.

        Args:
            type (TransactionTypes): The type of the transaction.
            user_id (int): The ID of the user.
            amount (int): The amount of the operation.
            reciever_id (int | None, optional): The ID of the reciever if the transaction type is to transfer. Defaults to None.
            reason (str | None, optional): The reason of the transaction. Defaults to None.

        Raises:
            ValueError: If transaction type is to transfer while no reciever ID is given.
        """

        # if transaction type is transfer but no reciever ID is given
        if type.value == TransactionTypes.Transfer.value and not reciever_id:
            raise ValueError(
                'The reciever ID can\'t be empty while the transaction type is "Transfer".'
            )

        self.transaction_id = str(uuid.uuid4())
        self.type = type.value
        self.user_id = user_id
        self.amount = amount
        self.reciever_id = reciever_id
        self.reason = reason

    async def commit(self) -> Transaction:
        """Commits the changes and stores the transaction.

        Returns:
            Transaction: The created transaction will be returned.
        """

        # creates the transaction
        self.date = datetime.now(timezone.utc)
        await db.execute(
            """
            INSERT INTO bank_transactions (transaction_id, type, user_id, amount, date, reciever_id, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                self.transaction_id,
                self.type,
                self.user_id,
                self.amount,
                int(self.date.timestamp()),
                self.reciever_id,
                self.reason,
            ),
        )
        return self


class Account:
    """The class representing a bank Account."""

    def __init__(
        self,
        *,
        user_id: int,
        balance: int = 0,
        created_at: datetime,
        last_daily_date: datetime | None = None,
    ):
        """Initiates the instance.

        Args:
            user_id (int): The ID of the user.
            created_at (datetime): The account creation date.
            balance (int, optional): The balance of the account. Defaults to 0.
            last_daily_date (datetime | None, optional): The date of the last time the user claimed daily reward. Defaults to None.

        Raises:
            ValueError: If a negative balance number is given.
        """

        # if a negative balance is given
        if balance < 0:
            raise ValueError("The balance can't be a negative number.")

        self.user_id = user_id
        self.balance = balance
        self.created_at = created_at
        self.last_daily_date = last_daily_date

    @property
    def balance_str(self) -> str:
        return str(self.balance) + " " + CURRENCY_STR

    async def deposit(
        self, quantity: int, reason: str | None = None
    ) -> Transaction | None:
        """Deposits to the account.

        Args:
            quantity (int): The quantity to deposit.
            reason (str | None, optional): The reason of the transaction. Defaults to None.

        Raises:
            ValueError: If a negative number is given.
        """

        # if no quantity is given
        if quantity == 0:
            return None

        # if a negative number is given
        if quantity < 0:
            raise ValueError("The deposit number can't be negative.")

        # updates the user's balance
        self.balance += quantity
        await db.execute(
            """
            UPDATE FROM bank_accounts
            SET balance = ?
            WHERE user_id = ?;
            """,
            (self.balance, self.user_id),
        )

        # creates the transaction
        return await Transaction(
            type=TransactionTypes.Deposit,
            user_id=self.user_id,
            amount=quantity,
            reason=reason,
        ).commit()  # returns the transaction

    async def withdraw(
        self, quantity: int, reason: str | None = None
    ) -> Transaction | None:
        """Withdraws from the account.

        Args:
            quantity (int): The quantity to withdraw.
            reason (str | None, optional): The reason of the transaction. Defaults to None.

        Raises:
            ValueError: If a negative number is given.
        """

        # if no quantity is given
        if quantity == 0:
            return None

        # if a negative number is given
        if quantity < 0:
            raise ValueError("The withdraw number can't be negative.")

        # updates the user's balance
        self.balance -= quantity
        await db.execute(
            """
            UPDATE FROM bank_accounts
            SET balance = ?
            WHERE user_id = ?;
            """,
            (self.balance, self.user_id),
        )

        return await Transaction(
            type=TransactionTypes.Withdraw,
            user_id=self.user_id,
            amount=quantity,
            reason=reason,
        ).commit()  # returns the transaction

    async def transfer_money_to(
        self, reciever_id: int, quantity: int, reason: str | None = None
    ) -> Transaction | None:
        """Transfers from an account to another.

        Args:
            reciever_id (int): The ID of the reciever.
            quantity (int): The quantity to transfer.
            reason (str | None, optional): The reason of the transaction. Defaults to None.

        Raises:
            ValueError: If the given number is negative.
            InsufficientBalance: If the given number to be transfered is higher than current balance.
            AccountDoesntExist: If the reciever's account is not found.

        Returns:
            Transaction | None: The transaction. `None`, if the quantity is 0.
        """

        # if no quantity is given
        if quantity == 0:
            return None

        # if a negative number is given
        if quantity < 0:
            raise ValueError("The quantity to transfer can't be negative.")

        # if given quantity is higher than balance
        if quantity > self.balance:
            raise InsufficientBalance(
                "The given quantity is higher than current balance to transfer."
            )

        reciever_account = await get_account(
            reciever_id
        )  # trys to fetch the reciever's account
        # if no account is found
        if not reciever_account:
            raise AccountDoesntExist("There is no such account to transfer balance to.")

        # withdraws from sender's account
        self.balance -= quantity
        await db.execute(
            """
            UPDATE bank_account
            SET balance = ?
            WHERE user_id = ?;
            """,
            (self.balance, self.user_id),
        )

        # deposits to reciever's account
        reciever_account.balance += quantity
        await db.execute(
            """
            UPDATE bank_account
            SET balance = ?
            WHERE user_id = ?;
            """,
            (reciever_account.balance, reciever_account.user_id),
        )

        return await Transaction(
            type=TransactionTypes.Transfer,
            user_id=self.user_id,
            amount=quantity,
            reciever_id=reciever_id,
            reason=reason,
        ).commit()  # returns the transaction

    async def set_balance(
        self, quantity: int, reason: str | None = None
    ) -> Transaction:
        """Sets the account's balance.

        Args:
            quantity (int): The balance number to be set.
            reason (str | None, optional): The reason of the transaction. Defaults to None.

        Raises:
            ValueError: If a negative balance number is given.
        """

        # if a negative number is given
        if quantity < 0:
            raise ValueError("The balance number can't be negative.")

        # updates the user's balance
        self.balance = quantity
        await db.execute(
            """
            UPDATE FROM bank_accounts
            SET balance = ?
            WHERE user_id = ?;
            """,
            (self.balance, self.user_id),
        )

        return await Transaction(
            type=TransactionTypes.BalanceSet,
            user_id=self.user_id,
            amount=quantity,
            reason=reason,
        ).commit()  # returns the transaction

    async def delete(self) -> None:
        """Deletes the account."""

        # deletes the account
        await db.execute(
            """
            DELETE FROM bank_account
            WHERE user_id = ?;
            """,
            (self.user_id,),
        )
        del self


async def get_account(user_id: int) -> Account | None:
    """Fetches a bank account with user's ID.

    Args:
        user_id (int): The ID of the user.

    Returns:
        Account | None: The fetched account, if the user with given ID has an account. `None`, otherwise.
    """

    # trys to fetch the account
    row = await db.fetchone(
        """
        SELECT * FROM bank_accounts
        WHERE user_id = ?;
        """,
        (user_id,),
    )
    if not row:
        return None

    return Account(
        user_id=row["user_id"],
        balance=row["balance"],
        created_at=datetime.fromtimestamp(row["created_at"]),
        last_daily_date=datetime.fromtimestamp(row["last_daily_date"]),
    )  # creates an account instance based on the fetched data and returns it


async def create_account(*, user_id: int, balance: int = 0) -> Account:
    """Creates a bank account for the user.

    Args:
        user_id (int): The ID of the user.
        balance (int, optional): The initial balance the user will start with. Defaults to 0.

    Raises:
        AccountExists: If trying to create an account for a user who already has one.
        ValueError: If a negative number is given for balance.

    Returns:
        Account: The created account.
    """

    account = await get_account(user_id)  # trys to fetch user's account
    # if user already has an account
    if account:
        raise AccountExists("This user already has an account.")

    # if a negative credit is given for balance
    if balance < 0:
        raise ValueError("Balance can't be negative.")

    now = datetime.now(timezone.utc)  # timestamp
    await db.execute(
        """
        INSERT INTO bank_accounts (user_id, balance, created_at)
        VALUES (?, ?, ?);
        """,
        (user_id, balance, int(now.timestamp())),
    )

    return Account(
        user_id=user_id, balance=balance, created_at=now
    )  # returns the created account instance


async def balance_transfer(
    *, sender_id: int, reciever_id: int, quantity: int, reason: str | None = None
) -> Transaction | None:
    """An alternative way to transfer balance between bank accounts through senders ID.

    Args:
        sender_id (int): The ID of the sender.
        reciever_id (int): The ID of the reciever.
        quantity (int): The quantity to transfer.
        reason (str | None, optional): The reason of the transaction. Defaults to None.

    Raises:
        AccountDoesntExist: If the sender has no bank account.

    Returns:
        Transaction | None: The transaction. `None`, if the quantity is 0.
    """

    sender_account = await get_account(sender_id)  # trys to fetch the sender's account
    # if no account is found for the sender
    if not sender_account:
        raise AccountDoesntExist("The sender has no account to transfer anything.")

    return await sender_account.transfer_money_to(
        reciever_id, quantity, reason
    )  # transfers the money


async def delete_account(user_id: int) -> None:
    """Deletes a bank account.

    Args:
        user_id (int): The ID of the user.

    Raises:
        AccountDoesntExist: If trying to delete the account of a user who hasn't one already.
    """

    account = await get_account(user_id)  # trys to fetch the user's account
    # if user has already no account.
    if not account:
        raise AccountDoesntExist("This user has no account to be deleted.")

    await account.delete()  # deletes the account
