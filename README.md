# Trading Bot — Binance Futures Testnet (USDT-M)

A small, structured Python CLI application that places **MARKET** and
**LIMIT** orders on the Binance USDT-M Futures **Testnet**, with input
validation, structured logging, and clean error handling.

## Project Structure

```
trading_bot/
  bot/
    __init__.py
    client.py           # Signed REST wrapper around the Binance Futures Testnet API
    orders.py            # Order placement logic (calls client, builds OrderResult)
    validators.py         # CLI input validation (symbol/side/type/qty/price)
    logging_config.py     # Rotating file + console logging setup
    cli.py                # argparse-based CLI entry point
  sample_logs/
    market_order_sample.log
    limit_order_sample.log
  requirements.txt
  README.md
```

- **client.py** only knows how to talk to Binance (build signed requests, send them, raise
  clear exceptions). It has no CLI or business-logic knowledge.
- **orders.py** turns validated parameters into an API call, logs the request/response,
  and returns a predictable `OrderResult` object.
- **validators.py** is pure, dependency-free validation logic — easy to unit test.
- **cli.py** wires everything together and is the only layer that touches `argparse`/`print`.

## Setup

1. **Clone / unzip this project**, then create a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a Binance Futures Testnet account and API key**:
   - Go to https://testnet.binancefuture.com and log in (GitHub account).
   - Generate an **API Key** and **Secret** from the testnet dashboard.
   - Fund your testnet account (a free faucet balance is provided automatically).

4. **Provide your credentials** (either works):
   ```bash
   export BINANCE_API_KEY="your_testnet_api_key"
   export BINANCE_API_SECRET="your_testnet_api_secret"
   ```
   or pass them directly with `--api-key` / `--api-secret` on each command.

## How to Run

### Place a MARKET order
```bash
python3 -m bot.cli --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Place a LIMIT order
```bash
python3 -m bot.cli --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.5 --price 3500
```

### Try it without API keys (`--dry-run`)
Every command supports `--dry-run`, which validates input and prints exactly what
*would* be sent, using a simulated response — no network call, no credentials needed.
This is how `sample_logs/*.log` in this repo were generated.
```bash
python3 -m bot.cli --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01 --dry-run
python3 -m bot.cli --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.5 --price 3500 --dry-run
```

### Example output
```
ORDER REQUEST:
  symbol: BTCUSDT
  side: BUY
  order_type: MARKET
  quantity: 0.01
  price: None
ORDER RESPONSE:
  orderId: 48253766
  status: FILLED
  executedQty: 0.01
  avgPrice: 42913.37
SUCCESS
```

On failure (bad input, rejected order, or network issue), the CLI prints `ERROR: <message>`
followed by `FAILED`, and the full details are always written to the log file.

## Logging

All requests, responses, and errors are logged to `logs/trading_bot.log` (created
automatically, rotated at 2MB with 5 backups). Console output stays at `INFO` level and
above (clean), while the file captures `DEBUG` level detail including the exact
signed-request parameters (minus the signature) and raw Binance response bodies.

The `sample_logs/` folder contains real log output from one MARKET and one LIMIT order,
generated via `--dry-run` for this submission.

## Error Handling & Validation

- **Input validation** (`validators.py`): symbol format, side (`BUY`/`SELL`), order type
  (`MARKET`/`LIMIT`), quantity > 0, and price required + > 0 for LIMIT orders. Invalid input
  is rejected before any network call is made.
- **API errors**: non-200 responses from Binance are caught and raised as `BinanceAPIError`
  with the status code and payload, logged, and surfaced as a clean failure message.
- **Network errors**: connection/timeout issues are caught as `BinanceNetworkError` so the
  CLI never crashes with a raw traceback.
- **Unexpected errors**: a final catch-all logs the full traceback (`logger.exception`) while
  still returning a clean, predictable result to the CLI.

## Assumptions

- Only **USDT-M Futures** (`/fapi/v1/order` on `https://testnet.binancefuture.com`) is in
  scope, per the task description — not Spot or Coin-M.
- Only `MARKET` and `LIMIT` order types are required; `LIMIT` orders default to
  `timeInForce=GTC` since the task did not specify a different policy.
- `--dry-run` was added so the app (and its logging) can be fully exercised and demonstrated
  without requiring live testnet credentials in this environment — this satisfies the "log
  files from at least one MARKET and one LIMIT order" deliverable. With real
  `BINANCE_API_KEY` / `BINANCE_API_SECRET` values, the exact same code path places real
  orders on the testnet (only the network call and response are different).
- Symbol validation assumes standard USDT-M perpetual naming (e.g. `BTCUSDT`, `ETHUSDT`).

## Bonus

Enhanced CLI UX: clear, labeled request/response summary blocks, explicit validation error
messages, and a `--dry-run` mode for safe experimentation without live credentials.
