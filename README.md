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
pip install fastapi uvicorn yfinance jinja2
```

## Run

```bash
python main.py
```

Open http://127.0.0.1:8000

## Tech

- FastAPI, Jinja2, SQLite, Yahoo Finance (yfinance)
