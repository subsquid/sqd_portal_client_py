from dataclasses import field, dataclass
from typing import Literal

# Import field enums for backward compatibility - these will be set after module loading
EVMFields = None
SolanaFields = None


def _initialize_field_enums():
    """Initialize field enums after all modules are loaded."""
    global EVMFields, SolanaFields
    try:
        from ..query.evm.fields import EVMFields as EVMFields_import
        from ..query.solana.fields import SolanaFields as SolanaFields_import
        EVMFields = EVMFields_import
        SolanaFields = SolanaFields_import
    except ImportError:
        pass  # Keep as None if imports fail


@dataclass(frozen=True, kw_only=True)
class _Query:
    """
    Internal query dataclass for SQD Network portal queries.

    This class is used internally by the query builders and should not be used directly.
    Use Query.evm and Query.solana builders instead for programmatic query building.
    """


    # Solana-specific request lists

    fields: "_Fields" = field(default_factory=lambda: _Fields.minimal_fields())
    type: Literal["evm", "solana"] = "evm"

    def __post_init__(self):
        """Validate query parameters after initialization."""
        if self.from_block < 0:
            raise ValueError(f"from_block must be non-negative, got {self.from_block}")

        if self.to_block is not None and self.to_block < self.from_block:
            raise ValueError(
                f"to_block ({self.to_block}) must be greater than or equal to from_block ({self.from_block})"
            )



        to_blockString = "" if self.to_block is None else f'"to_block":{self.to_block}'

        # Build the middle part with proper comma handling
        middleParts = []
        if to_blockString:
            middleParts.append(to_blockString)
        if requestsString:
            middleParts.append(requestsString)

        middleString = ",".join(middleParts)

        # Filter fields based on query type
        fields_dict = {}
        for k, v in asdict(self.fields).items():
            if len(v) > 0:
                if k in ["block", "transaction", "log", "stateDiff", "trace"]:
                    # EVM fields - include for both EVM and Solana queries for compatibility
                    fields_dict[k] = {f.value: True for f in v}
                elif k in [
                    "instruction",
                    "solanaTransaction",
                    "solanaLog",
                    "balance",
                    "tokenBalance",
                    "reward",
                    "solanaBlock",
                ]:
                    # Solana fields - only include for Solana queries
                    if self.type == "solana":
                        fields_dict[k] = {f.value: True for f in v}

        fields_string = json_lib.dumps(fields_dict, separators=(",", ":"))

        return f'{{"type":"{self.type}","from_block":{self.from_block},{middleString},"fields":{fields_string}}}'


@dataclass(frozen=True, kw_only=True)
class _Fields:
    """
    Defines which fields to include in query results for different data types.
    """

    # EVM fields using the imported enums
    block: set[EVMFields.Block] = field(default_factory=set)
    transaction: set[EVMFields.Transaction] = field(default_factory=set)
    log: set[EVMFields.Log] = field(default_factory=set)
    stateDiff: set[EVMFields.StateDiff] = field(default_factory=set)
    trace: set[EVMFields.Trace] = field(default_factory=set)

    # Solana fields using the imported enums
    instruction: set[SolanaFields.Instruction] = field(default_factory=set)
    solanaTransaction: set[SolanaFields.SolanaTransaction] = field(default_factory=set)
    solanaLog: set[SolanaFields.SolanaLog] = field(default_factory=set)
    balance: set[SolanaFields.Balance] = field(default_factory=set)
    tokenBalance: set[SolanaFields.TokenBalance] = field(default_factory=set)
    reward: set[SolanaFields.Reward] = field(default_factory=set)
    solanaBlock: set[SolanaFields.SolanaBlock] = field(default_factory=set)

    # Expose field enums as nested classes for backward compatibility
    Block = EVMFields.Block
    Transaction = EVMFields.Transaction
    Log = EVMFields.Log
    StateDiff = EVMFields.StateDiff
    Trace = EVMFields.Trace

    # Solana field enums
    Instruction = SolanaFields.Instruction
    SolanaTransaction = SolanaFields.SolanaTransaction
    SolanaLog = SolanaFields.SolanaLog
    Balance = SolanaFields.Balance
    TokenBalance = SolanaFields.TokenBalance
    Reward = SolanaFields.Reward
    SolanaBlock = SolanaFields.SolanaBlock

    @classmethod
    def all_fields(cls):
        """Get all available fields for all data types."""
        return cls(
            block=set(EVMFields.Block),
            transaction=set(EVMFields.Transaction),
            log=set(EVMFields.Log),
            stateDiff=set(EVMFields.StateDiff),
            trace=set(EVMFields.Trace),
            # Solana fields
            instruction=set(SolanaFields.Instruction),
            solanaTransaction=set(SolanaFields.SolanaTransaction),
            solanaLog=set(SolanaFields.SolanaLog),
            balance=set(SolanaFields.Balance),
            tokenBalance=set(SolanaFields.TokenBalance),
            reward=set(SolanaFields.Reward),
            solanaBlock=set(SolanaFields.SolanaBlock),
        )

    @classmethod
    def minimal_fields(cls):
        """Get minimal fields (just IDs and indexes)."""
        return cls(
            block={EVMFields.Block.number},
            transaction={
                EVMFields.Transaction.hash,
                EVMFields.Transaction.transactionIndex,
            },
            log={EVMFields.Log.logIndex, EVMFields.Log.transactionIndex},
            stateDiff={EVMFields.StateDiff.transactionIndex},
            trace={EVMFields.Trace.transactionIndex, EVMFields.Trace.traceAddress},
            # Solana minimal fields
            instruction={
                SolanaFields.Instruction.transactionIndex,
                SolanaFields.Instruction.instructionAddress,
            },
            solanaTransaction={SolanaFields.SolanaTransaction.transactionIndex},
            solanaLog={
                SolanaFields.SolanaLog.transactionIndex,
                SolanaFields.SolanaLog.logIndex,
            },
            balance={
                SolanaFields.Balance.transactionIndex,
                SolanaFields.Balance.account,
            },
            tokenBalance={
                SolanaFields.TokenBalance.transactionIndex,
                SolanaFields.TokenBalance.account,
            },
            reward={SolanaFields.Reward.pubKey},
            solanaBlock={SolanaFields.SolanaBlock.number},
        )

    @classmethod
    def block_only(cls):
        """Get fields for blocks only."""
        return cls(
            block=set(EVMFields.Block),
            transaction=set(),
            log=set(),
            stateDiff=set(),
            trace=set(),
            # Solana fields
            instruction=set(),
            solanaTransaction=set(),
            solanaLog=set(),
            balance=set(),
            tokenBalance=set(),
            reward=set(),
            solanaBlock=set(),
        )

    @classmethod
    def transactions_only(cls):
        """Get fields for transactions only."""
        return cls(
            block=set(),
            transaction=set(EVMFields.Transaction),
            log=set(),
            stateDiff=set(),
            trace=set(),
            # Solana fields
            instruction=set(),
            solanaTransaction=set(),
            solanaLog=set(),
            balance=set(),
            tokenBalance=set(),
            reward=set(),
            solanaBlock=set(),
        )

    def to_sqd_string(self):
        return json_lib.dumps(
            {
                k: {f.value: True for f in v}
                for k, v in asdict(self).items()
                if len(v) > 0
            },
            separators=(",", ":"),
        )
