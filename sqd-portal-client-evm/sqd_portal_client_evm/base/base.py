from dataclasses import field, dataclass, asdict
from typing import Literal
import ujson as json_lib

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
        return

    _bind_field_enum_classes()


def _bind_field_enum_classes():
    """Bind enum classes to _Fields once they're available."""
    if EVMFields:
        _Fields.Block = EVMFields.Block
        _Fields.Transaction = EVMFields.Transaction
        _Fields.Log = EVMFields.Log
        _Fields.StateDiff = EVMFields.StateDiff
        _Fields.Trace = EVMFields.Trace

    if SolanaFields:
        _Fields.Instruction = SolanaFields.Instruction
        _Fields.SolanaTransaction = SolanaFields.SolanaTransaction
        _Fields.SolanaLog = SolanaFields.SolanaLog
        _Fields.Balance = SolanaFields.Balance
        _Fields.TokenBalance = SolanaFields.TokenBalance
        _Fields.Reward = SolanaFields.Reward
        _Fields.SolanaBlock = SolanaFields.SolanaBlock


@dataclass(frozen=True, kw_only=True)
class _Fields:
    """
    Defines which fields to include in query results for different data types.
    """

    # EVM fields using the imported enums
    block: set = field(default_factory=set)
    transaction: set = field(default_factory=set)
    log: set = field(default_factory=set)
    stateDiff: set = field(default_factory=set)
    trace: set = field(default_factory=set)

    # Solana fields using the imported enums
    instruction: set = field(default_factory=set)
    solanaTransaction: set = field(default_factory=set)
    solanaLog: set = field(default_factory=set)
    balance: set = field(default_factory=set)
    tokenBalance: set = field(default_factory=set)
    reward: set = field(default_factory=set)
    solanaBlock: set = field(default_factory=set)

    # Enum placeholders (bound at runtime)
    Block = None
    Transaction = None
    Log = None
    StateDiff = None
    Trace = None
    Instruction = None
    SolanaTransaction = None
    SolanaLog = None
    Balance = None
    TokenBalance = None
    Reward = None
    SolanaBlock = None

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

    def to_sqd_string(self):
        return json_lib.dumps(
            {
                k: {f.value: True for f in v}
                for k, v in asdict(self).items()
                if len(v) > 0
            },
            separators=(",", ":"),
        )
