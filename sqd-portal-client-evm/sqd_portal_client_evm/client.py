from typing import Optional
from .dataset import Dataset
from .query import *
from .transport import fetch_query_output

def get_data(
	*,
	dataset: Dataset | str,
	query: Query | str,
	portal_url: str = 'https://portal.sqd.dev',
	flattening: Optional[str] = 'by_itemtype'
):
	endpoint = f'{portal_url}/datasets/{dataset.value}/finalized-stream'
	str_query = query.to_sqd_string()
	print(str_query)
	return fetch_query_output(endpoint, str_query)
