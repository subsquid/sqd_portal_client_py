common_abis = {
    'erc20': {
        'events': {
            'Transfer': {
                'signature': 'Transfer(address,address,uint256)',
                'topic': '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef',
            }
        }
    }
}

__all__ = ['common_abis']
