"""This file contains the core structure of the Bank system.
It contains all the logic such as required classes and related functions to do various operations
listed below:
1- Accounts: creating, depositing, withdrawing and etc.
2- Checks: issuing and depositing.
3- Transactions: Storing transactions.

Also, it should be note that the logic in this module is only and only made for Amelie's developers' workspace ease
and no real user should be able to work, interact or see any of the operations, messages or raised errors below.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from core.database import execute, fetchone
from core.dbconstants import AccountTable, CheckTable, TransactionTable
from core.logHandler import loggerSetup

# currency information
CURRENCY_NAME = "Cookie"
CURRENCY_ICON = "<:1lvl:1027191671328354304>"  # discord emoji
CURRENCY_STR = CURRENCY_ICON + " " + CURRENCY_NAME + "s"

logger = loggerSetup(__name__)
__all__ = [
    "BankErrors",
    "Account",
    "Check",
    "balance_transfer",
    "create_account",
    "delete_account",
    "get_account",
    "get_check",
    "issue_check",
]


# exception classes
class BankErrors(Exception):
    """The base class for all bank exceptions."""

    pass


class AccountDoesntExist(BankErrors):
    """When trying to do an operation on an account that doesn't exist."""

    pass


class AccountExists(BankErrors):
    """When trying to create an account for a user who already has one."""

    pass


class InsufficientBalance(BankErrors):
    """When trying to transfer an amount of balance that is insufficient."""

    pass


class AlreadyDepositedCheck(BankErrors):
    """When trying to deposit a check that is already deposited."""

    pass


class AlreadyIssuedCheck(BankErrors):
    """When trying to issue a check that is issued already."""

    pass


class UnnecessaryOperation(BankErrors):
    """When trying to do an unnecessary operation that doesn't change anything."""

    pass


class TransactionTypes(Enum):
    """The class for possible transaction types."""

    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    TRANSFER = "TRANSFER"
    BALANCESET = "BALANCESET"

    def __str__(self) -> str:
        return self.value


class Account:
    """The class representing a bank Account."""

    def __init__(
        self,
        *,
        user_id: int,
        balance: int = 0,
        created_at: datetime,
        last_daily_date: datetime | None = None,
        last_work_date: datetime | None = None,
    ) -> None:
        """Initiates the instance.

        Args:
            user_id (int): The ID of the user.
            created_at (datetime): The account creation date.
            balance (int, optional): The balance of the account. Defaults to 0.
            last_daily_date (datetime | None, optional): The date of the last time the user claimed daily reward. Defaults to None.
            last_work_date (datetime | None, optional): The date of the last time the user has worked. Defaults to None.

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
        self.last_work_date = last_work_date

    @property
    def balance_str(self) -> str:
        """Returns a string made of balance number plus currency name and icon."""

        return str(self.balance) + " " + CURRENCY_STR

    async def deposit(self, quantity: int, reason: str | None = None) -> Transaction:
        """Deposits to the account.

        Args:
            quantity (int): The quantity to deposit.
            reason (str | None, optional): The reason of the transaction. Defaults to None.

        Raises:
            ValueError: If a negative number is given.

        Returns:
            Transaction: The transaction.
        """

        # if a negative number is given
        if quantity < 0:
            raise ValueError("The deposition amount can't be negative.")

        # if quantity is 0
        if quantity == 0:
            raise UnnecessaryOperation("The deposition amount can't be 0.")

        # updates the user's balance
        self.balance += quantity
        await execute(
            f"""
            UPDATE {AccountTable.TABLE_NAME}
            SET {AccountTable.COL_BALANCE} = ?
            WHERE {AccountTable.COL_USER_ID} = ?;
            """,
            (self.balance, self.user_id),
        )

        # creates the transaction
        return await Transaction(
            type=TransactionTypes.DEPOSIT,
            user_id=self.user_id,
            amount=quantity,
            reason=reason,
        ).commit()  # returns the transaction

    async def withdraw(self, quantity: int, reason: str | None = None) -> Transaction:
        """Withdraws from the account.

        Args:
            quantity (int): The quantity to withdraw.
            reason (str | None, optional): The reason of the transaction. Defaults to None.

        Raises:
            ValueError: If a negative number is given.
            InsufficientBalance: If the withdraw quantity is higher than current balance.

        Returns:
            Transaction: The transaction.
        """

        # if a negative number is given
        if quantity < 0:
            raise ValueError("The withdrawal amount can't be negative.")

        # if quantity is 0
        if quantity == 0:
            raise UnnecessaryOperation("The withdrawal amount can't be 0.")

        # if withdraw amount is higher than the current balance
        if quantity > self.balance:
            raise InsufficientBalance(
                "The withdrawal amount is higher than current balance."
            )

        # updates the user's balance
        self.balance -= quantity
        await execute(
            f"""
            UPDATE {AccountTable.TABLE_NAME}
            SET {AccountTable.COL_BALANCE} = ?
            WHERE {AccountTable.COL_USER_ID} = ?;
            """,
            (self.balance, self.user_id),
        )

        return await Transaction(
            type=TransactionTypes.WITHDRAW,
            user_id=self.user_id,
            amount=quantity,
            reason=reason,
        ).commit()  # returns the transaction

    async def transfer_money_to(
        self, receiver_id: int, quantity: int, reason: str | None = None
    ) -> Transaction | None:
        """Transfers from an account to another.

        Args:
            receiver_id (int): The ID of the receiver.
            quantity (int): The quantity to transfer.
            reason (str | None, optional): The reason of the transaction. Defaults to None.

        Raises:
            ValueError: If the given number is negative.
            InsufficientBalance: If the given number to be transfered is higher than current balance.
            AccountDoesntExist: If the receiver's account is not found.

        Returns:
            Transaction | None: The transaction. `None`, if the quantity is 0.
        """

        # if a negative number is given
        if quantity < 0:
            raise ValueError("The quantity to transfer can't be negative.")

        # if quantity is 0
        if quantity == 0:
            raise UnnecessaryOperation("The balance transfering amount can't be 0.")

        # if given quantity is higher than balance
        if quantity > self.balance:
            raise InsufficientBalance(
                "The balance transfering amount is higher than current balance."
            )

        receiver_account = await get_account(
            receiver_id
        )  # tries to fetch the receiver's account
        # if no account is found
        if not receiver_account:
            raise AccountDoesntExist("There is no such account to transfer balance to.")

        # withdraws from sender's account
        self.balance -= quantity
        await execute(
            f"""
            UPDATE {AccountTable.TABLE_NAME}
            SET {AccountTable.COL_BALANCE} = ?
            WHERE {AccountTable.COL_USER_ID} = ?;
            """,
            (self.balance, self.user_id),
        )

        # deposits to receiver's account
        receiver_account.balance += quantity
        await execute(
            f"""
            UPDATE {AccountTable.TABLE_NAME}
            SET {AccountTable.COL_BALANCE} = ?
            WHERE {AccountTable.COL_USER_ID} = ?;
            """,
            (receiver_account.balance, receiver_account.user_id),
        )

        return await Transaction(
            type=TransactionTypes.TRANSFER,
            user_id=self.user_id,
            amount=quantity,
            receiver_id=receiver_id,
            reason=reason,
        ).commit()  # returns the transaction

    async def set_balance(
        self, quantity: int, reason: str | None = None
    ) -> Transaction | None:
        """Sets the account's balance.

        Args:
            quantity (int): The balance number to be set.
            reason (str | None, optional): The reason of the transaction. Defaults to None.

        Raises:
            ValueError: If a negative balance number is given.

        Returns:
            Transaction | None: The transaction. `None`, if the new balance is equal to the previous one.
        """

        # if a negative number is given
        if quantity < 0:
            raise ValueError("The balance number can't be negative.")

        # if the new balance is equal to the previous one
        if quantity == self.balance:
            return None

        # updates the user's balance
        self.balance = quantity
        await execute(
            f"""
            UPDATE {AccountTable.TABLE_NAME}
            SET {AccountTable.COL_BALANCE} = ?
            WHERE {AccountTable.COL_USER_ID} = ?;
            """,
            (self.balance, self.user_id),
        )

        return await Transaction(
            type=TransactionTypes.BALANCESET,
            user_id=self.user_id,
            amount=quantity,
            reason=reason,
        ).commit()  # returns the transaction

    async def delete(self) -> None:
        """Deletes the account."""

        # deletes the account
        await execute(
            f"""
            DELETE FROM {AccountTable.TABLE_NAME}
            WHERE {AccountTable.COL_USER_ID} = ?;
            """,
            (self.user_id,),
        )


class Check:
    """The class representing a check."""

    def __init__(
        self,
        *,
        check_id: str | None = None,
        sender_id: int,
        amount: int,
        receiver_id: int,
        reason: str | None = None,
        date: datetime | None = None,
        deposited: bool = False,
    ) -> None:
        """Initiates the instance.

        Args:
            sender_id (int): The ID of the sender.
            amount (int): The amount of the check.
            receiver_id (int): The ID of the receiver.
            check_id (str | None, optional): The check ID. It must be left empty if issuing, as it will be generated automatically. Defaults to None.
            reason (str | None, optional): The reason for issuing the check. Defaults to None.
            date (datetime | None, optional): The issued date. It must be left empty if issuing, as it will be generated automatically. Defaults to None.
            deposited (bool, optional): The deposition state. Defaults to False.

        Raises:
            ValueError: If a negative amount is given.
        """

        # if a negative amount is given
        if amount < 0:
            raise ValueError("The amount can't be negative.")

        # if quantity is 0
        if amount == 0:
            raise UnnecessaryOperation("The check amount can't be 0.")

        self.check_id = check_id or str(uuid.uuid4())
        self.sender_id = sender_id
        self.amount = amount
        self.receiver_id = receiver_id
        self.reason = reason
        self.date = date
        self.deposited = deposited

    async def issue(self) -> Transaction:
        """Issues a bank check.

        Raises:
            AlreadyIssuedCheck: If trying to issue an already issued check.
            AccountDoesntExist: If the sender bank account can not be fetched.

        Returns:
            Transaction: The transaction.
        """

        # if the check is already issued
        if self.date:
            raise AlreadyIssuedCheck("This check is already issued.")

        sender_account = await get_account(
            self.sender_id
        )  # tries to fetch sender's account
        # if sender has no account
        if not sender_account:
            raise AccountDoesntExist("The sender has no account to issue a check.")

        self.date = datetime.now(timezone.utc)  # generates the check date

        # withdraws the check amount from the sender's account and returns the transaction
        tran = await sender_account.withdraw(self.amount, reason="Check Issuance.")

        # saves the check info in the db
        await execute(
            f"""
            INSERT INTO {CheckTable.TABLE_NAME} ({CheckTable.columns})
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                self.check_id,
                self.sender_id,
                self.amount,
                self.receiver_id,
                self.reason,
                int(self.date.timestamp()),
                0,
            ),
        )

        return tran

    async def deposit(self) -> Transaction:
        """Deposits the check into receiver's account.

        Raises:
            AlreadyDepositedCheck: If trying to deposit an already deposited check.
            AccountDoesntExist: If the receiver's bank account can not be fetched.

        Returns:
            Transaction: The transaction.
        """

        # if the check is already deposited
        if self.deposited:
            raise AlreadyDepositedCheck(
                "This check is already deposited in the receiver's account."
            )

        receiver_account = await get_account(
            self.receiver_id
        )  # tries to fetch receiver's account
        # if receiver has no account
        if not receiver_account:
            raise AccountDoesntExist("The receiver has no account to deposit into.")

        # deposits the check amount to the receiver's account and returns the transaction
        tran = await receiver_account.deposit(self.amount, reason="Check Deposition.")

        # updates the state of the check in the db
        await execute(
            f"""
            UPDATE {CheckTable.TABLE_NAME}
            SET {CheckTable.COL_DEPOSITED} = ?
            WHERE {CheckTable.COL_ID} = ?;
            """,
            (1, self.check_id),
        )

        return tran


class Transaction:
    "The class representing a bank transaction."

    def __init__(
        self,
        *,
        type: TransactionTypes,
        user_id: int,
        amount: int,
        receiver_id: int | None = None,
        reason: str | None = None,
    ) -> None:
        """Initiates the instance.

        Args:
            type (TransactionTypes): The type of the transaction.
            user_id (int): The ID of the user.
            amount (int): The amount of the operation.
            receiver_id (int | None, optional): The ID of the receiver if the transaction type is to transfer. Defaults to None.
            reason (str | None, optional): The reason of the transaction. Defaults to None.

        Raises:
            ValueError: If transaction type is to transfer while no receiver ID is given.
        """

        # if transaction type is transfer but no receiver ID is given
        if type.value == TransactionTypes.TRANSFER.value and not receiver_id:
            raise ValueError(
                'The receiver ID can\'t be empty while the transaction type is "Transfer".'
            )

        # if a negative amount is given
        if amount < 0:
            raise ValueError("The amount can't be negative.")

        self.transaction_id = str(uuid.uuid4())
        self.type = type.value
        self.user_id = user_id
        self.amount = amount
        self.receiver_id = receiver_id
        self.reason = reason

    async def commit(self) -> Transaction:
        """Commits the changes and stores the transaction.
        This method must be called right after creation.

        Returns:
            Transaction: The created transaction.
        """

        # creates the transaction
        self.date = datetime.now(timezone.utc)
        await execute(
            f"""
            INSERT INTO {TransactionTable.TABLE_NAME} ({TransactionTable.columns()})
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                self.transaction_id,
                self.type,
                self.user_id,
                self.amount,
                int(self.date.timestamp()),
                self.receiver_id,
                self.reason,
            ),
        )
        return self


async def balance_transfer(
    *, sender_id: int, receiver_id: int, quantity: int, reason: str | None = None
) -> Transaction | None:
    """An alternative way to transfer balance between bank accounts through senders ID.

    Args:
        sender_id (int): The ID of the sender.
        receiver_id (int): The ID of the receiver.
        quantity (int): The quantity to transfer.
        reason (str | None, optional): The reason of the transaction. Defaults to None.

    Raises:
        AccountDoesntExist: If the sender has no bank account.

    Returns:
        Transaction | None: The transaction. `None`, if the quantity is 0.
    """

    sender_account = await get_account(sender_id)  # tries to fetch the sender's account
    # if no account is found for the sender
    if not sender_account:
        raise AccountDoesntExist("The sender has no account to transfer anything.")

    return await sender_account.transfer_money_to(
        receiver_id, quantity, reason
    )  # transfers the money


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

    account = await get_account(user_id)  # tries to fetch user's account
    # if user already has an account
    if account:
        raise AccountExists("This user already has an account.")

    # if a negative credit is given for balance
    if balance < 0:
        raise ValueError("Balance can't be negative.")

    now = datetime.now(timezone.utc)  # timestamp
    await execute(
        f"""
        INSERT INTO {AccountTable.TABLE_NAME} ({AccountTable.columns()})
        VALUES (?, ?, ?, ?, ?);
        """,
        (user_id, balance, int(now.timestamp()), None, None),
    )

    return Account(
        user_id=user_id, balance=balance, created_at=now
    )  # returns the created account instance


async def delete_account(user_id: int) -> None:
    """Deletes a bank account.

    Args:
        user_id (int): The ID of the user.

    Raises:
        AccountDoesntExist: If trying to delete the account of a user who hasn't one already.
    """

    account = await get_account(user_id)  # tries to fetch the user's account
    # if user has already no account.
    if not account:
        raise AccountDoesntExist("This user has no account to be deleted.")

    await account.delete()  # deletes the account


async def get_account(user_id: int) -> Account | None:
    """Fetches a bank account via user's ID.

    Args:
        user_id (int): The ID of the user.

    Returns:
        Account | None: The fetched account, if the user with given ID has an account. `None`, otherwise.
    """

    # tries to fetch the account
    row = await fetchone(
        f"""
        SELECT * FROM {AccountTable.TABLE_NAME}
        WHERE {AccountTable.COL_USER_ID} = ?;
        """,
        (user_id,),
    )
    if not row:
        return None

    return Account(
        user_id=row["user_id"],
        balance=row["balance"],
        created_at=datetime.fromtimestamp(row["created_at"]),
        last_daily_date=(
            datetime.fromtimestamp(row["last_daily_date"])
            if row["last_daily_date"]
            else None
        ),
        last_work_date=(
            datetime.fromtimestamp(row["last_work_date"])
            if row["last_work_date"]
            else None
        ),
    )  # creates an account instance based on the fetched data and returns it


async def get_check(check_id: str) -> Check | None:
    """Fetches a bank check via it's ID.

    Args:
        check_id (str): The ID of the check.

    Returns:
        Check | None: The fetched check if found. `None`, otherwise.
    """

    # tries to fetch the check
    row = await fetchone(
        f"""
        SELECT * FROM {CheckTable.TABLE_NAME}
        WHERE {CheckTable.COL_ID} = ?;
        """,
        (check_id,),
    )
    if not row:
        return None

    return Check(
        check_id=row["id"],
        sender_id=row["sender_id"],
        amount=row["amount"],
        receiver_id=row["receiver_id"],
        reason=row["reason"],
        date=datetime.fromtimestamp(row["date"]),
        deposited=(row["deposited"] == 1),
    )  # creates a check instance based on the fetched data and returns it


async def issue_check(
    *,
    sender_id: int,
    amount: int,
    receiver_id: int,
    reason: str | None = None,
) -> Transaction | None:
    """An alternative method to issue a bank check.

    Args:
        sender_id (int): The ID of the sender.
        amount (int): The amount of the check.
        receiver_id (int): The ID of the receiver.
        reason (str | None, optional): The reason of the check. Defaults to None.

    Returns:
        Transaction | None: The transaction. `None` if the amount is 0.
    """

    return await Check(
        sender_id=sender_id,
        amount=amount,
        receiver_id=receiver_id,
        reason=reason,
    ).issue()
