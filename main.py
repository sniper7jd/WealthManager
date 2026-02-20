from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import yfinance as yf
from datetime import date
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def get_db():
    conn = sqlite3.connect("wealth.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY, name TEXT, type TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY, account_id INTEGER, date TEXT, type TEXT, amount REAL, description TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS portfolio (id INTEGER PRIMARY KEY, brokerage TEXT, ticker TEXT, shares REAL, avg_cost REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- DASHBOARD ROUTE ---
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    conn = get_db()
    
    # Calculate Cash
    # Calculate Cash
    cash_data = conn.execute('''
        SELECT transactions.type, SUM(transactions.amount) as total 
        FROM transactions 
        JOIN accounts ON transactions.account_id = accounts.id 
        WHERE accounts.type = 'Bank Account' 
        GROUP BY transactions.type
    ''').fetchall()
    
    total_cash = sum([row['total'] for row in cash_data if row['type'] == 'Deposit']) - sum([row['total'] for row in cash_data if row['type'] == 'Withdrawal'])

    # Calculate Debt
    credit_data = conn.execute('''
        SELECT transactions.type, SUM(transactions.amount) as total 
        FROM transactions 
        JOIN accounts ON transactions.account_id = accounts.id 
        WHERE accounts.type = 'Credit Card' 
        GROUP BY transactions.type
    ''').fetchall()
    
    total_debt = sum([row['total'] for row in credit_data if row['type'] == 'Debit']) - sum([row['total'] for row in credit_data if row['type'] == 'Credit'])
    # Calculate Portfolio
    portfolio = conn.execute("SELECT * FROM portfolio").fetchall()
    total_invested = 0.0
    if portfolio:
        tickers = list(set([row['ticker'] for row in portfolio]))
        try:
            live_data = yf.download(tickers, period="1d", progress=False)['Close']
            for row in portfolio:
                t = row['ticker']
                price = float(live_data.iloc[-1]) if len(tickers) == 1 else float(live_data[t].iloc[-1])
                total_invested += price * row['shares']
        except:
            total_invested = sum([row['shares'] * row['avg_cost'] for row in portfolio])

    net_worth = total_cash - total_debt + total_invested
    accounts = conn.execute("SELECT * FROM accounts").fetchall()
    conn.close()

    return templates.TemplateResponse("dashboard.html", {
        "request": request, "net_worth": f"{net_worth:,.2f}", "total_cash": f"{total_cash:,.2f}",
        "total_debt": f"{total_debt:,.2f}", "total_invested": f"{total_invested:,.2f}", "accounts": accounts,
        "chart_history": [net_worth * 0.9, net_worth * 0.95, net_worth * 0.98, net_worth * 1.02, net_worth]
    })

# --- ACCOUNT ROUTES ---
@app.post("/add_account")
async def add_account(name: str = Form(...), type: str = Form(...)):
    conn = get_db()
    conn.execute("INSERT INTO accounts (name, type) VALUES (?, ?)", (name, type))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/", status_code=303)

@app.get("/account/{account_id}", response_class=HTMLResponse)
async def view_account(request: Request, account_id: int):
    conn = get_db()
    account = conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
    txs = conn.execute("SELECT * FROM transactions WHERE account_id=? ORDER BY date DESC", (account_id,)).fetchall()
    
    # Calculate specific account balance
    bal = 0.0
    for tx in txs:
        if tx['type'] in ['Deposit', 'Debit']: bal += tx['amount']
        else: bal -= tx['amount']
        
    conn.close()
    return templates.TemplateResponse("account.html", {"request": request, "account": account, "transactions": txs, "balance": f"{bal:,.2f}"})

@app.post("/account/{account_id}/transaction")
async def add_transaction(account_id: int, type: str = Form(...), amount: float = Form(...), description: str = Form(...)):
    conn = get_db()
    conn.execute("INSERT INTO transactions (account_id, date, type, amount, description) VALUES (?, ?, ?, ?, ?)", 
                 (account_id, date.today().isoformat(), type, amount, description))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/account/{account_id}", status_code=303)

@app.post("/account/{account_id}/delete")
async def delete_account(account_id: int):
    conn = get_db()
    conn.execute("DELETE FROM accounts WHERE id=?", (account_id,))
    conn.execute("DELETE FROM transactions WHERE account_id=?", (account_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/", status_code=303)

# --- PORTFOLIO ROUTES ---
@app.get("/portfolio", response_class=HTMLResponse)
async def view_portfolio(request: Request):
    conn = get_db()
    portfolio = conn.execute("SELECT * FROM portfolio").fetchall()
    conn.close()
    return templates.TemplateResponse("portfolio.html", {"request": request, "portfolio": portfolio})

@app.post("/add_holding")
async def add_holding(brokerage: str = Form(...), ticker: str = Form(...), shares: float = Form(...), avg_cost: float = Form(...)):
    conn = get_db()
    conn.execute("INSERT INTO portfolio (brokerage, ticker, shares, avg_cost) VALUES (?, ?, ?, ?)", 
                 (brokerage, ticker.upper(), shares, avg_cost))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/portfolio", status_code=303)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)