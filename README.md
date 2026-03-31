# WealthManager

A personal wealth tracking app built with FastAPI. Track bank accounts, credit cards, and investment portfolios with live stock prices from Yahoo Finance.

## Features

- **Dashboard** — Net worth, liquid cash, credit debt, and market portfolio with color-coded balances
- **Bank Accounts & Credit Cards** — Add accounts, log transactions (Debit/Credit for bank, Expense/Refund/Payment for credit cards)
- **Investment Portfolio** — Track holdings by brokerage, ticker, shares, and cost basis
- **Portfolio Emulator** — Add stocks with ticker autocomplete, live prices, gain/loss tracking, and price charts

## Setup

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Open http://127.0.0.1:8000

## Tech

- FastAPI, Jinja2, SQLite, Yahoo Finance (yfinance)

## Compatibility Notes

- Dependencies are pinned to compatible version ranges in `requirements.txt` to avoid FastAPI/Starlette breakages across machines.
- If you already have an older environment, recreate it:

```bash
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
