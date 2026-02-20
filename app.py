import streamlit as st
import pandas as pd
import yfinance as yf
import os
from datetime import date

st.set_page_config(page_title="Wealth Command", layout="wide")

# --- 1. Database Engine ---
FILES = {"accounts": "accounts.csv", "txs": "transactions.csv", "portfolio": "portfolio.csv"}

def load_data(key, cols):
    if os.path.exists(FILES[key]): return pd.read_csv(FILES[key])
    return pd.DataFrame(columns=cols)

def save_data(key):
    st.session_state[key].to_csv(FILES[key], index=False)

if "accounts" not in st.session_state:
    st.session_state.accounts = load_data("accounts", ["Account Name", "Type"])
    st.session_state.txs = load_data("txs", ["Date", "Account Name", "Type", "Amount", "Description"])
    st.session_state.portfolio = load_data("portfolio", ["Ticker", "Shares", "Avg Cost"])

# --- 2. Core Calculations ---
txs = st.session_state.txs
accounts = st.session_state.accounts
port = st.session_state.portfolio

# Bank Cash (Deposits - Withdrawals)
bank_names = accounts[accounts["Type"] == "Bank Account"]["Account Name"].tolist()
bank_txs = txs[txs["Account Name"].isin(bank_names)]
total_cash = bank_txs[bank_txs["Type"] == "Deposit"].Amount.astype(float).sum() - bank_txs[bank_txs["Type"] == "Withdrawal"].Amount.astype(float).sum()

# Credit Debt (Debits - Credits)
credit_names = accounts[accounts["Type"] == "Credit Card"]["Account Name"].tolist()
credit_txs = txs[txs["Account Name"].isin(credit_names)]
total_debt = credit_txs[credit_txs["Type"] == "Debit"].Amount.astype(float).sum() - credit_txs[credit_txs["Type"] == "Credit"].Amount.astype(float).sum()

# Portfolio Value
total_invested = 0.0
live_prices = {}
if not port.empty:
    tickers = port["Ticker"].unique().tolist()
    try:
        live_data = yf.download(tickers, period="1d", progress=False)['Close']
        for t in tickers:
            price = float(live_data.iloc[-1]) if len(tickers) == 1 else float(live_data[t].iloc[-1])
            live_prices[t] = price
            total_invested += price * float(port.loc[port["Ticker"] == t, "Shares"].values[0])
    except Exception:
        total_invested = (port["Shares"].astype(float) * port["Avg Cost"].astype(float)).sum()

net_worth = total_cash - total_debt + total_invested

# --- 3. Persistent Top Header ---
st.title("💠 Wealth Command Center")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Net Worth", f"${net_worth:,.2f}")
c2.metric("Total Cash", f"${total_cash:,.2f}")
c3.metric("Credit Debt", f"${total_debt:,.2f}", delta="Liabilities", delta_color="inverse")
c4.metric("Market Assets", f"${total_invested:,.2f}")
st.markdown("___")

# --- 4. Interactive Application Tabs ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🏦 Banking & Ledgers", "📈 Portfolio & Insights"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.subheader("Asset Allocation")
    if net_worth != 0 or total_debt != 0:
        chart_data = pd.DataFrame({
            "Category": ["Cash", "Investments", "Credit Debt"], 
            "Balance": [total_cash, total_invested, -total_debt]
        }).set_index("Category")
        st.bar_chart(chart_data, height=300)
    else:
        st.info("Log transactions or add stock positions to generate your dashboard.")

# --- TAB 2: BANKING & LEDGERS ---
with tab2:
    col_acc, col_tx = st.columns([1, 2])
    
    with col_acc:
        st.subheader("1. Manage Accounts")
        st.write("Add, rename, or delete accounts here.")
        edited_accs = st.data_editor(
            st.session_state.accounts, 
            num_rows="dynamic", 
            key="acc_editor",
            column_config={"Type": st.column_config.SelectboxColumn(options=["Bank Account", "Credit Card"], required=True)}
        )
        if st.button("Save Account Changes"):
            st.session_state.accounts = edited_accs
            save_data("accounts")
            st.success("Accounts updated!")
            st.rerun()

    with col_tx:
        st.subheader("2. Master Ledger")
        st.write("Double-click to edit typos, or select a row and press Delete to remove a transaction.")
        
        # Dynamic dropdown for the ledger editor based on current accounts
        valid_accounts = st.session_state.accounts["Account Name"].tolist()
        
        edited_txs = st.data_editor(
            st.session_state.txs,
            num_rows="dynamic",
            key="tx_editor",
            column_config={
                "Account Name": st.column_config.SelectboxColumn(options=valid_accounts, required=True),
                "Type": st.column_config.SelectboxColumn(options=["Deposit", "Withdrawal", "Debit", "Credit"], required=True),
                "Amount": st.column_config.NumberColumn(min_value=0.0, format="$%.2f", required=True)
            }
        )
        if st.button("Save Ledger Edits"):
            st.session_state.txs = edited_txs
            save_data("txs")
            st.success("Ledger updated!")
            st.rerun()

# --- TAB 3: PORTFOLIO & INSIGHTS ---
with tab3:
    st.subheader("Equity Holdings")
    st.write("Add new tickers, update your average costs, or sell out of positions.")
    
    edited_port = st.data_editor(
        st.session_state.portfolio,
        num_rows="dynamic",
        key="port_editor",
        column_config={
            "Ticker": st.column_config.TextColumn(required=True),
            "Shares": st.column_config.NumberColumn(min_value=0.0, step=1.0, required=True),
            "Avg Cost": st.column_config.NumberColumn(min_value=0.0, format="$%.2f", required=True)
        },
        use_container_width=True
    )
    if st.button("Save Portfolio Changes"):
        st.session_state.portfolio = edited_port
        save_data("portfolio")
        st.success("Portfolio updated!")
        st.rerun()
        
    st.markdown("___")
    st.subheader("Live Market Insights")
    
    if not st.session_state.portfolio.empty:
        # Create a dropdown to select a stock from your portfolio to analyze
        insight_ticker = st.selectbox("Select a holding to view historical performance:", st.session_state.portfolio["Ticker"].unique())
        
        if insight_ticker:
            try:
                # Fetch 6 months of historical data
                hist_data = yf.Ticker(insight_ticker).history(period="6mo")
                if not hist_data.empty:
                    st.line_chart(hist_data['Close'], height=250)
                    
                    # Display quick stats underneath the graph
                    c_price = live_prices.get(insight_ticker, 0)
                    avg_cost = st.session_state.portfolio[st.session_state.portfolio["Ticker"] == insight_ticker]["Avg Cost"].values[0]
                    shares = st.session_state.portfolio[st.session_state.portfolio["Ticker"] == insight_ticker]["Shares"].values[0]
                    
                    p_l = (c_price - avg_cost) * shares
                    
                    st.write(f"**Current Price:** ${c_price:,.2f} | **Your Avg Cost:** ${avg_cost:,.2f} | **Total P/L:** ${p_l:,.2f}")
            except Exception as e:
                st.warning(f"Could not load graph for {insight_ticker}: {e}")
    else:
        st.info("Add a stock above to unlock live market insights.")