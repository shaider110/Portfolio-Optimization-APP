import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Portfolio Advisor App", layout="wide")

st.title("Portfolio Advisor & Stock Tracker")
st.caption("Educational tool only. Not financial advice.")

# ---------------------------
# Helper functions
# ---------------------------

def recommend_allocation(age, risk_tolerance, horizon):
    if risk_tolerance == "Conservative":
        equity = max(20, 100 - age - 20)
    elif risk_tolerance == "Moderate":
        equity = max(30, 110 - age)
    else:
        equity = max(40, 120 - age)

    if horizon < 5:
        equity -= 20
    elif horizon > 15:
        equity += 10

    equity = min(max(equity, 10), 90)
    bonds = 100 - equity - 5
    cash = 5

    if bonds < 0:
        bonds = 0
        cash = 100 - equity

    return {
        "Equity": equity,
        "Bonds / Fixed Income": bonds,
        "Cash": cash
    }


def get_stock_data(tickers, period="1y"):
    data = yf.download(tickers, period=period, auto_adjust=True, progress=False)["Close"]
    if isinstance(data, pd.Series):
        data = data.to_frame()
    return data.dropna()


def portfolio_metrics(prices, weights):
    returns = prices.pct_change().dropna()
    annual_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    expected_return = np.dot(weights, annual_returns)
    volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

    sharpe = expected_return / volatility if volatility != 0 else 0

    return expected_return, volatility, sharpe, returns


def random_portfolios(prices, num_portfolios=3000):
    returns = prices.pct_change().dropna()
    annual_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    results = []

    for _ in range(num_portfolios):
        weights = np.random.random(len(prices.columns))
        weights = weights / np.sum(weights)

        port_return = np.dot(weights, annual_returns)
        port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe = port_return / port_vol if port_vol != 0 else 0

        results.append({
            "Return": port_return,
            "Volatility": port_vol,
            "Sharpe": sharpe,
            "Weights": weights
        })

    return pd.DataFrame(results)


# ---------------------------
# Sidebar
# ---------------------------

st.sidebar.header("Investor Profile")

age = st.sidebar.number_input("Age", min_value=18, max_value=100, value=25)
annual_income = st.sidebar.number_input("Annual Income", min_value=0, value=60000, step=5000)
monthly_savings = st.sidebar.number_input("Monthly Savings", min_value=0, value=1000, step=100)
risk_tolerance = st.sidebar.selectbox("Risk Tolerance", ["Conservative", "Moderate", "Aggressive"])
horizon = st.sidebar.slider("Investment Horizon (Years)", 1, 40, 10)

st.sidebar.header("Stock Portfolio")
ticker_input = st.sidebar.text_input("Enter tickers separated by commas", "AAPL, MSFT, NVDA, SPY")
period = st.sidebar.selectbox("Data Period", ["6mo", "1y", "2y", "5y"], index=1)

tickers = [ticker.strip().upper() for ticker in ticker_input.split(",") if ticker.strip()]

# ---------------------------
# Recommended allocation
# ---------------------------

st.header("1. Recommended Asset Allocation")

allocation = recommend_allocation(age, risk_tolerance, horizon)
allocation_df = pd.DataFrame({
    "Asset Class": list(allocation.keys()),
    "Allocation (%)": list(allocation.values())
})

col1, col2 = st.columns(2)

with col1:
    st.dataframe(allocation_df, use_container_width=True)

with col2:
    fig = px.pie(
        allocation_df,
        names="Asset Class",
        values="Allocation (%)",
        title="Recommended Allocation"
    )
    st.plotly_chart(fig, use_container_width=True)

st.info(
    f"Based on age {age}, {risk_tolerance.lower()} risk tolerance, "
    f"and a {horizon}-year horizon, the model suggests approximately "
    f"{allocation['Equity']}% equity exposure."
)

# ---------------------------
# Stock tracking
# ---------------------------

st.header("2. Stock Tracking")

try:
    prices = get_stock_data(tickers, period)

    st.subheader("Price Data")
    st.dataframe(prices.tail(), use_container_width=True)

    fig_prices = go.Figure()

    normalized_prices = prices / prices.iloc[0] * 100

    for ticker in normalized_prices.columns:
        fig_prices.add_trace(
            go.Scatter(
                x=normalized_prices.index,
                y=normalized_prices[ticker],
                mode="lines",
                name=ticker
            )
        )

    fig_prices.update_layout(
        title="Normalized Price Performance",
        xaxis_title="Date",
        yaxis_title="Growth of $100"
    )

    st.plotly_chart(fig_prices, use_container_width=True)

    # ---------------------------
    # Portfolio metrics
    # ---------------------------

    st.header("3. Portfolio Risk & Return")

    st.write("Set portfolio weights:")

    weights = []
    cols = st.columns(len(tickers))

    for i, ticker in enumerate(tickers):
        weight = cols[i].number_input(
            f"{ticker} Weight (%)",
            min_value=0.0,
            max_value=100.0,
            value=round(100 / len(tickers), 2),
            step=1.0
        )
        weights.append(weight)

    total_weight = sum(weights)

    if total_weight == 0:
        st.warning("Total weight cannot be zero.")
    else:
        weights = np.array(weights) / total_weight

        expected_return, volatility, sharpe, returns = portfolio_metrics(prices, weights)

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric("Expected Annual Return", f"{expected_return:.2%}")
        metric2.metric("Annual Volatility", f"{volatility:.2%}")
        metric3.metric("Sharpe Ratio", f"{sharpe:.2f}")

        st.subheader("Correlation Matrix")
        corr = returns.corr()
        fig_corr = px.imshow(
            corr,
            text_auto=True,
            title="Asset Correlation Matrix"
        )
        st.plotly_chart(fig_corr, use_container_width=True)

    # ---------------------------
    # Portfolio optimization
    # ---------------------------

    st.header("4. Simple Portfolio Optimization")

    if st.button("Run Portfolio Optimization"):
        portfolios = random_portfolios(prices)

        best_portfolio = portfolios.loc[portfolios["Sharpe"].idxmax()]

        st.success("Optimization complete. Highest Sharpe portfolio found.")

        opt_weights = pd.DataFrame({
            "Ticker": prices.columns,
            "Optimal Weight (%)": best_portfolio["Weights"] * 100
        })

        st.dataframe(opt_weights, use_container_width=True)

        fig_frontier = px.scatter(
            portfolios,
            x="Volatility",
            y="Return",
            color="Sharpe",
            title="Random Portfolio Simulation",
            labels={
                "Volatility": "Annual Volatility",
                "Return": "Expected Annual Return"
            }
        )

        fig_frontier.add_trace(
            go.Scatter(
                x=[best_portfolio["Volatility"]],
                y=[best_portfolio["Return"]],
                mode="markers",
                marker=dict(size=14, symbol="star"),
                name="Best Sharpe Portfolio"
            )
        )

        st.plotly_chart(fig_frontier, use_container_width=True)

except Exception as e:
    st.error("Something went wrong while fetching or analyzing data.")
    st.write(e)

st.divider()
st.caption("Built with Streamlit, yfinance, pandas, numpy, and plotly.")
