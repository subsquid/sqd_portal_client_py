import sqd_portal_client_evm as sqe

sqe.get_data(
    dataset=sqe.Dataset.BINANCE,
    query=sqe.Query(
        transactionsRequests=[
            sqe.Query.TransactionsRequest(from_=["dsfsdf "]),
            sqe.Query.TransactionsRequest(sighash=["sdfsdf"]),
            sqe.Query.TransactionsRequest(),
        ],
        fields=sqe.Query.Fields(
            transaction={
                sqe.Query.Fields.Transaction.transactionIndex,
                sqe.Query.Fields.Transaction.hash,
            }
        ),
    ),
)
