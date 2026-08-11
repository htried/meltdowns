#!/usr/bin/env bash
set -euo pipefail

echo "Generating sales ledger transactions CSV..."
cat <<'CSV' > source_ledger.csv
id,category,revenue,cost,tax_rate
1,apparel,1200.00,400.00,0.15
2,electronics,5000.00,2500.00,0.10
3,apparel,800.00,300.00,0.15
4,furniture,3000.00,1500.00,0.12
5,electronics,1500.00,800.00,0.10
CSV

chmod +x calculate_margins.py

echo "Setup complete. Silent margins validation prepped."
