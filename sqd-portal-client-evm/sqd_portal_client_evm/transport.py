import requests
import json

def fetch_query_output(
	portal_endpoint_url: str,
	query: dict
) -> list[dict]:
	headers = {
		'Content-Type': 'application/json',
		'User-Agent': 'sqd_portal_client_py/0'
	}
	resp = requests.post(
		portal_endpoint_url,
		json=query,
		headers=headers
	)
	print(resp.text)
	return [ json.loads(jline) for jline in resp.text.split('\n') if jline != '' ]
