"""
Solana Query Builder for SQD Portal Client

This module provides Solana-specific query functionality for the SQD (Subsquid) Network portal.
"""

try:
    import ujson as json_lib
except ImportError:
    import json as json_lib

from dataclasses import dataclass, field
from typing import Optional

from sqd_portal_client_evm.utils import _request_to_sqd_string
from sqd_portal_client_evm.query.solana.fields import SolanaFields
from .requests import (
    InstructionsRequest,
    SolanaTransactionsRequest,
    BalancesRequest,
    TokenBalancesRequest,
    RewardsRequest,
    SolanaLogsRequest,
)
from ...base.base import _Fields


@dataclass(frozen=True, kw_only=True)
class SolanaQueryBuilder:
    """
    Builder class for Solana queries with convenient method chaining.
    """
    from_block: int = 0
    to_block: Optional[int] = None
    instructions_requests: list[InstructionsRequest] = field(default_factory=list)
    solana_transactions_requests: list[SolanaTransactionsRequest] = field(
        default_factory=list
    )
    balances_requests: list[BalancesRequest] = field(default_factory=list)
    token_balances_requests: list[TokenBalancesRequest] = field(default_factory=list)
    rewards_requests: list[RewardsRequest] = field(default_factory=list)
    solana_logs_requests: list[SolanaLogsRequest] = field(default_factory=list)
    fields: Optional[_Fields] = None
    type: str = field(default='solana')
    
    @classmethod
    def get_instructions(
            cls,
            program_id: Optional[str] = None,
            from_block: int = 0,
            to_block: Optional[int] = None,
            d1: Optional[str] = None,
            d2: Optional[str] = None,
            d4: Optional[str] = None,
            d8: Optional[str] = None,
            include_transaction: bool = False,
            include_inner_instructions: bool = False,
            include_logs: bool = False,
            fields: Optional[SolanaFields] = None,
    ) -> SolanaQueryBuilder:
        """
        Create a Solana instructions query.

        Args:
            program_id: Filter by program ID
            from_block: Starting slot number
            to_block: Ending slot number (optional)
            d1, d2, d4, d8: Byte discriminators for instruction data
            include_transaction: Include parent transaction
            include_inner_instructions: Include inner instructions
            include_logs: Include logs produced by instructions
            fields: Fields to include (default: minimal fields)

        Example:
            query = Query.solana().get_instructions(program_id='11111111111111111111111111111112', from_block=200000000)
        """
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

        return cls(
            from_block=from_block,
            to_block=to_block,
            instructions_requests=[request],
            fields=fields or SolanaFields.minimal_fields(),
            type="solana",
        )

    @classmethod
    def get_transactions(
            cls,
            account: Optional[str] = None,
            from_block: int = 0,
            to_block: Optional[int] = None,
            include_instructions: bool = False,
            include_balances: bool = False,
            include_token_balances: bool = False,
            include_logs: bool = False,
            fields: Optional[SolanaFields] = None,
    ) -> SolanaQueryBuilder:
        """
        Create a Solana transactions query.

        Args:
            account: Filter by account address
            from_block: Starting slot number
            to_block: Ending slot number (optional)
            include_instructions: Include instructions executed by the transaction
            include_balances: Include SOL balance updates
            include_token_balances: Include token balance updates
            include_logs: Include logs produced by the transaction
            fields: Fields to include (default: minimal fields)

        Example:
            query = Query.solana().get_transactions(account='address...', from_block=200000000)
        """
        request = SolanaTransactionsRequest(
            feePayer=[account] if account else None,
            instructions=include_instructions,
            balances=include_balances,
            tokenBalances=include_token_balances,
            logs=include_logs,
        )

        # Import here to avoid circular imports

        return cls(
            from_block=from_block,
            to_block=to_block,
            solana_transactions_requests=[request],
            fields=fields or SolanaFields.minimal_fields(),
        )

    @classmethod
    def get_balances(
            cls,
            account: Optional[str] = None,
            from_block: int = 0,
            to_block: Optional[int] = None,
            include_transaction: bool = False,
            fields: Optional[SolanaFields] = None,
    ) -> SolanaQueryBuilder:
        """
        Create a Solana balances query.

        Args:
            account: Filter by account address
            from_block: Starting slot number
            to_block: Ending slot number (optional)
            include_transaction: Include parent transaction
            fields: Fields to include (default: minimal fields)

        Example:
            query = Query.solana().get_balances(account='address...', from_block=200000000)
        """
        request = BalancesRequest(
            account=[account] if account else None, transaction=include_transaction
        )

        return cls(
            from_block=from_block,
            to_block=to_block,
            balances_requests=[request],
            fields=fields or SolanaFields.minimal_fields(),
            type="solana",
        )

    def get_token_balances(
            self,
            account: Optional[str] = None,
            from_block: int = 0,
            to_block: Optional[int] = None,
            include_transaction: bool = False,
            fields: Optional[SolanaFields] = None,
    ) -> SolanaQueryBuilder:
        """
        Create a Solana token balances query.

        Args:
            account: Filter by token account address
            from_block: Starting slot number
            to_block: Ending slot number (optional)
            include_transaction: Include parent transaction
            fields: Fields to include (default: minimal fields)

        Example:
            query = Query.solana().get_token_balances(account='address...', from_block=200000000)
        """
        request = TokenBalancesRequest(
            account=[account] if account else None, transaction=include_transaction
        )

        # Import here to avoid circular imports
        from ..query import SolanaQueryBuilder, _Fields

        return SolanaQueryBuilder(
            from_block=from_block,
            to_block=to_block,
            tokenBalancesRequests=[request],
            fields=fields or _Fields.minimal_fields(),
            type="solana",
        )

    def get_rewards(
            self,
            pubkey: Optional[str] = None,
            from_block: int = 0,
            to_block: Optional[int] = None,
            fields: Optional[SolanaFields] = None,
    ) -> SolanaQueryBuilder:
        """
        Create a Solana rewards query.

        Args:
            pubkey: Filter by public key that received rewards
            from_block: Starting slot number
            to_block: Ending slot number (optional)
            fields: Fields to include (default: minimal fields)

        Example:
            query = Query.solana().get_rewards(pubkey='address...', from_block=200000000)
        """
        request = RewardsRequest(pubkey=[pubkey] if pubkey else None)

        # Import here to avoid circular imports
        from ..query import SolanaQueryBuilder, _Fields

        return SolanaQueryBuilder(
            from_block=from_block,
            to_block=to_block,
            rewardsRequests=[request],
            fields=fields or _Fields.minimal_fields(),
            type="solana",
        )

    def get_logs(
            self,
            program_id: Optional[str] = None,
            kind: Optional[str] = None,
            from_block: int = 0,
            to_block: Optional[int] = None,
            include_transaction: bool = False,
            fields: Optional[SolanaFields] = None,
    ) -> SolanaQueryBuilder:
        """
        Create a Solana logs query.

        Args:
            program_id: Filter by program ID that produced the logs
            kind: Filter by log kind ('log', 'data', 'other')
            from_block: Starting slot number
            to_block: Ending slot number (optional)
            include_transaction: Include parent transaction
            fields: Fields to include (default: minimal fields)

        Example:
            query = Query.solana().get_logs(program_id='address...', from_block=200000000)
        """
        request = SolanaLogsRequest(
            programId=[program_id] if program_id else None,
            kind=[kind] if kind else None,
            transaction=include_transaction,
        )

        # Import here to avoid circular imports
        from ..query import SolanaQueryBuilder, _Fields

        return SolanaQueryBuilder(
            from_block=from_block,
            to_block=to_block,
            solanaLogsRequests=[request],
            fields=fields or _Fields.minimal_fields(),
            type="solana",
        )

    def to_sqd_string(self):
        """Convert query builder to SQD API string format"""
        # Build the complete query structure
        query_dict = {
            "type": self.type,
            "fromBlock": self.from_block,
        }

        if self.to_block is not None:
            query_dict["toBlock"] = self.to_block

        if self.fields is not None:
            if hasattr(self.fields, 'to_sqd_string'):
                # Parse the JSON string back to dict for consistency
                query_dict["fields"] = json_lib.loads(self.fields.to_sqd_string())
            else:
                # Fallback for other field formats
                query_dict["fields"] = self.fields

        # Add requests if any exist
        requests_dict = {}

        if self.instructions_requests:
            requests_dict["instructions"] = [
                r.to_sqd_string() for r in self.instructions_requests
            ]

        if self.solana_transactions_requests:
            requests_dict["transactions"] = [
                r.to_sqd_string() for r in self.solana_transactions_requests
            ]

        if self.balances_requests:
            requests_dict["balances"] = [
                _request_to_sqd_string(r) for r in self.balances_requests
            ]

        if self.token_balances_requests:
            requests_dict["tokenBalances"] = [
                _request_to_sqd_string(r) for r in self.token_balances_requests
            ]

        if self.rewards_requests:
            requests_dict["rewards"] = [
                _request_to_sqd_string(r) for r in self.rewards_requests
            ]

        if self.solana_logs_requests:
            requests_dict["logs"] = [
                _request_to_sqd_string(r) for r in self.solana_logs_requests
            ]

        if requests_dict:
            query_dict["requests"] = requests_dict

        return json_lib.dumps(query_dict, separators=(",", ":"))
