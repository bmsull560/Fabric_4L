---
name: format_currency
description: Formats numeric values as localized currency strings
---

# Format Currency

Format numeric values as localized currency strings with proper symbols.

## Parameters

- `amount`: number — Amount to format (required)
- `currency`: string — Currency code USD, EUR, GBP, etc. (default: USD)
- `locale`: string — Locale code (default: en_US)
- `decimals`: integer — Decimal places (default: 0)

## Steps

1. Get currency symbol for code
2. Format number with locale settings
3. Apply symbol and sign
4. Return formatted string

## Output

Returns FormatCurrencyOutput with:
- `formatted`: Formatted currency string
- `numeric`: Original numeric value
- `currency`: Currency code
