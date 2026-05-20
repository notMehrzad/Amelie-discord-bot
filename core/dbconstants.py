"""This file contains database constants. All table names and columns' names are stored here."""


class _Table:
    @classmethod
    def columns(cls) -> str:
        """Returns a string made of columns' names."""

        return ", ".join(v for i, v in vars(cls).items() if i.startswith("COL"))


class AccountTable(_Table):
    TABLE_NAME = "bank_accounts"

    COL_USER_ID = "user_id"
    COL_BALANCE = "balance"
    COL_CREATED_AT = "created_at"
    COL_LAST_DAILY_DATE = "last_daily_date"
    COL_LAST_WORK_DATE = "last_work_date"


class CheckTable(_Table):
    TABLE_NAME = "bank_checks"

    COL_ID = "id"
    COL_SENDER_ID = "sender_id"
    COL_AMOUNT = "amount"
    COL_RECEIVER_ID = "receiver_id"
    COL_REASON = "reason"
    COL_DATE = "date"
    COL_DEPOSITED = "deposited"


class TransactionTable(_Table):
    TABLE_NAME = "bank_transactions"

    COL_ID = "id"
    COL_TYPE = "type"
    COL_USER_ID = "user_id"
    COL_AMOUNT = "amount"
    COL_DATE = "date"
    COL_RECEIVER_ID = "receiver_id"
    COL_REASON = "reason"
