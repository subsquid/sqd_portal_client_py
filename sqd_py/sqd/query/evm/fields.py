from sqd._compat import StrEnum

# ============================================================================ #
# EVM Field Definitions (matches SQD API spec exactly)
# ============================================================================ #

class BlockField(StrEnum):
    """Available block header fields (per OpenAPI spec)"""
    hash = "hash"
    height = "height"
    number = "number"
    parentHash = "parentHash"
    timestamp = "timestamp"
    nonce = "nonce"
    sha3Uncles = "sha3Uncles"
    logsBloom = "logsBloom"
    transactionsRoot = "transactionsRoot"
    stateRoot = "stateRoot"
    receiptsRoot = "receiptsRoot"
    mixHash = "mixHash"
    miner = "miner"
    difficulty = "difficulty"
    totalDifficulty = "totalDifficulty"
    extraData = "extraData"
    size = "size"
    gasLimit = "gasLimit"
    gasUsed = "gasUsed"
    baseFeePerGas = "baseFeePerGas"
    l1BlockNumber = "l1BlockNumber"


class TransactionField(StrEnum):
    """Available transaction fields (per OpenAPI spec)"""
    transactionIndex = "transactionIndex"
    from_ = "from"
    to = "to"
    hash = "hash"
    gas = "gas"
    gasPrice = "gasPrice"
    maxFeePerGas = "maxFeePerGas"
    maxPriorityFeePerGas = "maxPriorityFeePerGas"
    input = "input"
    nonce = "nonce"
    value = "value"
    v = "v"
    r = "r"
    s = "s"
    yParity = "yParity"
    chainId = "chainId"
    gasUsed = "gasUsed"
    cumulativeGasUsed = "cumulativeGasUsed"
    effectiveGasPrice = "effectiveGasPrice"
    contractAddress = "contractAddress"
    type = "type"
    status = "status"
    sighash = "sighash"
    # L2-specific fields
    l1Fee = "l1Fee"
    l1FeeScalar = "l1FeeScalar"
    l1GasPrice = "l1GasPrice"
    l1GasUsed = "l1GasUsed"
    l1BlobBaseFee = "l1BlobBaseFee"
    l1BlobBaseFeeScalar = "l1BlobBaseFeeScalar"
    l1BaseFeeScalar = "l1BaseFeeScalar"


class LogField(StrEnum):
    """Available log fields (per OpenAPI spec)"""
    logIndex = "logIndex"
    transactionIndex = "transactionIndex"
    address = "address"
    data = "data"
    topics = "topics"
    transactionHash = "transactionHash"


class TraceField(StrEnum):
    """Available trace fields (per OpenAPI spec)"""
    transactionIndex = "transactionIndex"
    traceAddress = "traceAddress"
    type = "type"
    subtraces = "subtraces"
    error = "error"
    # Create trace fields
    createFrom = "createFrom"
    createValue = "createValue"
    createGas = "createGas"
    createInit = "createInit"
    createResultGasUsed = "createResultGasUsed"
    createResultCode = "createResultCode"
    createResultAddress = "createResultAddress"
    # Call trace fields
    callFrom = "callFrom"
    callTo = "callTo"
    callValue = "callValue"
    callGas = "callGas"
    callSighash = "callSighash"
    callInput = "callInput"
    callResultGasUsed = "callResultGasUsed"
    callResultOutput = "callResultOutput"
    # Suicide trace fields
    suicideAddress = "suicideAddress"
    suicideRefundAddress = "suicideRefundAddress"
    suicideBalance = "suicideBalance"
    # Reward trace fields
    rewardAuthor = "rewardAuthor"
    rewardValue = "rewardValue"
    rewardType = "rewardType"


class StateDiffField(StrEnum):
    """Available state diff fields (per OpenAPI spec)"""
    transactionIndex = "transactionIndex"
    address = "address"
    key = "key"
    kind = "kind"
    prev = "prev"
    next = "next"
