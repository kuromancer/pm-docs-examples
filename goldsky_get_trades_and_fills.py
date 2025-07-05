import requests
from datetime import datetime, timedelta
from typing import List, Tuple, TypeVar
import time

TypeVar("Trade", bound=Trade)
TypeVar("Fill", bound=Fill)


def fetch_trades(
    start_trades_timestamp: int,
    start_fills_timestamp: int,
    asset_id: str,
    end_trades_timestamp: int = int((datetime.now() + timedelta(days=1)).timestamp()),
    end_fills_timestamp: int = int((datetime.now() + timedelta(days=1)).timestamp()),
    first: int = 1000,
    depth: int = 1,
) -> Tuple[List[Trade], List[Fill]]:  # Add 'first' parameter
    url = "https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/orderbook-subgraph/prod/gn"
    all_trades = []
    all_fills = []
    skip = 0
    # recursive depth limit
    if depth > 5:
        return all_trades, all_fills
    # exponential backoff
    if depth > 1:
        time.sleep(2**depth)
    while True:
        query = """
        query GetLatestTrades($startTradesTimestamp: BigInt!, $startFillsTimestamp: BigInt!, $endTradesTimestamp: BigInt!, $endFillsTimestamp: BigInt!, $assetID: String!, $first: Int!, $skip: Int!) {
            orderFilledEvents(
                where: {
                    timestamp_gt: $startTradesTimestamp,
                    makerAssetId: $assetID
                }
                orderBy: timestamp
                orderDirection: asc
                first: $first  # Add 'first' to the query
                skip: $skip    # Add 'skip' to the query
            ) {
                id
                transactionHash
                timestamp
                orderHash
                maker
                taker
                makerAssetId
                takerAssetId
                makerAmountFilled
                takerAmountFilled
                fee
            }
            ordersMatchedEvents(
                where: {
                    timestamp_gt: $startFillsTimestamp,
                    takerAssetID: $assetID
                }
                orderBy: timestamp
                orderDirection: asc
                first: $first  # Add 'first' to the query
                skip: $skip    # Add 'skip' to the query
            ) {
                id
                timestamp
                makerAssetID
                takerAssetID
                makerAmountFilled
                takerAmountFilled
            }
        }
        """

        variables = {
            "startTradesTimestamp": str(start_trades_timestamp),
            "startFillsTimestamp": str(start_fills_timestamp),
            "endTradesTimestamp": str(end_trades_timestamp),
            "endFillsTimestamp": str(end_fills_timestamp),
            "assetID": asset_id,
            "first": first,  # Pass 'first' to variables
            "skip": skip,  # Pass 'skip' to variables
        }

        payload = {"query": query, "variables": variables}

        headers = {"Content-Type": "application/json"}

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            if (
                data["errors"][0]["message"]
                == "the chain was reorganized while executing the query"
            ):
                logger.info(
                    "Chain was reorganized while executing the query, skipping..."
                )
                return fetch_trades(
                    start_trades_timestamp,
                    start_fills_timestamp,
                    asset_id,
                    end_trades_timestamp,
                    end_fills_timestamp,
                    first,
                    depth + 1,
                )
            raise Exception(f"GraphQL Errors: {data['errors']}")

        trades = []
        fills = []
        if "data" in data:
            trades = data["data"]["orderFilledEvents"]
            fills = data["data"]["ordersMatchedEvents"]
            trades.sort(
                key=lambda x: int(x.get("timestamp", 0)), reverse=True
            )  # Sort within each batch
            fills.sort(
                key=lambda x: int(x.get("timestamp", 0)), reverse=True
            )  # Sort within each batch
        if not trades and not fills:  # If there are no trades, break the loop
            break

        all_trades.extend(trades)
        all_fills.extend(fills)
        skip += first  # Increment skip

    return all_trades, all_fills
