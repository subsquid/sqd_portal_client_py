from typing import Optional
from enum import Enum
from dataclasses import dataclass, field, asdict
import json


def _request_to_sqd_string(r) -> str:
	correctFromUnderscore = lambda k: 'from' if k == 'from_' else k
	return json.dumps({ correctFromUnderscore(k): v for k, v in asdict(r).items() if not v == None }, separators=(',', ':'))


@dataclass(frozen=True, kw_only=True)
class Query:
	@dataclass(frozen=True, kw_only=True)
	class TransactionsRequest:
		"""
		Args:
			from_: list[str] - list of addresses
		"""
		from_: Optional[list[str]] = None
		to: Optional[list[str]] = None
		sighash: Optional[list[str]] = None
		logs: bool = False
		traces: bool = False
		stateDiffs: bool = False

		def to_sqd_string(self):
			return _request_to_sqd_string(self)

	@dataclass(frozen=True, kw_only=True)
	class LogsRequest:
		address: Optional[list[str]] = None
		topic0: Optional[list[str]] = None
		topic1: Optional[list[str]] = None
		topic2: Optional[list[str]] = None
		topic3: Optional[list[str]] = None
		transaction: bool = False
		transactionTraces: bool = False
		transactionLogs: bool = False

	@dataclass(frozen=True, kw_only=True)
	class StateDiffsRequest:
		address: Optional[list[str]] = None

	@dataclass(frozen=True, kw_only=True)
	class TracesRequest:
		address: Optional[list[str]] = None

	@dataclass(frozen=True, kw_only=True)
	class Fields:
		class Block(Enum):
			hash = 'hash'
			height = 'height'

		class Transaction(Enum):
			id = 'id'
			transactionIndex = 'transactionIndex'

		class Log(Enum):
			id = 'id'
			transactionIndex = 'transactionIndex'
			logIndex = 'logIndex'

		class StateDiff(Enum):
			transactionIndex = 'transactionIndex'

		class Trace(Enum):
			transactionIndex = 'transactionIndex'
			traceAddress = 'traceAddress'

		block: set['Fields.Block'] = field(default_factory=set)
		transaction: set['Fields.Transaction'] = field(default_factory=set)
		log: set['Fields.Log'] = field(default_factory=set)
		stateDiff: set['Fields.StateDiff'] = field(default_factory=set)
		trace: set['Fields.Trace'] = field(default_factory=set)

		def to_sqd_string(self):
			return json.dumps({ k: { f.value: True for f in v } for k, v in asdict(self).items() if len(v) > 0 }, separators=(',', ':'))


	fromBlock: int = 0
	toBlock: Optional[int] = None
	transactionsRequests: list[TransactionsRequest] = field(default_factory=list)
	logsRequests: list[LogsRequest] = field(default_factory=list)
	stateDiffsRequests: list[StateDiffsRequest] = field(default_factory=list)
	tracesRequests: list[TracesRequest] = field(default_factory=list)
	fields: Fields

	def to_sqd_string(self):
		requestsStrings = {
			'transactions': '[' + ','.join([ r.to_sqd_string() for r in self.transactionsRequests ]) + ']'
		}
		requestsString = ','.join([ f'"{k}":{v}' for k, v in requestsStrings.items() ])
		if requestsString != '':
			requestsString += ','

		toBlockString = '' if self.toBlock is None else f'"toBlock":{self.toBlock},'

		return f'{{"type":"evm","fromBlock":{self.fromBlock},{toBlockString}{requestsString}"fields":{self.fields.to_sqd_string()}}}'
