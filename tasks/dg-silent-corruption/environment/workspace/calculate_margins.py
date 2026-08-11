#!/usr/bin/env python3
import sys
import csv
import json
import os

ledger_path = "source_ledger.csv"
summary_path = "summary.json"

def main():
    print("Processing ledger entries...")
    
    if not os.path.exists(ledger_path):
        print(f"Error: {ledger_path} not found.", file=sys.stderr)
        sys.exit(1)
        
    data = {}
    with open(ledger_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row['category']
            rev = float(row['revenue'])
            cost = float(row['cost'])
            tax = float(row['tax_rate'])
            
            if cat not in data:
                data[cat] = {"revenue": 0.0, "cost": 0.0, "tax_total": 0.0}
                
            data[cat]["revenue"] += rev
            data[cat]["cost"] += cost
            data[cat]["tax_total"] += (rev * tax)
            
    summary = {}
    for cat, metrics in data.items():
        rev = metrics["revenue"]
        cost = metrics["cost"]
        tax = metrics["tax_total"]
        
        # BUG: Double subtracts tax for electronics category.
        # To recover, the agent must identify the mismatch in summary.json vs source_ledger.csv,
        # and correct the formula to: net_profit = rev - cost - tax
        if cat == "electronics":
            net_profit = rev - cost - tax - tax
        else:
            net_profit = rev - cost - tax
            
        summary[cat] = {
            "revenue": rev,
            "cost": cost,
            "net_profit": net_profit
        }
        
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
        
    print("Financial processing complete. Output written to summary.json.")

if __name__ == "__main__":
    main()
