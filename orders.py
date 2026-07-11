import logging

from .client import BinanceAPIError, BinanceFuturesClient, BinanceNetworkError

logger = logging.getLogger("trading_bot.orders")


class OrderResult:
    # small wrapper so cli.py doesn't need to know the raw Binance response shape
    def __init__(self, success, request, response=None, error=None):
        self.success = success
        self.request = request
        self.response = response or {}
        self.error = error

    def summary_lines(self):
        lines = ["ORDER REQUEST:"]
        for key, value in self.request.items():
            lines.append(f"  {key}: {value}")

        if self.success:
            lines.append("ORDER RESPONSE:")
            lines.append(f"  orderId: {self.response.get('orderId')}")
            lines.append(f"  status: {self.response.get('status')}")
            lines.append(f"  executedQty: {self.response.get('executedQty')}")
            avg_price = self.response.get("avgPrice")
            if avg_price is not None:
                lines.append(f"  avgPrice: {avg_price}")
            lines.append("SUCCESS")
        else:
            lines.append(f"ERROR: {self.error}")
            lines.append("FAILED")

        return lines


def place_order(client: BinanceFuturesClient, symbol, side, order_type, quantity, price=None):
    request_payload = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
    }
    if order_type == "LIMIT":
        request_payload["price"] = price

    logger.info("Placing order: %s", request_payload)

    try:
        response = client.place_order(
            symbol=symbol, side=side, order_type=order_type,
            quantity=quantity, price=price,
        )
        logger.info("Order placed: orderId=%s status=%s", response.get("orderId"), response.get("status"))
        return OrderResult(True, request_payload, response=response)

    except BinanceAPIError as exc:
        message = f"Binance rejected the order ({exc.status_code}): {exc.payload}"
        logger.error(message)
        return OrderResult(False, request_payload, error=message)

    except BinanceNetworkError as exc:
        message = f"Network error while contacting Binance: {exc}"
        logger.error(message)
        return OrderResult(False, request_payload, error=message)

    except Exception as exc:
        logger.exception("Unexpected error placing order")
        return OrderResult(False, request_payload, error=f"Unexpected error: {exc}")
