from __future__ import annotations

from typing import Literal, Optional, Sequence

from ..dataset import Dataset
from .factory import BaseQueryFactory
from .solana_query import (
    BalanceField,
    InstructionField,
    RewardField,
    SolanaLogField,
    SolanaQuery,
    SolanaTransactionField,
    TokenBalanceField,
)  # not adjusting


class SolanaQueryFactory(BaseQueryFactory):
    """Build Solana queries for a given SQD client."""

    def __init__(
        self,
        *,
        dataset: Dataset,
        portal_url: str,
        stream_type: Literal["finalized", "realtime"],
    ) -> None:
        super().__init__(
            dataset=dataset, portal_url=portal_url, stream_type=stream_type
        )

    def get_instructions(
        self,
        *,
        program_id: Optional[str] = None,
        from_block: int,
        to_block: Optional[int] = None,
        d1: Optional[str] = None,
        d2: Optional[str] = None,
        d4: Optional[str] = None,
        d8: Optional[str] = None,
        include_transaction: bool = False,
        include_inner_instructions: bool = False,
        include_logs: bool = False,
        include_fields: Optional[Sequence[InstructionField]] = None,
    ) -> SolanaQuery:
        query = SolanaQuery.create(
            client=self,
            from_block=from_block,
            to_block=to_block,
        )
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
        account: Optional[str] = None,
        from_block: int,
        to_block: Optional[int] = None,
        include_instructions: bool = False,
        include_balances: bool = False,
        include_token_balances: bool = False,
        include_logs: bool = False,
        include_fields: Optional[Sequence[SolanaTransactionField]] = None,
    ) -> SolanaQuery:
        query = SolanaQuery.create(
            client=self,
            from_block=from_block,
            to_block=to_block,
        )
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
        account: Optional[str] = None,
        from_block: int,
        to_block: Optional[int] = None,
        include_transaction: bool = False,
        include_fields: Optional[Sequence[BalanceField]] = None,
    ) -> SolanaQuery:
        query = SolanaQuery.create(
            client=self,
            from_block=from_block,
            to_block=to_block,
        )
        query = query.add_balances_request(
            account=account,
            include_transaction=include_transaction,
        )
        return query.add_fields(include_fields)

    def get_token_balances(
        self,
        *,
        account: Optional[str] = None,
        from_block: int,
        to_block: Optional[int] = None,
        include_transaction: bool = False,
        include_fields: Optional[Sequence[TokenBalanceField]] = None,
    ) -> SolanaQuery:
        query = SolanaQuery.create(
            client=self,
            from_block=from_block,
            to_block=to_block,
        )
        query = query.add_token_balances_request(
            account=account,
            include_transaction=include_transaction,
        )
        return query.add_fields(include_fields)

    def get_rewards(
        self,
        *,
        pubkey: Optional[str] = None,
        from_block: int,
        to_block: Optional[int] = None,
        include_fields: Optional[Sequence[RewardField]] = None,
    ) -> SolanaQuery:
        query = SolanaQuery.create(
            client=self,
            from_block=from_block,
            to_block=to_block,
        )
        query = query.add_rewards_request(pubkey=pubkey)
        return query.add_fields(include_fields)

    def get_logs(
        self,
        *,
        program_id: Optional[str] = None,
        kind: Optional[str] = None,
        from_block: int,
        to_block: Optional[int] = None,
        include_instruction: bool = False,
        include_transaction: bool = False,
        include_fields: Optional[Sequence[SolanaLogField]] = None,
    ) -> SolanaQuery:
        query = SolanaQuery.create(
            client=self,
            from_block=from_block,
            to_block=to_block,
        )
        query = query.add_solana_logs_request(
            program_id=program_id,
            kind=kind,
            include_instruction=include_instruction,
            include_transaction=include_transaction,
        )
        return query.add_fields(include_fields)


__all__ = ["SolanaQueryFactory"]
