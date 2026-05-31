"""This file contains database constants. All table names and columns' names are stored here."""

from typing import final

__all__ = ["AccountTable", "CheckTable", "TransactionTable"]


class _Table:
    @classmethod
    def columns(cls) -> str:
        """Returns a string made of columns' names."""

        return ", ".join(v for i, v in vars(cls).items() if i.startswith("COL"))


@final
class AccountTable(_Table):
    TABLE_NAME = "bank_accounts"

    COL_USER_ID = "user_id"
    COL_BALANCE = "balance"
    COL_CREATED_AT = "created_at"
    COL_LAST_DAILY_DATE = "last_daily_date"
    COL_LAST_WORK_DATE = "last_work_date"


@final
class AnonContactTable(_Table):
    TABLE_NAME = "anon_contacts"

    COL_ID = "id"
    COL_USER_ID = "user_id"
    COL_CONTACT_ID = "contact_id"
    COL_CONTACT_ANON_ID = "contact_anon_id"
    COL_BLOCKED = "blocked"


@final
class AnonSessionTable(_Table):
    TABLE_NAME = "anon_sessions"

    COL_ID = "id"
    COL_SESSION_ID = "session_id"
    COL_RECEIVER_ID = "receiver_id"
    COL_CONTACT_ANON_ID = "contact_anon_id"
    COL_CONTACT_MESSAGE_COLLECTOR_ID = "contact_message_collector_id"
    COL_SESSION_DATE = "session_date"
    COL_RESPONDED = "responded"


@final
class AnonUserTable(_Table):
    TABLE_NAME = "anon_users"

    COL_USER_ID = "user_id"
    COL_PUBLIC_ID = "public_id"
    COL_CREATED_AT = "created_at"


@final
class CheckTable(_Table):
    TABLE_NAME = "bank_checks"

    COL_ID = "id"
    COL_SENDER_ID = "sender_id"
    COL_AMOUNT = "amount"
    COL_RECEIVER_ID = "receiver_id"
    COL_REASON = "reason"
    COL_DATE = "date"
    COL_DEPOSITED = "deposited"


@final
class InventoryTable(_Table):
    TABLE_NAME = "inventory"

    COL_USER_ID = "user_id"
    COL_ITEM_NAME = "item_name"
    COL_QUANTITY = "quantity"


@final
class LotteryTable(_Table):
    TABLE_NAME = "lottery"

    COL_USER_ID = "user_id"
    COL_SIGNED_AT = "signed_at"


@final
class TicketTable(_Table):
    TABLE_NAME = "tickets"

    COL_ID = "id"
    COL_USER_ID = "user_id"
    COL_MESSAGE_COLLECTOR_ID = "message_collector_id"
    COL_SUBJECT = "subject"
    COL_STATE = "state"
    COL_CREATED_AT = "created_at"
    COL_CLOSED_AT = "closed_at"


@final
class TransactionTable(_Table):
    TABLE_NAME = "bank_transactions"

    COL_ID = "id"
    COL_TYPE = "type"
    COL_USER_ID = "user_id"
    COL_AMOUNT = "amount"
    COL_DATE = "date"
    COL_RECEIVER_ID = "receiver_id"
    COL_REASON = "reason"


@final
class WarnTable(_Table):
    TABLE_NAME = "warns"

    COL_ID = "id"
    COL_SERVER_ID = "server_id"
    COL_USER_WARN_ID = "user_warn_id"
    COL_MOD_ID = "mod_id"
    COL_USER_ID = "user_id"
    COL_REASON = "reason"
    COL_TIMESTAMP = "timestamp"
