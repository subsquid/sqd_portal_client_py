"""
EVM Fields for SQD Portal Client

This module provides EVM-specific field definitions for SQD (Subsquid) Network portal queries.
"""

from enum import Enum


class EVMFields:
    """EVM-specific field definitions"""

    class Block(Enum):
        """Available block fields (must match SQD API field names exactly)"""

        hash = "hash"
        number = "number"  # Note: SQD API uses 'number' not 'height'
        parentHash = "parentHash"
        timestamp = "timestamp"
        transactionsRoot = "transactionsRoot"
        receiptsRoot = "receiptsRoot"
        stateRoot = "stateRoot"
        logsBloom = "logsBloom"
        miner = "miner"
        size = "size"
        gasLimit = "gasLimit"
        gasUsed = "gasUsed"

    class Transaction(Enum):
        """Available transaction fields"""

        hash = "hash"
        transactionIndex = "transactionIndex"
        nonce = "nonce"
        from_ = "from"
        to = "to"
        input = "input"
        value = "value"
        gas = "gas"
        gasPrice = "gasPrice"
        maxFeePerGas = "maxFeePerGas"
        maxPriorityFeePerGas = "maxPriorityFeePerGas"
        v = "v"
        r = "r"
        s = "s"
        yParity = "yParity"
        chainId = "chainId"
        sighash = "sighash"
        contractAddress = "contractAddress"
        gasUsed = "gasUsed"
        cumulativeGasUsed = "cumulativeGasUsed"
        effectiveGasPrice = "effectiveGasPrice"
        type = "type"
        status = "status"
        maxFeePerBlobGas = "maxFeePerBlobGas"
        blobVersionedHashes = "blobVersionedHashes"
        l1Fee = "l1Fee"
        l1FeeScalar = "l1FeeScalar"
        l1GasPrice = "l1GasPrice"
        l1GasUsed = "l1GasUsed"
        l1BlobBaseFee = "l1BlobBaseFee"
        l1BlobBaseFeeScalar = "l1BlobBaseFeeScalar"
        l1BaseFeeScalar = "l1BaseFeeScalar"

    class Log(Enum):
        """Available log fields"""

        logIndex = "logIndex"
        transactionIndex = "transactionIndex"
        transactionHash = "transactionHash"
        address = "address"
        data = "data"
        topics = "topics"

    class StateDiff(Enum):
        """Available state diff fields"""

        transactionIndex = "transactionIndex"

    class Trace(Enum):
        """Available trace fields"""

        transactionIndex = "transactionIndex"
        traceAddress = "traceAddress"

    @classmethod
    def minimal_fields(cls):
        return EVMFields({EVMFields.Block.number})

    def to_dict(self):
        """Convert fields to dictionary format for SQD API"""
        if isinstance(self, set):
            # Handle legacy set format
            return {field.value for field in self}
        else:
            # Handle EVMFields object
            return {field.value for field in self._fields}

    def __init__(self, fields_set):
        self._fields = fields_set
