from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence, Tuple

from ..base.base import _Fields
from .base_query import BaseSQDQuery, _FieldEnum, _freeze_field_map
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


class InstructionField(_FieldEnum):
    TRANSACTION_INDEX = ("instruction", SolanaFields.Instruction.transactionIndex.value)
    INSTRUCTION_ADDRESS = (
        "instruction",
        SolanaFields.Instruction.instructionAddress.value,
    )
    PROGRAM_ID = ("instruction", SolanaFields.Instruction.programId.value)
    ACCOUNTS = ("instruction", SolanaFields.Instruction.accounts.value)
    DATA = ("instruction", SolanaFields.Instruction.data.value)
    D1 = ("instruction", SolanaFields.Instruction.d1.value)
    D2 = ("instruction", SolanaFields.Instruction.d2.value)
    D4 = ("instruction", SolanaFields.Instruction.d4.value)
    D8 = ("instruction", SolanaFields.Instruction.d8.value)
    ERROR = ("instruction", SolanaFields.Instruction.error.value)
    COMPUTE_UNITS = (
        "instruction",
        SolanaFields.Instruction.computeUnitsConsumed.value,
    )
    IS_COMMITTED = ("instruction", SolanaFields.Instruction.isCommitted.value)
    DROPPED_LOG_MESSAGES = (
        "instruction",
        SolanaFields.Instruction.hasDroppedLogMessages.value,
    )


class SolanaTransactionField(_FieldEnum):
    TRANSACTION_INDEX = (
        "solanaTransaction",
        SolanaFields.SolanaTransaction.transactionIndex.value,
    )
    VERSION = ("solanaTransaction", SolanaFields.SolanaTransaction.version.value)
    ACCOUNT_KEYS = (
        "solanaTransaction",
        SolanaFields.SolanaTransaction.accountKeys.value,
    )
    ADDRESS_TABLE_LOOKUPS = (
        "solanaTransaction",
        SolanaFields.SolanaTransaction.addressTableLookups.value,
    )
    NUM_READONLY_SIGNED = (
        "solanaTransaction",
        SolanaFields.SolanaTransaction.numReadonlySignedAccounts.value,
    )
    NUM_READONLY_UNSIGNED = (
        "solanaTransaction",
        SolanaFields.SolanaTransaction.numReadonlyUnsignedAccounts.value,
    )
    NUM_REQUIRED_SIGNATURES = (
        "solanaTransaction",
        SolanaFields.SolanaTransaction.numRequiredSignatures.value,
    )
    RECENT_BLOCKHASH = (
        "solanaTransaction",
        SolanaFields.SolanaTransaction.recentBlockhash.value,
    )
    SIGNATURES = ("solanaTransaction", SolanaFields.SolanaTransaction.signatures.value)
    ERROR = ("solanaTransaction", SolanaFields.SolanaTransaction.err.value)
    FEE = ("solanaTransaction", SolanaFields.SolanaTransaction.fee.value)
    COMPUTE_UNITS = (
        "solanaTransaction",
        SolanaFields.SolanaTransaction.computeUnitsConsumed.value,
    )
    LOADED_ADDRESSES = (
        "solanaTransaction",
        SolanaFields.SolanaTransaction.loadedAddresses.value,
    )
    FEE_PAYER = ("solanaTransaction", SolanaFields.SolanaTransaction.feePayer.value)
    DROPPED_LOG_MESSAGES = (
        "solanaTransaction",
        SolanaFields.SolanaTransaction.hasDroppedLogMessages.value,
    )


class SolanaLogField(_FieldEnum):
    TRANSACTION_INDEX = (
        "solanaLog",
        SolanaFields.SolanaLog.transactionIndex.value,
    )
    LOG_INDEX = ("solanaLog", SolanaFields.SolanaLog.logIndex.value)
    INSTRUCTION_ADDRESS = (
        "solanaLog",
        SolanaFields.SolanaLog.instructionAddress.value,
    )
    PROGRAM_ID = ("solanaLog", SolanaFields.SolanaLog.programId.value)
    KIND = ("solanaLog", SolanaFields.SolanaLog.kind.value)
    MESSAGE = ("solanaLog", SolanaFields.SolanaLog.message.value)


class BalanceField(_FieldEnum):
    TRANSACTION_INDEX = ("balance", SolanaFields.Balance.transactionIndex.value)
    ACCOUNT = ("balance", SolanaFields.Balance.account.value)
    PRE = ("balance", SolanaFields.Balance.pre.value)
    POST = ("balance", SolanaFields.Balance.post.value)


class TokenBalanceField(_FieldEnum):
    TRANSACTION_INDEX = (
        "tokenBalance",
        SolanaFields.TokenBalance.transactionIndex.value,
    )
    ACCOUNT = ("tokenBalance", SolanaFields.TokenBalance.account.value)
    PRE_PROGRAM_ID = ("tokenBalance", SolanaFields.TokenBalance.preProgramId.value)
    POST_PROGRAM_ID = ("tokenBalance", SolanaFields.TokenBalance.postProgramId.value)
    PRE_OWNER = ("tokenBalance", SolanaFields.TokenBalance.preOwner.value)
    POST_OWNER = ("tokenBalance", SolanaFields.TokenBalance.postOwner.value)
    PRE_AMOUNT = ("tokenBalance", SolanaFields.TokenBalance.preAmount.value)
    POST_AMOUNT = ("tokenBalance", SolanaFields.TokenBalance.postAmount.value)


class RewardField(_FieldEnum):
    PUBKEY = ("reward", SolanaFields.Reward.pubKey.value)
    LAMPORTS = ("reward", SolanaFields.Reward.lamports.value)
    POST_BALANCE = ("reward", SolanaFields.Reward.postBalance.value)
    REWARD_TYPE = ("reward", SolanaFields.Reward.rewardType.value)
    COMMISSION = ("reward", SolanaFields.Reward.commission.value)


class SolanaBlockField(_FieldEnum):
    NUMBER = ("solanaBlock", SolanaFields.SolanaBlock.number.value)
    HEIGHT = ("solanaBlock", SolanaFields.SolanaBlock.height.value)
    PARENT_SLOT = ("solanaBlock", SolanaFields.SolanaBlock.parentSlot.value)
    TIMESTAMP = ("solanaBlock", SolanaFields.SolanaBlock.timestamp.value)


@dataclass(frozen=True, kw_only=True)
class SolanaQuery(BaseSQDQuery):
    """Immutable Solana query representation."""

    _instructions_requests: Tuple[InstructionsRequest, ...] = field(
        default_factory=tuple
    )
    _solana_transactions_requests: Tuple[SolanaTransactionsRequest, ...] = field(
        default_factory=tuple
    )
    _balances_requests: Tuple[BalancesRequest, ...] = field(default_factory=tuple)
    _token_balances_requests: Tuple[TokenBalancesRequest, ...] = field(
        default_factory=tuple
    )
    _rewards_requests: Tuple[RewardsRequest, ...] = field(default_factory=tuple)
    _solana_logs_requests: Tuple[SolanaLogsRequest, ...] = field(
        default_factory=tuple
    )

    @classmethod
    def create(
        cls, *, client, from_block: int, to_block: Optional[int]
    ) -> "SolanaQuery":
        return cls(
            client=client,
            from_block=from_block,
            to_block=to_block,
            query_type="solana",
            _fields=_freeze_field_map(cls._default_field_map()),
        )

    @staticmethod
    def _default_field_map() -> Dict[str, Sequence[_FieldEnum]]:
        all_fields = _Fields.all_fields()
        return {
            "instruction": all_fields.instruction,
            "solanaTransaction": all_fields.solanaTransaction,
            "solanaLog": all_fields.solanaLog,
            "balance": all_fields.balance,
            "tokenBalance": all_fields.tokenBalance,
            "reward": all_fields.reward,
            "solanaBlock": all_fields.solanaBlock,
        }

    # ------------------------------------------------------------------ #
    # Request builders
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
