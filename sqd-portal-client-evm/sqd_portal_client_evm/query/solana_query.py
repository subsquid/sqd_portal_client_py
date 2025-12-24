from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Literal, Optional, Sequence, Tuple

from .base_query import BaseSQDQuery, FieldValue, _freeze_field_map
from .solana.fields import SolanaFields
from .solana.requests import (
    BalancesRequest,
    InstructionsRequest,
    RewardsRequest,
    SolanaLogsRequest,
    SolanaTransactionsRequest,
    TokenBalancesRequest,
)
from ..utils import _request_to_sqd_string


class InstructionField(Enum):
    """Fields available for instruction queries."""
    TRANSACTION_INDEX = FieldValue("instruction", SolanaFields.Instruction.transactionIndex.value)
    INSTRUCTION_ADDRESS = FieldValue("instruction", SolanaFields.Instruction.instructionAddress.value)
    PROGRAM_ID = FieldValue("instruction", SolanaFields.Instruction.programId.value)
    ACCOUNTS = FieldValue("instruction", SolanaFields.Instruction.accounts.value)
    DATA = FieldValue("instruction", SolanaFields.Instruction.data.value)
    D1 = FieldValue("instruction", SolanaFields.Instruction.d1.value)
    D2 = FieldValue("instruction", SolanaFields.Instruction.d2.value)
    D4 = FieldValue("instruction", SolanaFields.Instruction.d4.value)
    D8 = FieldValue("instruction", SolanaFields.Instruction.d8.value)
    ERROR = FieldValue("instruction", SolanaFields.Instruction.error.value)
    COMPUTE_UNITS = FieldValue("instruction", SolanaFields.Instruction.computeUnitsConsumed.value)
    IS_COMMITTED = FieldValue("instruction", SolanaFields.Instruction.isCommitted.value)
    DROPPED_LOG_MESSAGES = FieldValue("instruction", SolanaFields.Instruction.hasDroppedLogMessages.value)


class SolanaTransactionField(Enum):
    """Fields available for Solana transaction queries."""
    TRANSACTION_INDEX = FieldValue("solanaTransaction", SolanaFields.SolanaTransaction.transactionIndex.value)
    VERSION = FieldValue("solanaTransaction", SolanaFields.SolanaTransaction.version.value)
    ACCOUNT_KEYS = FieldValue("solanaTransaction", SolanaFields.SolanaTransaction.accountKeys.value)
    ADDRESS_TABLE_LOOKUPS = FieldValue("solanaTransaction", SolanaFields.SolanaTransaction.addressTableLookups.value)
    NUM_READONLY_SIGNED = FieldValue("solanaTransaction", SolanaFields.SolanaTransaction.numReadonlySignedAccounts.value)
    NUM_READONLY_UNSIGNED = FieldValue("solanaTransaction", SolanaFields.SolanaTransaction.numReadonlyUnsignedAccounts.value)
    NUM_REQUIRED_SIGNATURES = FieldValue("solanaTransaction", SolanaFields.SolanaTransaction.numRequiredSignatures.value)
    RECENT_BLOCKHASH = FieldValue("solanaTransaction", SolanaFields.SolanaTransaction.recentBlockhash.value)
    SIGNATURES = FieldValue("solanaTransaction", SolanaFields.SolanaTransaction.signatures.value)
    ERROR = FieldValue("solanaTransaction", SolanaFields.SolanaTransaction.err.value)
    FEE = FieldValue("solanaTransaction", SolanaFields.SolanaTransaction.fee.value)
    COMPUTE_UNITS = FieldValue("solanaTransaction", SolanaFields.SolanaTransaction.computeUnitsConsumed.value)
    LOADED_ADDRESSES = FieldValue("solanaTransaction", SolanaFields.SolanaTransaction.loadedAddresses.value)
    FEE_PAYER = FieldValue("solanaTransaction", SolanaFields.SolanaTransaction.feePayer.value)
    DROPPED_LOG_MESSAGES = FieldValue("solanaTransaction", SolanaFields.SolanaTransaction.hasDroppedLogMessages.value)


class SolanaLogField(Enum):
    """Fields available for Solana log queries."""
    TRANSACTION_INDEX = FieldValue("solanaLog", SolanaFields.SolanaLog.transactionIndex.value)
    LOG_INDEX = FieldValue("solanaLog", SolanaFields.SolanaLog.logIndex.value)
    INSTRUCTION_ADDRESS = FieldValue("solanaLog", SolanaFields.SolanaLog.instructionAddress.value)
    PROGRAM_ID = FieldValue("solanaLog", SolanaFields.SolanaLog.programId.value)
    KIND = FieldValue("solanaLog", SolanaFields.SolanaLog.kind.value)
    MESSAGE = FieldValue("solanaLog", SolanaFields.SolanaLog.message.value)


class BalanceField(Enum):
    """Fields available for balance queries."""
    TRANSACTION_INDEX = FieldValue("balance", SolanaFields.Balance.transactionIndex.value)
    ACCOUNT = FieldValue("balance", SolanaFields.Balance.account.value)
    PRE = FieldValue("balance", SolanaFields.Balance.pre.value)
    POST = FieldValue("balance", SolanaFields.Balance.post.value)


class TokenBalanceField(Enum):
    """Fields available for token balance queries."""
    TRANSACTION_INDEX = FieldValue("tokenBalance", SolanaFields.TokenBalance.transactionIndex.value)
    ACCOUNT = FieldValue("tokenBalance", SolanaFields.TokenBalance.account.value)
    PRE_PROGRAM_ID = FieldValue("tokenBalance", SolanaFields.TokenBalance.preProgramId.value)
    POST_PROGRAM_ID = FieldValue("tokenBalance", SolanaFields.TokenBalance.postProgramId.value)
    PRE_OWNER = FieldValue("tokenBalance", SolanaFields.TokenBalance.preOwner.value)
    POST_OWNER = FieldValue("tokenBalance", SolanaFields.TokenBalance.postOwner.value)
    PRE_AMOUNT = FieldValue("tokenBalance", SolanaFields.TokenBalance.preAmount.value)
    POST_AMOUNT = FieldValue("tokenBalance", SolanaFields.TokenBalance.postAmount.value)


class RewardField(Enum):
    """Fields available for reward queries."""
    PUBKEY = FieldValue("reward", SolanaFields.Reward.pubKey.value)
    LAMPORTS = FieldValue("reward", SolanaFields.Reward.lamports.value)
    POST_BALANCE = FieldValue("reward", SolanaFields.Reward.postBalance.value)
    REWARD_TYPE = FieldValue("reward", SolanaFields.Reward.rewardType.value)
    COMMISSION = FieldValue("reward", SolanaFields.Reward.commission.value)


class SolanaBlockField(Enum):
    """Fields available for Solana block queries."""
    NUMBER = FieldValue("solanaBlock", SolanaFields.SolanaBlock.number.value)
    HEIGHT = FieldValue("solanaBlock", SolanaFields.SolanaBlock.height.value)
    PARENT_SLOT = FieldValue("solanaBlock", SolanaFields.SolanaBlock.parentSlot.value)
    TIMESTAMP = FieldValue("solanaBlock", SolanaFields.SolanaBlock.timestamp.value)


@dataclass(frozen=True, kw_only=True)
class SolanaQuery(BaseSQDQuery):
    """Immutable Solana query representation.
    
    This class serves as both a query builder and the query itself.
    Use the class methods or SQD() function to create instances.
    
    Example:
        sqd = SQD(dataset='solana-mainnet')
        query = sqd.get_instructions(from_block=200_000_000, program_id='...')
        async for ix in query:
            print(ix)
    """

    _instructions_requests: Tuple[InstructionsRequest, ...] = field(default_factory=tuple)
    _solana_transactions_requests: Tuple[SolanaTransactionsRequest, ...] = field(default_factory=tuple)
    _balances_requests: Tuple[BalancesRequest, ...] = field(default_factory=tuple)
    _token_balances_requests: Tuple[TokenBalancesRequest, ...] = field(default_factory=tuple)
    _rewards_requests: Tuple[RewardsRequest, ...] = field(default_factory=tuple)
    _solana_logs_requests: Tuple[SolanaLogsRequest, ...] = field(default_factory=tuple)

    # ------------------------------------------------------------------ #
    # Factory methods (entry points)
    # ------------------------------------------------------------------ #
    @classmethod
    def create(
        cls,
        *,
        dataset: str,
        portal_url: str = "https://portal.sqd.dev",
        stream_type: Literal["finalized", "realtime"] = "realtime",
    ) -> "SolanaQuery":
        """Create a new Solana query builder with the given configuration."""
        return cls(
            dataset=dataset,
            portal_url=portal_url,
            stream_type=stream_type,
            query_type="solana",
            _fields=_freeze_field_map(cls._default_field_map()),
        )

    def get_instructions(
        self,
        *,
        from_block: int,
        program_id: Optional[str] = None,
        to_block: Optional[int] = None,
        d1: Optional[str] = None,
        d2: Optional[str] = None,
        d4: Optional[str] = None,
        d8: Optional[str] = None,
        include_transaction: bool = False,
        include_inner_instructions: bool = False,
        include_logs: bool = False,
        include_fields: Optional[Sequence[InstructionField]] = None,
    ) -> "SolanaQuery":
        """Query instructions matching the specified criteria."""
        query = self._copy(from_block=from_block, to_block=to_block)
        query = query.add_instructions_request(
            program_id=program_id,
            d1=d1,
            d2=d2,
            d4=d4,
            d8=d8,
            include_transaction=include_transaction,
            include_inner_instructions=include_inner_instructions,
            include_logs=include_logs,
        )
        return query.add_fields(include_fields)

    def get_transactions(
        self,
        *,
        from_block: int,
        account: Optional[str] = None,
        to_block: Optional[int] = None,
        include_instructions: bool = False,
        include_balances: bool = False,
        include_token_balances: bool = False,
        include_logs: bool = False,
        include_fields: Optional[Sequence[SolanaTransactionField]] = None,
    ) -> "SolanaQuery":
        """Query transactions matching the specified criteria."""
        query = self._copy(from_block=from_block, to_block=to_block)
        query = query.add_solana_transactions_request(
            account=account,
            include_instructions=include_instructions,
            include_balances=include_balances,
            include_token_balances=include_token_balances,
            include_logs=include_logs,
        )
        return query.add_fields(include_fields)

    def get_balances(
        self,
        *,
        from_block: int,
        account: Optional[str] = None,
        to_block: Optional[int] = None,
        include_transaction: bool = False,
        include_fields: Optional[Sequence[BalanceField]] = None,
    ) -> "SolanaQuery":
        """Query balance changes matching the specified criteria."""
        query = self._copy(from_block=from_block, to_block=to_block)
        query = query.add_balances_request(
            account=account,
            include_transaction=include_transaction,
        )
        return query.add_fields(include_fields)

    def get_token_balances(
        self,
        *,
        from_block: int,
        account: Optional[str] = None,
        to_block: Optional[int] = None,
        include_transaction: bool = False,
        include_fields: Optional[Sequence[TokenBalanceField]] = None,
    ) -> "SolanaQuery":
        """Query token balance changes matching the specified criteria."""
        query = self._copy(from_block=from_block, to_block=to_block)
        query = query.add_token_balances_request(
            account=account,
            include_transaction=include_transaction,
        )
        return query.add_fields(include_fields)

    def get_rewards(
        self,
        *,
        from_block: int,
        pubkey: Optional[str] = None,
        to_block: Optional[int] = None,
        include_fields: Optional[Sequence[RewardField]] = None,
    ) -> "SolanaQuery":
        """Query rewards matching the specified criteria."""
        query = self._copy(from_block=from_block, to_block=to_block)
        query = query.add_rewards_request(pubkey=pubkey)
        return query.add_fields(include_fields)

    def get_logs(
        self,
        *,
        from_block: int,
        program_id: Optional[str] = None,
        kind: Optional[str] = None,
        to_block: Optional[int] = None,
        include_instruction: bool = False,
        include_transaction: bool = False,
        include_fields: Optional[Sequence[SolanaLogField]] = None,
    ) -> "SolanaQuery":
        """Query logs matching the specified criteria."""
        query = self._copy(from_block=from_block, to_block=to_block)
        query = query.add_solana_logs_request(
            program_id=program_id,
            kind=kind,
            include_instruction=include_instruction,
            include_transaction=include_transaction,
        )
        return query.add_fields(include_fields)

    @staticmethod
    def _default_field_map() -> Dict[str, list[Enum]]:
        return {
            "instruction": [v for v in SolanaFields.Instruction],
            "solanaTransaction": [v for v in SolanaFields.SolanaTransaction],
            "solanaLog": [v for v in SolanaFields.SolanaLog],
            "balance": [v for v in SolanaFields.Balance],
            "tokenBalance": [v for v in SolanaFields.TokenBalance],
            "reward": [v for v in SolanaFields.Reward],
            "solanaBlock": [v for v in SolanaFields.SolanaBlock],
        }

    # ------------------------------------------------------------------ #
    # Request builders (low-level)
    # ------------------------------------------------------------------ #
    def add_instructions_request(
        self,
        *,
        program_id: Optional[str],
        d1: Optional[str],
        d2: Optional[str],
        d4: Optional[str],
        d8: Optional[str],
        include_transaction: bool,
        include_inner_instructions: bool,
        include_logs: bool,
    ) -> "SolanaQuery":
        request = InstructionsRequest(
            programId=[program_id] if program_id else None,
            d1=[d1] if d1 else None,
            d2=[d2] if d2 else None,
            d4=[d4] if d4 else None,
            d8=[d8] if d8 else None,
            transaction=include_transaction,
            innerInstructions=include_inner_instructions,
            logs=include_logs,
        )
        return self._copy(_instructions_requests=self._instructions_requests + (request,))

    def add_solana_transactions_request(
        self,
        *,
        account: Optional[str],
        include_instructions: bool,
        include_balances: bool,
        include_token_balances: bool,
        include_logs: bool,
    ) -> "SolanaQuery":
        request = SolanaTransactionsRequest(
            feePayer=[account] if account else None,
            instructions=include_instructions,
            balances=include_balances,
            tokenBalances=include_token_balances,
            logs=include_logs,
        )
        return self._copy(
            _solana_transactions_requests=self._solana_transactions_requests + (request,)
        )

    def add_balances_request(
        self,
        *,
        account: Optional[str],
        include_transaction: bool,
    ) -> "SolanaQuery":
        request = BalancesRequest(
            account=[account] if account else None,
            transaction=include_transaction,
        )
        return self._copy(_balances_requests=self._balances_requests + (request,))

    def add_token_balances_request(
        self,
        *,
        account: Optional[str],
        include_transaction: bool,
    ) -> "SolanaQuery":
        request = TokenBalancesRequest(
            account=[account] if account else None,
            transaction=include_transaction,
        )
        return self._copy(
            _token_balances_requests=self._token_balances_requests + (request,)
        )

    def add_rewards_request(
        self,
        *,
        pubkey: Optional[str],
    ) -> "SolanaQuery":
        request = RewardsRequest(pubkey=[pubkey] if pubkey else None)
        return self._copy(_rewards_requests=self._rewards_requests + (request,))

    def add_solana_logs_request(
        self,
        *,
        program_id: Optional[str],
        kind: Optional[str],
        include_instruction: bool,
        include_transaction: bool,
    ) -> "SolanaQuery":
        request = SolanaLogsRequest(
            programId=[program_id] if program_id else None,
            kind=[kind] if kind else None,
            instruction=include_instruction,
            transaction=include_transaction,
        )
        return self._copy(
            _solana_logs_requests=self._solana_logs_requests + (request,)
        )

    # ------------------------------------------------------------------ #
    # Payload hooks
    # ------------------------------------------------------------------ #
    def _chain_payload(self) -> Dict[str, object]:
        payload: Dict[str, object] = {}
        if self._instructions_requests:
            payload["instructions"] = [
                _request_to_sqd_string(request) for request in self._instructions_requests
            ]

        if self._solana_transactions_requests:
            payload["transactions"] = [
                _request_to_sqd_string(request)
                for request in self._solana_transactions_requests
            ]

        if self._balances_requests:
            payload["balances"] = [
                _request_to_sqd_string(request) for request in self._balances_requests
            ]

        if self._token_balances_requests:
            payload["tokenBalances"] = [
                _request_to_sqd_string(request)
                for request in self._token_balances_requests
            ]

        if self._rewards_requests:
            payload["rewards"] = [
                _request_to_sqd_string(request) for request in self._rewards_requests
            ]

        if self._solana_logs_requests:
            payload["logs"] = [
                _request_to_sqd_string(request) for request in self._solana_logs_requests
            ]

        return payload


__all__ = [
    "SolanaQuery",
    "InstructionField",
    "SolanaTransactionField",
    "SolanaLogField",
    "BalanceField",
    "TokenBalanceField",
    "RewardField",
    "SolanaBlockField",
]
