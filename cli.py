# CLI entry point for the trading bot.
#
# Examples:
#   python -m bot.cli --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
#   python -m bot.cli --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 65000
#
# Credentials come from BINANCE_API_KEY / BINANCE_API_SECRET env vars, or
# --api-key/--api-secret. --dry-run validates input and simulates a response
# without calling Binance, useful for testing without real keys.

import argparse
import os
import random
import sys
import time

from .client import FUTURES_TESTNET_BASE_URL, BinanceFuturesClient
from .logging_config import setup_logging
from .orders import OrderResult, place_order
from .validators import ValidationError, validate_order_params


def build_parser():
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Place MARKET or LIMIT orders on Binance Futures Testnet (USDT-M).",
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, help="BUY or SELL")
    parser.add_argument("--type", dest="order_type", required=True, help="MARKET or LIMIT")
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument("--price", default=None, help="Order price (required for LIMIT)")
    parser.add_argument("--api-key", default=os.environ.get("BINANCE_API_KEY"))
    parser.add_argument("--api-secret", default=os.environ.get("BINANCE_API_SECRET"))
    parser.add_argument("--base-url", default=FUTURES_TESTNET_BASE_URL)
    parser.add_argument("--dry-run", action="store_true",
                         help="Validate and simulate a response without calling Binance")
    return parser


def _simulate_response(symbol, side, order_type, quantity, price):
    # used for --dry-run so the request/response/logging flow can be
    # demoed without real API keys or network access
    fill_price = price if price is not None else round(random.uniform(20000, 70000), 2)
    return {
        "orderId": random.randint(10_000_000, 99_999_999),
        "symbol": symbol,
        "status": "FILLED" if order_type == "MARKET" else "NEW",
        "side": side,
        "type": order_type,
        "executedQty": quantity if order_type == "MARKET" else "0",
        "avgPrice": fill_price if order_type == "MARKET" else "0",
        "updateTime": int(time.time() * 1000),
    }


def main(argv=None):
    logger = setup_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        params = validate_order_params(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
    except ValidationError as exc:
        logger.error("Input validation failed: %s", exc)
        print(f"Invalid input: {exc}")
        return 1

    if args.dry_run:
        logger.info("Dry run - simulating order, not contacting Binance: %s", params)
        response = _simulate_response(
            params["symbol"], params["side"], params["order_type"],
            params["quantity"], params["price"],
        )
        result = OrderResult(True, params, response=response)
        for line in result.summary_lines():
            print(line)
        print("(dry run - no order was actually sent to Binance)")
        return 0

    if not args.api_key or not args.api_secret:
        message = ("Missing API credentials. Set BINANCE_API_KEY / BINANCE_API_SECRET, "
                    "pass --api-key/--api-secret, or use --dry-run.")
        logger.error(message)
        print(f"Error: {message}")
        return 1

    client = BinanceFuturesClient(api_key=args.api_key, api_secret=args.api_secret, base_url=args.base_url)

    result = place_order(
        client=client,
        symbol=params["symbol"],
        side=params["side"],
        order_type=params["order_type"],
        quantity=params["quantity"],
        price=params["price"],
    )

    for line in result.summary_lines():
        print(line)

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
