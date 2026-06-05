import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="AI Wealth Advisor", layout="wide")

st.title("AI-Powered Wealth & Portfolio Advisor")
st.caption("Educational prototype only. Not financial advice.")

# ---------------------------
# Helper Functions
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
    bonds = max(0, 100 - equity - 5)
    cash = 100 - equity - bonds

    return {"Equity": equity, "Bonds / Fixed Income": bonds, "Cash": cash}


def risk_score(age, risk_tolerance, horizon, monthly_savings, annual_income):
    score = 50

    if age < 30:
        score += 15
    elif age > 55:
        score -= 15

    if risk_tolerance == "Aggressive":
        score += 20
    elif risk_tolerance == "Conservative":
        score -= 20

    if horizon > 15:
        score += 15
    elif horizon < 5:
        score -= 15

    savings_rate = (monthly_savings * 12) / annual_income if annual_income > 0 else 0
    if savings_rate > 0.25:
        score += 10
    elif savings_rate < 0.10:
        score -= 10

    return int(min(max(score, 0), 100))


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


def portfolio_health_score(num_assets, volatility, sharpe):
    score = 50

    if num_assets >= 5:
        score += 15
    elif num_assets <= 2:
        score -= 15

    if volatility < 0.20:
        score += 15
    elif volatility > 0.35:
        score -= 15

    if sharpe > 1:
        score += 20
    elif sharpe < 0.3:
        score -= 10

    return int(min(max(score, 0), 100))


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


def future_value_projection(current_savings, monthly_savings, annual_return, years):
    months = years * 12
    monthly_return = annual_return / 12

    values = []
    portfolio_value = current_savings

    for month in range(months + 1):
        values.append({
            "Month": month,
            "Year": month / 12,
            "Projected Value": portfolio_value
        })
        portfolio_value = portfolio_value * (1 + monthly_return) + monthly_savings

    return pd.DataFrame(values)


def monte_carlo_simulation(start_value, monthly_savings, expected_return, volatility, years, simulations=500):
    months = years * 12
    monthly_return = expected_return / 12
    monthly_volatility = volatility / np.sqrt(12)

    all_paths = []

    for sim in range(simulations):
        value = start_value
        path = []

        for month in range(months + 1):
            path.append(value)
            random_return = np.random.normal(monthly_return, monthly_volatility)
            value = value * (1 + random_return) + monthly_savings

        all_paths.append(path)

    return pd.DataFrame(all_paths).T


def stress_test(weights, tickers):
    scenarios = {
        "COVID-style market shock": -0.20,
        "2022 inflation/rate shock": -0.18,
        "Mild recession": -0.10,
        "Strong bull market": 0.15
    }

    results = []
    for scenario, shock in scenarios.items():
        estimated_return = shock * np.sum(weights)
        results.append({
            "Scenario": scenario,
            "Estimated Portfolio Impact": estimated_return
        })

    return pd.DataFrame(results)


def hedging_suggestions(tickers, volatility):
    suggestions = []

    tech_names = ["AAPL", "MSFT", "NVDA", "TSLA", "META", "GOOGL", "AMZN"]
    tech_count = sum([1 for t in tickers if t in tech_names])

    if tech_count >= 3:
        suggestions.append("High technology concentration detected. Consider adding broad-market ETFs, bonds, or defensive assets.")

    if volatility > 0.30:
        suggestions.append("Portfolio volatility is high. Possible hedges include BND, TLT, GLD, or reducing concentrated equity exposure.")

    if "SPY" not in tickers and "VOO" not in tickers:
        suggestions.append("Consider adding a diversified market ETF such as SPY or VOO.")

    if "GLD" not in tickers:
        suggestions.append("Gold ETF exposure such as GLD can act as a defensive hedge during market stress.")

    if len(suggestions) == 0:
        suggestions.append("Portfolio risk appears reasonable based on current inputs.")

    return suggestions


# ---------------------------
# Sidebar Inputs
# ---------------------------

st.sidebar.header("Investor Profile")

age = st.sidebar.number_input("Age", min_value=18, max_value=100, value=25)
annual_income = st.sidebar.number_input("Annual Income", min_value=0, value=60000, step=5000)
current_savings = st.sidebar.number_input("Current Savings", min_value=0, value=10000, step=1000)
monthly_savings = st.sidebar.number_input("Monthly Savings", min_value=0, value=1000, step=100)
risk_tolerance = st.sidebar.selectbox("Risk Tolerance", ["Conservative", "Moderate", "Aggressive"])
horizon = st.sidebar.slider("Investment Horizon (Years)", 1, 40, 10)

st.sidebar.header("Portfolio")
ticker_input = st.sidebar.text_input("Enter tickers separated by commas", "AAPL, MSFT, NVDA, SPY")
period = st.sidebar.selectbox("Data Period", ["6mo", "1y", "2y", "5y"], index=1)

tickers = [ticker.strip().upper() for ticker in ticker_input.split(",") if ticker.strip()]

# ---------------------------
# Investor Profile
# ---------------------------

st.header("1. Investor Profile & AI Recommendation")

allocation = recommend_allocation(age, risk_tolerance, horizon)
score = risk_score(age, risk_tolerance, horizon, monthly_savings, annual_income)

col1, col2, col3 = st.columns(3)
col1.metric("Risk Score", f"{score}/100")
col2.metric("Investor Type", risk_tolerance)
col3.metric("Investment Horizon", f"{horizon} years")

allocation_df = pd.DataFrame({
    "Asset Class": list(allocation.keys()),
    "Allocation (%)": list(allocation.values())
})

c1, c2 = st.columns(2)

with c1:
    st.dataframe(allocation_df, use_container_width=True)

with c2:
    fig_alloc = px.pie(allocation_df, names="Asset Class", values="Allocation (%)", title="Recommended Asset Allocation")
    st.plotly_chart(fig_alloc, use_container_width=True)

st.info(
    f"AI-style insight: Based on your age, {risk_tolerance.lower()} risk profile, "
    f"and {horizon}-year horizon, the model recommends {allocation['Equity']}% equity exposure. "
    f"This suggests a portfolio focused on growth while keeping some allocation in fixed income and cash."
)

# ---------------------------
# Future Wealth Projection
# ---------------------------

st.header("2. Future Wealth Projection")

assumed_return = st.slider("Assumed Annual Return (%)", 1, 15, 7) / 100

projection = future_value_projection(current_savings, monthly_savings, assumed_return, horizon)

final_value = projection["Projected Value"].iloc[-1]

st.metric("Projected Portfolio Value", f"${final_value:,.0f}")

fig_projection = px.line(
    projection,
    x="Year",
    y="Projected Value",
    title="Projected Wealth Growth"
)
st.plotly_chart(fig_projection, use_container_width=True)

# ---------------------------
# Stock Data
# ---------------------------

st.header("3. Stock Tracking & Benchmark Comparison")

try:
    prices = get_stock_data(tickers, period)

    st.subheader("Latest Price Data")
    st.dataframe(prices.tail(), use_container_width=True)

    normalized = prices / prices.iloc[0] * 100

    fig_prices = go.Figure()

    for ticker in normalized.columns:
        fig_prices.add_trace(go.Scatter(x=normalized.index, y=normalized[ticker], mode="lines", name=ticker))

    benchmark = get_stock_data(["SPY"], period)
    benchmark_norm = benchmark / benchmark.iloc[0] * 100

    fig_prices.add_trace(go.Scatter(
        x=benchmark_norm.index,
        y=benchmark_norm["SPY"],
        mode="lines",
        name="Benchmark: SPY",
        line=dict(dash="dash")
    ))

    fig_prices.update_layout(
        title="Normalized Performance vs S&P 500 ETF",
        xaxis_title="Date",
        yaxis_title="Growth of $100"
    )

    st.plotly_chart(fig_prices, use_container_width=True)

    # ---------------------------
    # Portfolio Risk & Return
    # ---------------------------

    st.header("4. Portfolio Risk & Return")

    st.write("Set your portfolio weights:")

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
        st.warning("Total portfolio weight cannot be zero.")
    else:
        weights = np.array(weights) / total_weight

        expected_return, volatility, sharpe, returns = portfolio_metrics(prices, weights)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Expected Annual Return", f"{expected_return:.2%}")
        m2.metric("Annual Volatility", f"{volatility:.2%}")
        m3.metric("Sharpe Ratio", f"{sharpe:.2f}")
        m4.metric("Portfolio Health Score", f"{portfolio_health_score(len(tickers), volatility, sharpe)}/100")

        st.subheader("Correlation Matrix")
        corr = returns.corr()
        fig_corr = px.imshow(corr, text_auto=True, title="Asset Correlation Matrix")
        st.plotly_chart(fig_corr, use_container_width=True)

        # ---------------------------
        # Monte Carlo Simulation
        # ---------------------------

        st.header("5. Monte Carlo Simulation")

        if st.button("Run Monte Carlo Simulation"):
            mc = monte_carlo_simulation(
                current_savings,
                monthly_savings,
                expected_return,
                volatility,
                horizon,
                simulations=500
            )

            final_values = mc.iloc[-1]

            st.write("Simulation Results")
            c1, c2, c3 = st.columns(3)
            c1.metric("Worst Case 10th Percentile", f"${np.percentile(final_values, 10):,.0f}")
            c2.metric("Median Outcome", f"${np.percentile(final_values, 50):,.0f}")
            c3.metric("Best Case 90th Percentile", f"${np.percentile(final_values, 90):,.0f}")

            fig_mc = go.Figure()

            for i in range(min(50, mc.shape[1])):
                fig_mc.add_trace(go.Scatter(
                    y=mc.iloc[:, i],
                    mode="lines",
                    opacity=0.25,
                    showlegend=False
                ))

            fig_mc.update_layout(
                title="Monte Carlo Portfolio Simulation",
                xaxis_title="Months",
                yaxis_title="Portfolio Value"
            )

            st.plotly_chart(fig_mc, use_container_width=True)

        # ---------------------------
        # Optimization
        # ---------------------------

        st.header("6. Portfolio Optimization")

        if st.button("Run Portfolio Optimization"):
            portfolios = random_portfolios(prices)

            best_portfolio = portfolios.loc[portfolios["Sharpe"].idxmax()]
            min_vol_portfolio = portfolios.loc[portfolios["Volatility"].idxmin()]

            st.success("Optimization complete.")

            opt_weights = pd.DataFrame({
                "Ticker": prices.columns,
                "Max Sharpe Weight (%)": best_portfolio["Weights"] * 100,
                "Min Volatility Weight (%)": min_vol_portfolio["Weights"] * 100
            })

            st.dataframe(opt_weights, use_container_width=True)

            fig_frontier = px.scatter(
                portfolios,
                x="Volatility",
                y="Return",
                color="Sharpe",
                title="Efficient Frontier Simulation",
                labels={"Volatility": "Annual Volatility", "Return": "Expected Annual Return"}
            )

            fig_frontier.add_trace(go.Scatter(
                x=[best_portfolio["Volatility"]],
                y=[best_portfolio["Return"]],
                mode="markers",
                marker=dict(size=14, symbol="star"),
                name="Max Sharpe"
            ))

            fig_frontier.add_trace(go.Scatter(
                x=[min_vol_portfolio["Volatility"]],
                y=[min_vol_portfolio["Return"]],
                mode="markers",
                marker=dict(size=14, symbol="diamond"),
                name="Min Volatility"
            ))

            st.plotly_chart(fig_frontier, use_container_width=True)

        # ---------------------------
        # Hedging & Stress Testing
        # ---------------------------

        st.header("7. Risk Management, Hedging & Stress Testing")

        st.subheader("Hedging Suggestions")

        suggestions = hedging_suggestions(tickers, volatility)

        for s in suggestions:
            st.write(f"- {s}")

        st.subheader("Stress Test Scenarios")

        stress_df = stress_test(weights, tickers)
        stress_df["Estimated Portfolio Impact"] = stress_df["Estimated Portfolio Impact"].apply(lambda x: f"{x:.2%}")

        st.dataframe(stress_df, use_container_width=True)

        st.warning(
            "The hedging and stress testing module is simplified for educational purposes. "
            "A real platform would require deeper risk modeling, live options data, and regulatory suitability checks."
        )

except Exception as e:
    st.error("Something went wrong while fetching or analyzing market data.")
    st.write(e)

st.divider()
st.caption("Built with Streamlit, yfinance, pandas, numpy, and plotly.")
