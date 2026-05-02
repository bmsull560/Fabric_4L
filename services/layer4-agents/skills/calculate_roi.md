---
name: calculate_roi
description: Calculates ROI, NPV, IRR, and payback period
---

# Calculate ROI

Calculate comprehensive ROI metrics from investment and returns data.

## Parameters

- `investment`: number — Initial investment amount (required, >= 0)
- `returns`: array — List of periodic returns (optional)
- `time_periods`: integer — Number of time periods (default: 3)
- `discount_rate`: number — Discount rate 0.0-1.0 (default: 0.1)

## Steps

1. Calculate simple ROI: (total_return - investment) / investment
2. Calculate NPV using discount rate
3. Approximate IRR using iterative approach
4. Calculate payback period
5. Return all metrics

## Output

Returns CalculateROIOutput with:
- `simple_roi_percent`: Simple ROI percentage
- `npv`: Net Present Value
- `irr`: Internal Rate of Return (or null)
- `payback_period_months`: Payback period in months (or null)
- `total_return`: Sum of all returns
