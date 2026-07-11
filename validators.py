# Input validation for order params from the CLI. Kept separate from the
# CLI and client layers so it's easy to test on its own.

import re

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}

# quick sanity check for USDT-M pairs like BTCUSDT, ETHUSDT
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{2,15}USDT$")


class ValidationError(ValueError):
    pass


def validate_symbol(symbol):
    if not symbol:
        raise ValidationError("Symbol is required (e.g. BTCUSDT).")
    symbol = symbol.strip().upper()
    if not SYMBOL_PATTERN.match(symbol):
        raise ValidationError(f"Invalid symbol '{symbol}'. Expected a USDT-M pair like 'BTCUSDT'.")
    return symbol


def validate_side(side):
    if not side:
        raise ValidationError("Side is required (BUY or SELL).")
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(f"Invalid side '{side}'. Must be one of {sorted(VALID_SIDES)}.")
    return side


def validate_order_type(order_type):
    if not order_type:
        raise ValidationError("Order type is required (MARKET or LIMIT).")
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(f"Invalid order type '{order_type}'. Must be one of {sorted(VALID_ORDER_TYPES)}.")
    return order_type


def validate_quantity(quantity):
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity must be a number, got '{quantity}'.")
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than 0.")
    return quantity


def validate_price(price, order_type):
    # price only matters for LIMIT orders, ignored for MARKET
    if order_type == "MARKET":
        return None
    if price is None:
        raise ValidationError("Price is required for LIMIT orders.")
    try:
        price = float(price)
    except (TypeError, ValueError):
        raise ValidationError(f"Price must be a number, got '{price}'.")
    if price <= 0:
        raise ValidationError("Price must be greater than 0.")
    return price


def validate_order_params(symbol, side, order_type, quantity, price=None):
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    order_type = validate_order_type(order_type)
    quantity = validate_quantity(quantity)
    price = validate_price(price, order_type)

    return {
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "price": price,
    }
