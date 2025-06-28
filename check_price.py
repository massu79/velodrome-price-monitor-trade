import requests
from datetime import datetime, timedelta

def fetch_velodrome_price(pair_address: str):
    url = "https://api.thegraph.com/subgraphs/name/velodrome/v2"  # 最新のサブグラフURLに置き換えてください
    now = int(datetime.utcnow().timestamp())
    since = int((datetime.utcnow() - timedelta(hours=24)).timestamp())

    query = """
    {
      swaps(first: 1000, orderBy: timestamp, orderDirection: desc,
        where: {pair: "%s", timestamp_gte: %d}) {
        amount0In
        amount1In
        amount0Out
        amount1Out
        timestamp
      }
    }
    """ % (pair_address.lower(), since)

    response = requests.post(url, json={'query': query})
    data = response.json()

    if 'data' not in data or 'swaps' not in data['data']:
        raise ValueError("Invalid data received")

    prices = []
    for swap in data['data']['swaps']:
        try:
            # 単純な価格推定（例：WETH/USDC）
            amount_usdc = float(swap["amount0In"] or swap["amount0Out"] or 0)
            amount_weth = float(swap["amount1Out"] or swap["amount1In"] or 0)
            if amount_weth > 0:
                price = amount_usdc / amount_weth
                prices.append(price)
        except:
            continue

    if not prices:
        raise ValueError("No valid prices found")

    return {
        "current": prices[0],
        "min_24h": min(prices),
        "max_24h": max(prices)
    }
