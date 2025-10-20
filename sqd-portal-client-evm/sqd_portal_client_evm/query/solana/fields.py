"""
Solana Fields for SQD Portal Client

This module provides Solana-specific field definitions for SQD (Subsquid) Network portal queries.
"""

from enum import Enum


class SolanaFields:
    """Solana-specific field definitions"""

    class Instruction(Enum):
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

    class SolanaTransaction(Enum):
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

    class SolanaLog(Enum):
        """Available Solana log fields"""

        transactionIndex = "transactionIndex"
        logIndex = "logIndex"
        instructionAddress = "instructionAddress"
        programId = "programId"
        kind = "kind"
        message = "message"

    class Balance(Enum):
        """Available balance fields"""

        transactionIndex = "transactionIndex"
        account = "account"
        pre = "pre"
        post = "post"

    class TokenBalance(Enum):
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

    class Reward(Enum):
        """Available reward fields"""

        pubKey = "pubKey"
        lamports = "lamports"
        postBalance = "postBalance"
        rewardType = "rewardType"
        commission = "commission"

    class SolanaBlock(Enum):
        """Available Solana block fields"""

        number = "number"
        height = "height"
        parentSlot = "parentSlot"
        timestamp = "timestamp"

    @classmethod
    def minimal_fields(cls):
        return SolanaFields({SolanaFields.SolanaBlock.number})

    def to_dict(self):
        """Convert fields to dictionary format for SQD API"""
        if isinstance(self, set):
            # Handle legacy set format
            return {field.value for field in self}
        else:
            # Handle SolanaFields object
            return {field.value for field in self._fields}

    def __init__(self, fields_set):
        self._fields = fields_set
