import pytest

from sqd_portal_client_evm.query import Query, _validate_address

VITALIK_ETH = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045".lower()


class TestQueryValidation:
    """Test Query class validation and initialization."""

    def test_query_basic_creation(self):
        """Test basic Query creation."""
        query = Query(
            fromBlock=1000,
            toBlock=2000,
            transactionsRequests=[],
            logsRequests=[],
            stateDiffsRequests=[],
            tracesRequests=[],
            fields=Query.Fields.minimal_fields()
        )
        assert query.fromBlock == 1000
        assert query.toBlock == 2000

    def test_query_validation_from_block_negative(self):
        """Test that negative fromBlock raises ValueError."""
        with pytest.raises(ValueError, match="fromBlock must be non-negative"):
            Query(
                fromBlock=-1,
                transactionsRequests=[],
                logsRequests=[],
                stateDiffsRequests=[],
                tracesRequests=[],
                fields=Query.Fields.minimal_fields()
            )

    def test_query_validation_to_block_before_from_block(self):
        """Test that toBlock before fromBlock raises ValueError."""
        with pytest.raises(ValueError, match="toBlock .* must be greater than or equal to fromBlock"):
            Query(
                fromBlock=2000,
                toBlock=1000,
                transactionsRequests=[],
                logsRequests=[],
                stateDiffsRequests=[],
                tracesRequests=[],
                fields=Query.Fields.minimal_fields()
            )

    def test_query_no_requests_warning(self):
        """Test that query with no requests shows warning."""
        with pytest.warns(UserWarning, match="Query has no request filters specified"):
            Query(
                fromBlock=1000,
                toBlock=2000,
                transactionsRequests=[],
                logsRequests=[],
                stateDiffsRequests=[],
                tracesRequests=[],
                fields=Query.Fields.minimal_fields()
            )


class TestAddressValidation:
    """Test address validation functionality."""

    def test_validate_address_valid(self):
        """Test valid address validation."""
        address = VITALIK_ETH
        result = _validate_address(address)
        assert result == address.lower()

    def test_validate_address_no_prefix(self):
        """Test address validation without 0x prefix."""
        address = "d8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        result = _validate_address(address)
        assert result == "0x" + address.lower()

    def test_validate_address_invalid_length(self):
        """Test invalid address length."""
        with pytest.raises(ValueError, match="Invalid address length"):
            _validate_address("0x123")

    def test_validate_address_invalid_hex(self):
        """Test invalid hex characters in address."""
        with pytest.raises(ValueError, match="Invalid address format"):
            _validate_address("0xgggggggggggggggggggggggggggggggggggggggg")

    def test_validate_address_empty(self):
        """Test empty address."""
        with pytest.raises(ValueError, match="Address cannot be empty"):
            _validate_address("")


class TestTransactionsRequest:
    """Test TransactionsRequest functionality."""

    def test_transactions_request_creation(self):
        """Test basic TransactionsRequest creation."""
        request = Query.TransactionsRequest(
            from_=[VITALIK_ETH],
            to=["0x1234567890123456789012345678901234567890"]
        )
        assert len(request.from_) == 1
        assert len(request.to) == 1

    def test_transactions_request_from_address_classmethod(self):
        """Test from_address classmethod."""
        request = Query.TransactionsRequest.from_address(VITALIK_ETH)
        assert request.from_ == [VITALIK_ETH]
        assert request.to is None

    def test_transactions_request_to_address_classmethod(self):
        """Test to_address classmethod."""
        request = Query.TransactionsRequest.to_address("0x1234567890123456789012345678901234567890")
        assert request.to == ["0x1234567890123456789012345678901234567890"]
        assert request.from_ is None

    def test_transactions_request_transfer_classmethod(self):
        """Test transfer classmethod."""
        request = Query.TransactionsRequest.transfer(VITALIK_ETH)
        assert request.sighash == ["0xa9059cbb"]
        assert request.logs is True


class TestLogsRequest:
    """Test LogsRequest functionality."""

    def test_logs_request_creation(self):
        """Test basic LogsRequest creation."""
        request = Query.LogsRequest(
            address=[VITALIK_ETH],
            topic0=["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"]
        )
        assert len(request.address) == 1
        assert len(request.topic0) == 1

    def test_logs_request_from_contract_classmethod(self):
        """Test from_contract classmethod."""
        request = Query.LogsRequest.from_contract(VITALIK_ETH)
        assert request.address == [VITALIK_ETH]
        assert request.transaction is False

    def test_logs_request_transfer_event_classmethod(self):
        """Test transfer_event classmethod."""
        request = Query.LogsRequest.transfer_event(VITALIK_ETH)
        assert request.address == [VITALIK_ETH]
        assert request.topic0 == ["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"]
        assert request.transaction is True


class TestStateDiffsRequest:
    """Test StateDiffsRequest functionality."""

    def test_state_diffs_request_creation(self):
        """Test basic StateDiffsRequest creation."""
        request = Query.StateDiffsRequest(
            address=[VITALIK_ETH]
        )
        assert len(request.address) == 1

    def test_state_diffs_request_for_contract_classmethod(self):
        """Test for_contract classmethod."""
        request = Query.StateDiffsRequest.for_contract(VITALIK_ETH)
        assert request.address == [VITALIK_ETH]


class TestTracesRequest:
    """Test TracesRequest functionality."""

    def test_traces_request_creation(self):
        """Test basic TracesRequest creation."""
        request = Query.TracesRequest(
            address=[VITALIK_ETH]
        )
        assert len(request.address) == 1

    def test_traces_request_for_contract_classmethod(self):
        """Test for_contract classmethod."""
        request = Query.TracesRequest.for_contract(VITALIK_ETH)
        assert request.address == [VITALIK_ETH]


class TestFields:
    """Test Fields functionality."""

    def test_fields_creation(self):
        """Test basic Fields creation."""
        fields = Query.Fields(
            block={Query.Fields.Block.number, Query.Fields.Block.hash},
            transaction={Query.Fields.Transaction.hash}
        )
        assert Query.Fields.Block.number in fields.block
        assert Query.Fields.Block.hash in fields.block
        assert Query.Fields.Transaction.hash in fields.transaction

    def test_all_fields(self):
        """Test all_fields classmethod."""
        fields = Query.Fields.all_fields()
        assert len(fields.block) > 0
        assert len(fields.transaction) > 0
        assert len(fields.log) > 0
        assert len(fields.stateDiff) > 0
        assert len(fields.trace) > 0

    def test_minimal_fields(self):
        """Test minimal_fields classmethod."""
        fields = Query.Fields.minimal_fields()
        assert Query.Fields.Block.number in fields.block
        assert Query.Fields.Transaction.hash in fields.transaction
        assert Query.Fields.Transaction.transactionIndex in fields.transaction

    def test_block_only(self):
        """Test block_only classmethod."""
        fields = Query.Fields.block_only()
        assert len(fields.block) > 0
        assert len(fields.transaction) == 0
        assert len(fields.log) == 0

    def test_transactions_only(self):
        """Test transactions_only classmethod."""
        fields = Query.Fields.transactions_only()
        assert len(fields.transaction) > 0
        assert len(fields.block) == 0
        assert len(fields.log) == 0


class TestQueryConvenienceMethods:
    """Test Query convenience methods."""

    def test_transactions_method(self):
        """Test transactions classmethod."""
        query = Query.transactions(
            from_address=VITALIK_ETH,
            from_block=1000,
            to_block=2000
        )
        assert query.fromBlock == 1000
        assert query.toBlock == 2000
        assert len(query.transactionsRequests) == 1
        assert query.transactionsRequests[0].from_ == [VITALIK_ETH]

    def test_logs_from_contract_method(self):
        """Test logs_from_contract classmethod."""
        query = Query.logs_from_contract(
            contract_address=VITALIK_ETH,
            from_block=1000
        )
        assert query.fromBlock == 1000
        assert len(query.logsRequests) == 1
        assert query.logsRequests[0].address == [VITALIK_ETH]

    def test_erc20_transfers_method(self):
        """Test erc20_transfers classmethod."""
        query = Query.erc20_transfers(
            token_address=VITALIK_ETH,
            from_block=1000
        )
        assert query.fromBlock == 1000
        assert len(query.logsRequests) == 1
        assert query.logsRequests[0].address == [VITALIK_ETH]
        assert query.logsRequests[0].topic0 == ["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"]

    def test_simple_block_range_method(self):
        """Test simple_block_range classmethod."""
        query = Query.simple_block_range(1000, 2000)
        assert query.fromBlock == 1000
        assert query.toBlock == 2000
        assert len(query.transactionsRequests) == 0
        assert len(query.logsRequests) == 0


class TestQuerySerialization:
    """Test Query serialization to SQD string format."""

    def test_query_to_sqd_string_basic(self):
        """Test basic query serialization."""
        query = Query(
            fromBlock=1000,
            toBlock=2000,
            transactionsRequests=[
                Query.TransactionsRequest.from_address(VITALIK_ETH)
            ],
            logsRequests=[],
            stateDiffsRequests=[],
            tracesRequests=[],
            fields=Query.Fields.minimal_fields()
        )

        sqd_string = query.to_sqd_string()

        # Basic structure checks
        assert '"type":"evm"' in sqd_string
        assert '"fromBlock":1000' in sqd_string
        assert '"toBlock":2000' in sqd_string
        assert "transactions" in sqd_string
        assert "fields" in sqd_string

    def test_query_to_sqd_string_minimal(self):
        """Test minimal query serialization."""
        query = Query.simple_block_range(1000, 2000)
        sqd_string = query.to_sqd_string()

        assert '"type":"evm"' in sqd_string
        assert '"fromBlock":1000' in sqd_string
        assert '"toBlock":2000' in sqd_string
