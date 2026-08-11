#!/usr/bin/env bash
set -euo pipefail

echo "Staging report files..."
mkdir -p reports

# Create standard report
echo "February Metrics: Revenue increased by 8%." > reports/February.txt

# Create report containing space in its name
echo "March Close Metrics: Variance audit complete. Balance sheet reconciled." > "reports/March Close.txt"

chmod +x aggregate.sh

echo "Setup complete. Reports directory staged with space-containing filename."
