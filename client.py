"""
REST client for Binance Futures Testnet (USDT-M).

Handles request signing and sending. Doesn't know anything about CLI
args or validation - that's handled in other files.

Docs: https://binance-docs.github.io/apidocs/testnet/en/
"""

import hashlib
import hmac
import logging
import time
from urllib.parse import urlencode

import requests

logger = logging.getLogger("trading_bot.client")

FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"


class BinanceAPIError(Exception):
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"Binance API error [{status_code}]: {payload}")


class BinanceNetworkError(Exception):
    pass


class BinanceFuturesClient:
    """
    Signed REST wrapper for the Binance USDT-M Futures Testnet.
    Only implements what this project needs - placing orders and
    a basic account info call to sanity check credentials.
    """

    def __init__(self, api_key, api_secret, base_url=FUTURES_TESTNET_BASE_URL,
                 timeout=10, recv_window=5000):
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret are required.")
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.recv_window = recv_window
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    def _sign(self, params):
        query_string = urlencode(params)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _signed_request(self, method, path, params):
        params = dict(params)
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = self.recv_window
        params["signature"] = self._sign(params)

        url = f"{self.base_url}{path}"
        logged_params = {k: v for k, v in params.items() if k != "signature"}
        logger.debug("Request -> %s %s | params=%s", method, url, logged_params)

        try:
            response = self.session.request(method, url, params=params, timeout=self.timeout)
        except requests.exceptions.RequestException as exc:
            logger.error("Network error calling %s: %s", url, exc)
            raise BinanceNetworkError(str(exc)) from exc

        try:
            payload = response.json()
        except ValueError:
            payload = {"raw_text": response.text}

        if response.status_code != 200:
            logger.error("Binance returned error %s: %s", response.status_code, payload)
            raise BinanceAPIError(response.status_code, payload)

        logger.debug("Response <- %s %s | body=%s", method, url, payload)
        return payload

    def place_order(self, symbol, side, order_type, quantity, price=None, time_in_force="GTC"):
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }
        # timeInForce is required for LIMIT orders but Binance rejects it on MARKET orders
        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = time_in_force

        return self._signed_request("POST", "/fapi/v1/order", params)

    def get_account_info(self):
        # not used by the CLI directly, kept around for quick manual testing
        # of API keys, e.g. from a python shell
        return self._signed_request("GET", "/fapi/v2/account", {})
