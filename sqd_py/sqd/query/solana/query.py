from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

from sqd.query.base_query import BaseSQDQuery
from sqd.query.solana.fields import (
    BalanceField,
    InstructionField,
    RewardField,
    SolanaBlockField,
    SolanaLogField,
    SolanaTransactionField,
    TokenBalanceField,
)
from sqd.query.solana.requests import (
    BalancesRequest,
    InstructionsRequest,
    RewardsRequest,
    SolanaLogsRequest,
    SolanaTransactionsRequest,
    TokenBalancesRequest,
)
from sqd.utils import _request_to_sqd_string

# ============================================================================ #
# SolanaQuery
# ============================================================================ #


@dataclass(frozen=True, kw_only=True)
class SolanaQuery(BaseSQDQuery):
    """Immutable Solana query representation.

    Example:
        sqd = SQD(dataset='solana-mainnet')
        query = sqd.get_instructions(from_block=200_000_000, program_id='...')
        async for ix in query:
            print(ix)
    """

    _instructions_requests: tuple[InstructionsRequest, ...] = field(
        default_factory=tuple
    )
    _solana_transactions_requests: tuple[SolanaTransactionsRequest, ...] = field(
        default_factory=tuple
    )
    _balances_requests: tuple[BalancesRequest, ...] = field(default_factory=tuple)
    _token_balances_requests: tuple[TokenBalancesRequest, ...] = field(
        default_factory=tuple
    )
    _rewards_requests: tuple[RewardsRequest, ...] = field(default_factory=tuple)
    _solana_logs_requests: tuple[SolanaLogsRequest, ...] = field(default_factory=tuple)

    # ------------------------------------------------------------------ #
    # Factory methods
    # ------------------------------------------------------------------ #
    @classmethod
    def create(
        cls,
        *,
        dataset: str,
        portal_url: str = "https://portal.sqd.dev",
        stream_type: Literal["finalized", "realtime"] = "realtime",
    ) -> "SolanaQuery":
        """Create a new Solana query builder."""
        return cls(
            dataset=dataset,
            portal_url=portal_url,
            stream_type=stream_type,
            query_type="solana",
        )

    def get_instructions(
        self,
        *,
        from_block: int,
        program_id: str | None = None,
        to_block: int | None = None,
        d1: str | None = None,
        d2: str | None = None,
        d4: str | None = None,
        d8: str | None = None,
        include_transaction: bool = False,
        include_inner_instructions: bool = False,
        include_logs: bool = False,
        include_fields: Sequence[InstructionField] | None = None,
    ) -> "SolanaQuery":
        """Query instructions matching the specified criteria."""
        query = self.copy(from_block=from_block, to_block=to_block)
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
        return query.add_fields("instruction", include_fields)

    def get_transactions(
        self,
        *,
        from_block: int,
        account: str | None = None,
        to_block: int | None = None,
        include_instructions: bool = False,
        include_balances: bool = False,
        include_token_balances: bool = False,
        include_logs: bool = False,
        include_fields: Sequence[SolanaTransactionField] | None = None,
    ) -> "SolanaQuery":
        """Query transactions matching the specified criteria."""
        query = self.copy(from_block=from_block, to_block=to_block)
        query = query.add_solana_transactions_request(
            account=account,
            include_instructions=include_instructions,
            include_balances=include_balances,
            include_token_balances=include_token_balances,
            include_logs=include_logs,
        )
        return query.add_fields("solanaTransaction", include_fields)

    def get_balances(
        self,
        *,
        from_block: int,
        account: str | None = None,
        to_block: int | None = None,
        include_transaction: bool = False,
        include_fields: Sequence[BalanceField] | None = None,
    ) -> "SolanaQuery":
        """Query balance changes."""
        query = self.copy(from_block=from_block, to_block=to_block)
        query = query.add_balances_request(
            account=account, include_transaction=include_transaction
        )
        return query.add_fields("balance", include_fields)

    def get_token_balances(
        self,
        *,
        from_block: int,
        account: str | None = None,
        to_block: int | None = None,
        include_transaction: bool = False,
        include_fields: Sequence[TokenBalanceField] | None = None,
    ) -> "SolanaQuery":
        """Query token balance changes."""
        query = self.copy(from_block=from_block, to_block=to_block)
        query = query.add_token_balances_request(
            account=account, include_transaction=include_transaction
        )
        return query.add_fields("tokenBalance", include_fields)

    def get_rewards(
        self,
        *,
        from_block: int,
        pubkey: str | None = None,
        to_block: int | None = None,
        include_fields: Sequence[RewardField] | None = None,
    ) -> "SolanaQuery":
        """Query rewards."""
        query = self.copy(from_block=from_block, to_block=to_block)
        query = query.add_rewards_request(pubkey=pubkey)
        return query.add_fields("reward", include_fields)

    def get_logs(
        self,
        *,
        from_block: int,
        program_id: str | None = None,
        kind: str | None = None,
        to_block: int | None = None,
        include_instruction: bool = False,
        include_transaction: bool = False,
        include_fields: Sequence[SolanaLogField] | None = None,
    ) -> "SolanaQuery":
        """Query logs."""
        query = self.copy(from_block=from_block, to_block=to_block)
        query = query.add_solana_logs_request(
            program_id=program_id,
            kind=kind,
            include_instruction=include_instruction,
            include_transaction=include_transaction,
        )
        return query.add_fields("solanaLog", include_fields)

    @staticmethod
    def _default_field_map() -> dict[str, list[str]]:
        return {
            "instruction": list(InstructionField),
            "solanaTransaction": list(SolanaTransactionField),
            "solanaLog": list(SolanaLogField),
            "balance": list(BalanceField),
            "tokenBalance": list(TokenBalanceField),
            "reward": list(RewardField),
            "solanaBlock": list(SolanaBlockField),
        }

    # ------------------------------------------------------------------ #
    # Request builders (low-level)
    # ------------------------------------------------------------------ #
    def add_instructions_request(
        self,
        *,
        program_id: str | None,
        d1: str | None,
        d2: str | None,
        d4: str | None,
        d8: str | None,
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
        return self.copy(
            _instructions_requests=self._instructions_requests + (request,)
        )

    def add_solana_transactions_request(
        self,
        *,
        account: str | None,
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
        return self.copy(
            _solana_transactions_requests=self._solana_transactions_requests
            + (request,)
        )

    def add_balances_request(
        self, *, account: str | None, include_transaction: bool
    ) -> "SolanaQuery":
        request = BalancesRequest(
            account=[account] if account else None, transaction=include_transaction
        )
        return self.copy(_balances_requests=self._balances_requests + (request,))

    def add_token_balances_request(
        self, *, account: str | None, include_transaction: bool
    ) -> "SolanaQuery":
        request = TokenBalancesRequest(
            account=[account] if account else None, transaction=include_transaction
        )
        return self.copy(
            _token_balances_requests=self._token_balances_requests + (request,)
        )

    def add_rewards_request(self, *, pubkey: str | None) -> "SolanaQuery":
        request = RewardsRequest(pubkey=[pubkey] if pubkey else None)
        return self.copy(_rewards_requests=self._rewards_requests + (request,))

    def add_solana_logs_request(
        self,
        *,
        program_id: str | None,
        kind: str | None,
        include_instruction: bool,
        include_transaction: bool,
    ) -> "SolanaQuery":
        request = SolanaLogsRequest(
            programId=[program_id] if program_id else None,
            kind=[kind] if kind else None,
            instruction=include_instruction,
            transaction=include_transaction,
        )
        return self.copy(_solana_logs_requests=self._solana_logs_requests + (request,))

    # ------------------------------------------------------------------ #
    # Payload hooks
    # ------------------------------------------------------------------ #
    def _chain_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        if self._instructions_requests:
            payload["instructions"] = [
                _request_to_sqd_string(r) for r in self._instructions_requests
            ]
        if self._solana_transactions_requests:
            payload["transactions"] = [
                _request_to_sqd_string(r) for r in self._solana_transactions_requests
            ]
        if self._balances_requests:
            payload["balances"] = [
                _request_to_sqd_string(r) for r in self._balances_requests
            ]
        if self._token_balances_requests:
            payload["tokenBalances"] = [
                _request_to_sqd_string(r) for r in self._token_balances_requests
            ]
        if self._rewards_requests:
            payload["rewards"] = [
                _request_to_sqd_string(r) for r in self._rewards_requests
            ]
        if self._solana_logs_requests:
            payload["logs"] = [
                _request_to_sqd_string(r) for r in self._solana_logs_requests
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
