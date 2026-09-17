# CashFlow AI

A local desktop finance dashboard built with Python and CustomTkinter.

This repository preserves the original GitHub project history while adding the current CashFlow AI desktop application and local data model.

## Project history

The original project on GitHub was a Python-based finance and cash-flow analysis project focused on:

- income and expense analysis
- cash flow tracking
- monthly financial summaries
- financial data visualisation
- practical data analysis workflows

The original notebook and analysis script are retained in this branch so the existing GitHub history remains intact.

## Project structure

- `app/` — modular desktop application logic
- `data/` — local JSON finance storage
- `reports/` — report output folder
- `cashflow_analysis.py` — original project analysis script
- `finance_cashflow_analysis.ipynb` — original notebook from the GitHub repository
- `tests/` — automated regression tests

## Features

- Editable finance sections for:
  - Bank accounts
  - Savings
  - Credit cards
  - Loans
  - Investments
  - Income
  - Fixed expenses
  - Direct debits
  - Payments completed
  - Payments pending
  - Goals with target, current, remaining and progress bar
- Dashboard summary with:
  - Total assets
  - Total available cash
  - Total savings
  - Total investments
  - Total debt
  - Total loans
  - Goals target/progress/remaining
  - Upcoming critical payments
  - Safe to spend until next payday
  - Financial status: Green, Amber or Red
- All data is saved locally in JSON.
- Uses GBP values and local-editable forms.

## Run locally

```bash
python3 main.py
```

The app will use the local project data files and can bootstrap a local Python environment when needed.

## Data privacy

The local financial data files are intentionally excluded from version control and remain private.

