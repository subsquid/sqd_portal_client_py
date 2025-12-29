from sqd._compat import StrEnum

# ============================================================================ #
# Solana Field Definitions (API field names)
# ============================================================================ #

class InstructionField(StrEnum):
    """Available instruction fields"""
    transactionIndex = "transactionIndex"
    instructionAddress = "instructionAddress"
    programId = "programId"
    accounts = "accounts"
    data = "data"
    d1 = "d1"
    d2 = "d2"
    d4 = "d4"
    d8 = "d8"
    error = "error"
    computeUnitsConsumed = "computeUnitsConsumed"
    isCommitted = "isCommitted"
    hasDroppedLogMessages = "hasDroppedLogMessages"


class SolanaTransactionField(StrEnum):
    """Available Solana transaction fields"""
    transactionIndex = "transactionIndex"
    version = "version"
    accountKeys = "accountKeys"
    addressTableLookups = "addressTableLookups"
    numReadonlySignedAccounts = "numReadonlySignedAccounts"
    numReadonlyUnsignedAccounts = "numReadonlyUnsignedAccounts"
    numRequiredSignatures = "numRequiredSignatures"
    recentBlockhash = "recentBlockhash"
    signatures = "signatures"
    err = "err"
    fee = "fee"
    computeUnitsConsumed = "computeUnitsConsumed"
    loadedAddresses = "loadedAddresses"
    feePayer = "feePayer"
    hasDroppedLogMessages = "hasDroppedLogMessages"


class SolanaLogField(StrEnum):
    """Available Solana log fields"""
    transactionIndex = "transactionIndex"
    logIndex = "logIndex"
    instructionAddress = "instructionAddress"
    programId = "programId"
    kind = "kind"
    message = "message"


class BalanceField(StrEnum):
    """Available balance fields"""
    transactionIndex = "transactionIndex"
    account = "account"
    pre = "pre"
    post = "post"


class TokenBalanceField(StrEnum):
    """Available token balance fields"""
    transactionIndex = "transactionIndex"
    account = "account"
    preMint = "preMint"
    postMint = "postMint"
    preDecimals = "preDecimals"
    postDecimals = "postDecimals"
    preProgramId = "preProgramId"
    postProgramId = "postProgramId"
    preOwner = "preOwner"
    postOwner = "postOwner"
    preAmount = "preAmount"
    postAmount = "postAmount"


class RewardField(StrEnum):
    """Available reward fields"""
    pubKey = "pubKey"
    lamports = "lamports"
    postBalance = "postBalance"
    rewardType = "rewardType"
    commission = "commission"


class SolanaBlockField(StrEnum):
    """Available Solana block fields"""
    number = "number"
    height = "height"
    parentSlot = "parentSlot"
    timestamp = "timestamp"

