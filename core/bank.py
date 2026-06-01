"""Contains the core structure of Bank system.

It contains all the logic such as required classes and related functions to do various
operations listed below:
1- Accounts: creating, depositing, withdrawing etc.
2- Checks: issuing and depositing
3- Transactions: Storing transactions

Also, it should be noted that the logic in this module is only and only made for
Amelie's developers' workspace ease and no real user should be able to work, interact or
see any of the operations, messages or raised errors below.
"""

from __future__ import annotations

__all__ = [
    "CURRENCY_STR",
    "Account",
    "BankError",
    "Check",
    "balance_transfer",
    "create_account",
    "delete_account",
    "get_account",
    "get_check",
    "issue_check",
]

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import final, override

from core.database import execute, fetchone
from core.dbconstants import AccountTable, CheckTable, TransactionTable
from core.log_handler import logger_setup

# currency information
CURRENCY_NAME = "Cookie"
CURRENCY_ICON = "<:1lvl:1027191671328354304>"  # discord emoji
CURRENCY_STR = CURRENCY_ICON + " " + CURRENCY_NAME + "s"

logger = logger_setup(__name__)


# exception classes
class BankError(Exception):
    """Common base class for all bank.py exceptions."""


class AccountDoesntExistError(BankError):
    """Raised when trying to do an operation on an account that doesn't exist."""

    def __init__(self) -> None:
        super().__init__("This account doesn't exist.")


class AccountExistsError(BankError):
    """Raised when trying to create an account for a user who already has one."""

    def __init__(self) -> None:
        super().__init__("This user already has an account.")


class InsufficientBalanceError(BankError):
    """Raised when trying to transfer an amount of balance that is insufficient."""

    def __init__(self) -> None:
        super().__init__("The balance amount is insufficient for the operation.")


class AlreadyDepositedCheckError(BankError):
    """Raised when trying to deposit a check that is already deposited."""

    def __init__(self, check: Check) -> None:
        self.check = check
        super().__init__("This check has been already deposited.")


class AlreadyIssuedCheckError(BankError):
    """Raised when trying to issue a check that is issued already."""

    def __init__(self, check: Check) -> None:
        self.check = check
        super().__init__("This check has been already issued.")


class UnnecessaryOperationError(BankError):
    """Raised when trying to do an unnecessary operation."""

    def __init__(self) -> None:
        super().__init__(
            "The operation is unnecessary and doesn't change anything in the account.",
        )


@final
class Account:
    """Represents a bank Account."""

    def __init__(
        self,
        *,
        user_id: int,
        balance: float = 0,
    ) -> None:
        """Initialize a bank account.

        Args:
            user_id (int): ID of the user.
            balance (float, optional): Initial balance of the account. Defaults to 0.

        Raises:
            ValueError: Raise when a negative balance number is given.

        """
        # Raise an error if a negative balance is given.
        if balance < 0:
            msg = "The balance can't be a negative number."
            raise ValueError(msg)

        self.user_id: int = user_id
        self.balance: float = balance
        self.created_at: datetime | None = None
        self.last_daily_date: datetime | None = None
        self.last_work_date: datetime | None = None

    @property
    def balance_str(self) -> str:
        """Return a string made of balance number plus currency name and icon."""
        return str(self.balance) + " " + CURRENCY_STR

    async def deposit(
        self,
        quantity: float,
        reason: str | None = None,
    ) -> Transaction:
        """Deposit to the account.

        Args:
            quantity (float): Quantity to deposit.
            reason (str | None, optional): Reason of the transaction. Defaults to None.

        Raises:
            ValueError: Raise when a negative number is given.

        Returns:
            Transaction: Return the transaction.

        """
        # Raise an error if a negative quantity is given.
        if quantity < 0:
            msg = "Deposition amount can not be negative."
            raise ValueError(msg)

        # Raise an error if quantity is zero.
        if quantity == 0:
            raise UnnecessaryOperationError

        # Update the user's balance.
        self.balance += quantity
        await execute(
            f"""
            UPDATE {AccountTable.TABLE_NAME}
            SET {AccountTable.COL_BALANCE} = ?
            WHERE {AccountTable.COL_USER_ID} = ?;
            """,  # noqa: S608
            (self.balance, self.user_id),
        )

        # Create  and return the transaction.
        return await Transaction(
            tran_type=Transaction.TYPES.DEPOSIT,
            user_id=self.user_id,
            amount=quantity,
            reason=reason,
        ).commit()

    async def withdraw(
        self,
        quantity: float,
        reason: str | None = None,
    ) -> Transaction:
        """Withdraw from the account.

        Args:
            quantity (float): Quantity to withdraw.
            reason (str | None, optional): Reason of the transaction. Defaults to None.

        Raises:
            ValueError: Raise when a negative quantity is given.
            InsufficientBalance: Raise when the withdrawal quantity is higher than
                current balance.

        Returns:
            Transaction: Return the transaction.

        """
        # Raise an error if a negative quantity is given.
        if quantity < 0:
            msg = "The withdrawal amount can't be negative."
            raise ValueError(msg)

        # Raise an error if quantity is zero.
        if quantity == 0:
            raise UnnecessaryOperationError

        # Raise if  withdraw amount is higher than the current balance.
        if quantity > self.balance:
            raise InsufficientBalanceError

        # Update the user's balance.
        self.balance -= quantity
        await execute(
            f"""
            UPDATE {AccountTable.TABLE_NAME}
            SET {AccountTable.COL_BALANCE} = ?
            WHERE {AccountTable.COL_USER_ID} = ?;
            """,  # noqa: S608
            (self.balance, self.user_id),
        )

        # Create and return the transaction
        return await Transaction(
            tran_type=Transaction.TYPES.WITHDRAW,
            user_id=self.user_id,
            amount=quantity,
            reason=reason,
        ).commit()

    async def transfer_money_to(
        self,
        receiver_id: int,
        quantity: float,
        reason: str | None = None,
    ) -> Transaction:
        """Transfer balance from an account to another.

        Args:
            receiver_id (int): ID of receiver.
            quantity (float): Quantity to transfer.
            reason (str | None, optional): Reason of transaction. Defaults to None.

        Raises:
            ValueError: Raise when quantity is negative.
            UnnecessaryOperation: Raise when quantity is zero.
            InsufficientBalance: Raise when quantity is higher than current balance.
            AccountDoesntExist: Raise when receiver's account is not found.

        Returns:
            Transaction: Return transaction.

        """
        # Raise an error if quantity is negative.
        if quantity < 0:
            msg = "The quantity to transfer can't be negative."
            raise ValueError(msg)

        # Raise an error if quantity is zero.
        if quantity == 0:
            raise UnnecessaryOperationError

        # Raise an error if quantity is higher than current balance.
        if quantity > self.balance:
            raise InsufficientBalanceError

        # Fetch receiver's account.
        receiver_account = await get_account(receiver_id)

        # Raise an error if receiver's account couldn't be found.
        if not receiver_account:
            raise AccountDoesntExistError

        # Withdraw from sender's account.
        self.balance -= quantity
        await execute(
            f"""
            UPDATE {AccountTable.TABLE_NAME}
            SET {AccountTable.COL_BALANCE} = ?
            WHERE {AccountTable.COL_USER_ID} = ?;
            """,  # noqa: S608
            (self.balance, self.user_id),
        )

        # Deposits to receiver's account.
        receiver_account.balance += quantity
        await execute(
            f"""
            UPDATE {AccountTable.TABLE_NAME}
            SET {AccountTable.COL_BALANCE} = ?
            WHERE {AccountTable.COL_USER_ID} = ?;
            """,  # noqa: S608
            (receiver_account.balance, receiver_account.user_id),
        )

        # Create and return transaction.
        return await Transaction(
            tran_type=Transaction.TYPES.TRANSFER,
            user_id=self.user_id,
            amount=quantity,
            receiver_id=receiver_id,
            reason=reason,
        ).commit()

    async def set_balance(
        self,
        quantity: float,
        reason: str | None = None,
    ) -> Transaction:
        """Set the account's balance.

        Args:
            quantity (float): Balance to be set.
            reason (str | None, optional): Reason of transaction. Defaults to None.

        Raises:
            ValueError: Raise when quantity is negative.
            UnnecessaryOperation: Raise when quantity is zero.

        Returns:
            Transaction: Return transaction.

        """
        # Raise an error if quantity is negative.
        if quantity < 0:
            msg = "The balance number can't be negative."
            raise ValueError(msg)

        # Raise an error if quantity is equal to the current balance.
        if quantity == self.balance:
            raise UnnecessaryOperationError

        # Update user's balance.
        self.balance = quantity
        await execute(
            f"""
            UPDATE {AccountTable.TABLE_NAME}
            SET {AccountTable.COL_BALANCE} = ?
            WHERE {AccountTable.COL_USER_ID} = ?;
            """,  # noqa: S608
            (self.balance, self.user_id),
        )

        # Create and return transaction.
        return await Transaction(
            tran_type=Transaction.TYPES.BALANCESET,
            user_id=self.user_id,
            amount=quantity,
            reason=reason,
        ).commit()

    async def delete(self) -> None:
        """Delete bank account."""
        await execute(
            f"""
            DELETE FROM {AccountTable.TABLE_NAME}
            WHERE {AccountTable.COL_USER_ID} = ?;
            """,  # noqa: S608
            (self.user_id,),
        )


@final
class Check:
    """Represents a bank check."""

    def __init__(
        self,
        *,
        sender_id: int,
        amount: float,
        receiver_id: int,
        reason: str | None = None,
    ) -> None:
        """Initialize a bank check.

        Args:
            sender_id (int): ID of sender.
            amount (float): Amount of check.
            receiver_id (int): ID of receiver.
            reason (str | None, optional): Reason for issuing check. Defaults to None.

        Raises:
            ValueError: Raise if amount is negative.
            UnnecessaryOperation: Raise if amount is zero.

        """
        # Raise an error if amount is negative.
        if amount < 0:
            msg = "The amount can't be negative."
            raise ValueError(msg)

        # Raise an error if amount is zero.
        if amount == 0:
            raise UnnecessaryOperationError

        self.check_id: str | None = str(uuid.uuid4())
        self.sender_id: int = sender_id
        self.amount: float = amount
        self.receiver_id: int = receiver_id
        self.reason: str | None = reason
        self.date: datetime | None = None
        self.deposited: bool = False

    async def issue(self) -> Transaction:
        """Issue bank check.

        Raises:
            AlreadyIssuedCheck: If trying to issue an already issued check.
            AccountDoesntExistError: If the sender bank account can not be fetched.

        Returns:
            Transaction: The transaction.

        """
        # Raise an error if check is already issued.
        if self.date is not None:
            raise AlreadyIssuedCheckError(self)

        # Fetch sender's account.
        sender_account = await get_account(self.sender_id)

        # Raise an error if sender's account couldn't be found.
        if not sender_account:
            raise AccountDoesntExistError

        self.date = datetime.now(timezone.utc)  # Check issue date

        # Withdraw check amount from sender's account and save transaction.
        tran = await sender_account.withdraw(self.amount, reason="Check Issuance.")

        # Save check info in DB.
        await execute(
            f"""
            INSERT INTO {CheckTable.TABLE_NAME} ({CheckTable.columns})
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,  # noqa: S608
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
        """Deposit check into receiver's account.

        Raises:
            AlreadyDepositedCheckError: Raise when trying to deposit an already
                deposited check.
            AccountDoesntExistError: Raise when receiver's bank account can not be
                fetched.

        Returns:
            Transaction: Return transaction.

        """
        # Raise an error if check is already deposited.
        if self.deposited:
            raise AlreadyDepositedCheckError(self)

        # Fetch receiver's account.
        receiver_account = await get_account(self.receiver_id)

        # Raise an error if receiver's account couldn't be found.
        if not receiver_account:
            raise AccountDoesntExistError

        # Deposit check amount to receiver's account and save transaction.
        tran = await receiver_account.deposit(self.amount, reason="Check Deposition.")

        # Update state of check in DB.
        await execute(
            f"""
            UPDATE {CheckTable.TABLE_NAME}
            SET {CheckTable.COL_DEPOSITED} = ?
            WHERE {CheckTable.COL_ID} = ?;
            """,  # noqa: S608
            (1, self.check_id),
        )

        return tran


@final
class Transaction:
    """Represents a bank transaction."""

    class TYPES(Enum):
        """Represents different transaction types."""

        DEPOSIT = "DEPOSIT"
        WITHDRAW = "WITHDRAW"
        TRANSFER = "TRANSFER"
        BALANCESET = "BALANCESET"

        @override
        def __str__(self) -> str:
            return self.value

    def __init__(
        self,
        *,
        tran_type: TYPES,
        user_id: int,
        amount: float,
        receiver_id: int | None = None,
        reason: str | None = None,
    ) -> None:
        """Initialize a bank transaction.

        Args:
            tran_type (TransactionTypes): Type of transaction.
            user_id (int): ID of user.
            amount (float): Amount of operation.
            receiver_id (int | None, optional): ID of receiver if transaction type is to
                transfer. Defaults to None.
            reason (str | None, optional): Reason of transaction. Defaults to None.

        Raises:
            ValueError: Raise when transaction type is to transfer but no receiver ID is
                given.

        """
        # Raise an error if transaction type is to transfer but no receiver ID is given.
        if tran_type.value == Transaction.TYPES.TRANSFER.value and receiver_id is None:
            msg = 'Receiver ID can\'t be empty while transaction type is "Transfer".'
            raise ValueError(
                msg,
            )

        # Raise an error if amount is zero.
        if amount < 0:
            msg = "Amount can not be negative."
            raise ValueError(msg)

        self.date: datetime | None = None
        self.transaction_id: str = str(uuid.uuid4())
        self.type: str = tran_type.value
        self.user_id: int = user_id
        self.amount: float = amount
        self.receiver_id: int | None = receiver_id
        self.reason: str | None = reason

    async def commit(self) -> Transaction:
        """Commit changes and store transaction.

        This method must be called right after creation.

        Returns:
            Transaction: Return transaction.

        """
        # Create transaction and save it in DB.
        self.date = datetime.now(timezone.utc)  # Transaction creation date
        await execute(
            f"""
            INSERT INTO {TransactionTable.TABLE_NAME} ({TransactionTable.columns()})
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,  # noqa: S608
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
    *,
    sender_id: int,
    receiver_id: int,
    quantity: float,
    reason: str | None = None,
) -> Transaction:
    """Transfer balance between bank accounts in an alternative way through sender's ID.

    Args:
        sender_id (int): The ID of the sender.
        receiver_id (int): The ID of the receiver.
        quantity (float): The quantity to transfer.
        reason (str | None, optional): The reason of the transaction. Defaults to None.

    Raises:
        UnnecessaryOperation: Raise when quantity is zero.
        AccountDoesntExistError: Raise when receiver's accound can not be fetched.

    Returns:
        Transaction: Return transaction.

    """
    # Raise an error if quantity is zero.
    if quantity == 0:
        raise UnnecessaryOperationError

    # Fetch sender's account.
    sender_account = await get_account(sender_id)

    # Raise an error if sender's accoung couldn't be found.
    if not sender_account:
        raise AccountDoesntExistError

    # Transfer the money and return transaction.
    return await sender_account.transfer_money_to(receiver_id, quantity, reason)


async def create_account(*, user_id: int, balance: float = 0) -> Account:
    """Create a bank account.

    Args:
        user_id (int): ID of user.
        balance (float, optional): Initial balance that user will start with. Defaults
            to 0.

    Raises:
        AccountExists: Raise when trying to create account for a user who already has
            one.
        ValueError: Raise when balance is negative.

    Returns:
        Account: Return created account.

    """
    # Fetch user's account.
    account = await get_account(user_id)

    # Raise an erro if user already has an account.
    if account is not None:
        raise AccountExistsError

    # Raise an error if balance is negative.
    if balance < 0:
        msg = "Balance can not be negative."
        raise ValueError(msg)

    now = datetime.now(timezone.utc)  # Account creation date
    # Save account in DB.
    await execute(
        f"""
        INSERT INTO {AccountTable.TABLE_NAME} ({AccountTable.columns()})
        VALUES (?, ?, ?, ?, ?);
        """,  # noqa: S608
        (user_id, balance, int(now.timestamp()), None, None),
    )

    account = Account(user_id=user_id, balance=balance)
    account.created_at = now

    return account


async def delete_account(user_id: int) -> None:
    """Delete a bank account.

    Args:
        user_id (int): ID of user.

    Raises:
        AccountDoesntExistError: Raise when trying to delete account a user who already
            has none.

    """
    # Fetch user's account.
    account = await get_account(user_id)

    # Raise an error if user has already no account.
    if account is None:
        raise AccountDoesntExistError

    # Delete account
    await account.delete()


async def get_account(user_id: int) -> Account | None:
    """Fetch a bank account via user's ID.

    Args:
        user_id (int): ID of user.

    Returns:
        Account | None: The fetched account, if the user with given ID has an account.
            `None`, otherwise.

    """
    # tries to fetch the account
    row = await fetchone(
        f"""
        SELECT * FROM {AccountTable.TABLE_NAME}
        WHERE {AccountTable.COL_USER_ID} = ?;
        """,  # noqa: S608
        (user_id,),
    )
    if row is None:
        return None

    # Create an account instance based on the fetched data.
    account = Account(
        user_id=row["user_id"],
        balance=row["balance"],
    )
    account.created_at = datetime.fromtimestamp(row["created_at"], timezone.utc)
    account.last_daily_date = (
        datetime.fromtimestamp(row["last_daily_date"], timezone.utc)
        if row["last_daily_date"]
        else None
    )
    account.last_work_date = (
        datetime.fromtimestamp(row["last_work_date"], timezone.utc)
        if row["last_work_date"]
        else None
    )

    return account


async def get_check(check_id: str) -> Check | None:
    """Fetch a bank check via its ID.

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
        """,  # noqa: S608
        (check_id,),
    )
    if row is None:
        return None

    # Create a check instance based on the fetched data.
    check = Check(
        sender_id=row["sender_id"],
        amount=row["amount"],
        receiver_id=row["receiver_id"],
        reason=row["reason"],
    )
    check.check_id = row["id"]
    check.date = datetime.fromtimestamp(row["date"], timezone.utc)
    check.deposited = row["deposited"] == 1

    return check


async def issue_check(
    *,
    sender_id: int,
    amount: float,
    receiver_id: int,
    reason: str | None = None,
) -> Transaction:
    """Issue a bank check in an alternative way.

    Args:
        sender_id (int): The ID of the sender.
        amount (float): The amount of the check.
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
