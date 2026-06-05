import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="FinPilot AI", layout="wide")

# ---------------------------
# Styling
# ---------------------------

st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}
.big-title {
    font-size: 44px;
    font-weight: 800;
    color: #F9FAFB;
}
.subtitle {
    font-size: 18px;
    color: #9CA3AF;
    margin-bottom: 25px;
}
.section-card {
    background: linear-gradient(135deg, #111827, #1F2937);
    padding: 18px;
    border-radius: 18px;
    border: 1px solid #374151;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">FinPilot AI</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">AI-powered robo-advisory, portfolio analytics, optimization, and hedging intelligence.</div>',
    unsafe_allow_html=True
)

st.caption("Educational prototype only. Not financial advice.")

# ---------------------------
# Helper Functions
# ---------------------------

def apply_dark_theme(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F9FAFB")
    )
    return fig


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


def future_value_projection(current_savings, monthly_savings, annual_return, years):
    months = years * 12
    monthly_return = annual_return / 12
    portfolio_value = current_savings
    values = []

    for month in range(months + 1):
        values.append({
            "Month": month,
            "Year": month / 12,
            "Projected Value": portfolio_value
        })
        portfolio_value = portfolio_value * (1 + monthly_return) + monthly_savings

    return pd.DataFrame(values)


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


def monte_carlo_simulation(start_value, monthly_savings, expected_return, volatility, years, simulations=500):
    months = years * 12
    monthly_return = expected_return / 12
    monthly_volatility = volatility / np.sqrt(12)

    all_paths = []

    for _ in range(simulations):
        value = start_value
        path = []

        for _ in range(months + 1):
            path.append(value)
            random_return = np.random.normal(monthly_return, monthly_volatility)
            value = value * (1 + random_return) + monthly_savings

        all_paths.append(path)

    return pd.DataFrame(all_paths).T


def calculate_var(returns, portfolio_value, confidence=0.95):
    portfolio_returns = returns.mean(axis=1)
    var_percent = np.percentile(portfolio_returns, (1 - confidence) * 100)
    var_amount = portfolio_value * abs(var_percent)
    return var_percent, var_amount


def calculate_portfolio_beta(prices, weights, period):
    benchmark = get_stock_data(["SPY"], period)

    combined = prices.join(benchmark, how="inner", rsuffix="_benchmark")
    returns = combined.pct_change().dropna()

    portfolio_returns = returns[prices.columns].dot(weights)
    benchmark_returns = returns["SPY"]

    covariance = np.cov(portfolio_returns, benchmark_returns)[0][1]
    variance = np.var(benchmark_returns)

    beta = covariance / variance if variance != 0 else 0
    return beta


def hedge_portfolio_analysis(prices, weights, portfolio_value, period):
    current_return, current_vol, current_sharpe, returns = portfolio_metrics(prices, weights)

    hedge_assets = ["BND", "GLD"]
    hedge_data = get_stock_data(hedge_assets, period)

    combined_prices = prices.join(hedge_data, how="inner")

    if combined_prices.empty:
        return None

    hedge_weights = np.array(list(weights * 0.80) + [0.10, 0.10])
    hedge_weights = hedge_weights / hedge_weights.sum()

    hedged_return, hedged_vol, hedged_sharpe, hedged_returns = portfolio_metrics(combined_prices, hedge_weights)

    current_var_pct, current_var_amount = calculate_var(returns, portfolio_value)
    hedged_var_pct, hedged_var_amount = calculate_var(hedged_returns, portfolio_value)

    comparison = pd.DataFrame({
        "Metric": [
            "Expected Annual Return",
            "Annual Volatility",
            "Sharpe Ratio",
            "Daily 95% VaR"
        ],
        "Current Portfolio": [
            f"{current_return:.2%}",
            f"{current_vol:.2%}",
            f"{current_sharpe:.2f}",
            f"${current_var_amount:,.0f}"
        ],
        "Hedged Portfolio": [
            f"{hedged_return:.2%}",
            f"{hedged_vol:.2%}",
            f"{hedged_sharpe:.2f}",
            f"${hedged_var_amount:,.0f}"
        ]
    })

    hedge_weights_df = pd.DataFrame({
        "Asset": list(prices.columns) + hedge_assets,
        "Hedged Weight (%)": hedge_weights * 100
    })

    return comparison, hedge_weights_df


def enhanced_ai_recommendation(age, risk_tolerance, horizon, score, expected_return, volatility, sharpe, allocation):
    recs = []

    recs.append(
        f"Your risk score is {score}/100, which places you in a {risk_tolerance.lower()} investor profile."
    )

    if horizon >= 10:
        recs.append(
            "Your long investment horizon supports higher equity exposure because you have more time to absorb market volatility."
        )
    else:
        recs.append(
            "Your shorter horizon means capital protection becomes more important, so the model favors more defensive allocation."
        )

    if volatility > 0.30:
        recs.append(
            "Your current portfolio volatility is high. The app suggests adding defensive assets such as bonds, gold, or broad-market ETFs."
        )
    elif volatility < 0.15:
        recs.append(
            "Your portfolio volatility is low. This can reduce risk, but it may also limit long-term growth potential."
        )
    else:
        recs.append(
            "Your portfolio volatility appears balanced for a diversified investment strategy."
        )

    if sharpe > 1:
        recs.append(
            "Your Sharpe ratio is strong, meaning the portfolio is producing attractive return relative to its risk."
        )
    elif sharpe < 0.5:
        recs.append(
            "Your Sharpe ratio is weak, meaning the portfolio may not be efficiently rewarding you for the risk taken."
        )
    else:
        recs.append(
            "Your Sharpe ratio is reasonable, but diversification and optimization may improve risk-adjusted returns."
        )

    recs.append(
        f"The strategic allocation recommendation is {allocation['Equity']}% equities, "
        f"{allocation['Bonds / Fixed Income']}% fixed income, and {allocation['Cash']}% cash."
    )

    return recs


def stress_test(weights):
    scenarios = {
        "COVID-style market shock": -0.20,
        "2022 inflation and rate shock": -0.18,
        "Mild recession": -0.10,
        "Strong bull market": 0.15
    }

    results = []

    for scenario, shock in scenarios.items():
        estimated_return = shock * np.sum(weights)
        results.append({
            "Scenario": scenario,
            "Estimated Portfolio Impact": f"{estimated_return:.2%}"
        })

    return pd.DataFrame(results)


# ---------------------------
# Sidebar
# ---------------------------

st.sidebar.title("Control Center")

st.sidebar.header("Investor Inputs")
age = st.sidebar.number_input("Age", min_value=18, max_value=100, value=25)
annual_income = st.sidebar.number_input("Annual Income", min_value=0, value=60000, step=5000)
current_savings = st.sidebar.number_input("Current Savings", min_value=0, value=10000, step=1000)
monthly_savings = st.sidebar.number_input("Monthly Savings", min_value=0, value=1000, step=100)
risk_tolerance = st.sidebar.selectbox("Risk Tolerance", ["Conservative", "Moderate", "Aggressive"])
horizon = st.sidebar.slider("Investment Horizon", 1, 40, 10)

st.sidebar.header("Portfolio Inputs")
ticker_input = st.sidebar.text_input("Tickers", "AAPL, MSFT, NVDA, SPY")
period = st.sidebar.selectbox("Market Data Period", ["6mo", "1y", "2y", "5y"], index=1)

tickers = [ticker.strip().upper() for ticker in ticker_input.split(",") if ticker.strip()]

allocation = recommend_allocation(age, risk_tolerance, horizon)
score = risk_score(age, risk_tolerance, horizon, monthly_savings, annual_income)

# ---------------------------
# Main App
# ---------------------------

try:
    prices = get_stock_data(tickers, period)

    normalized = prices / prices.iloc[0] * 100

    weights_equal = np.array([1 / len(tickers)] * len(tickers))
    expected_return, volatility, sharpe, returns = portfolio_metrics(prices, weights_equal)

    health_score = portfolio_health_score(len(tickers), volatility, sharpe)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Risk Score", f"{score}/100")
    c2.metric("Expected Return", f"{expected_return:.2%}")
    c3.metric("Volatility", f"{volatility:.2%}")
    c4.metric("Sharpe Ratio", f"{sharpe:.2f}")

    tab_profile, tab_market, tab_portfolio, tab_ai, tab_risk = st.tabs([
        "Investor Intelligence",
        "Market Dashboard",
        "Portfolio Analytics",
        "AI Advisor",
        "Risk & Hedging Lab"
    ])

    # ---------------------------
    # Investor Intelligence
    # ---------------------------

    with tab_profile:
        st.subheader("Investor Intelligence")

        allocation_df = pd.DataFrame({
            "Asset Class": list(allocation.keys()),
            "Allocation (%)": list(allocation.values())
        })

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Recommended Strategic Allocation")
            st.dataframe(allocation_df, use_container_width=True)

        with col2:
            fig_alloc = px.pie(
                allocation_df,
                names="Asset Class",
                values="Allocation (%)",
                hole=0.45,
                title="Robo-Advisor Allocation"
            )
            fig_alloc = apply_dark_theme(fig_alloc)
            st.plotly_chart(fig_alloc, use_container_width=True)

        st.markdown("### Future Wealth Projection")

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
        fig_projection = apply_dark_theme(fig_projection)
        st.plotly_chart(fig_projection, use_container_width=True)

    # ---------------------------
    # Market Dashboard
    # ---------------------------

    with tab_market:
        st.subheader("Market Dashboard")

        st.markdown("### Latest Price Data")
        st.dataframe(prices.tail(), use_container_width=True)

        fig_prices = go.Figure()

        for ticker in normalized.columns:
            fig_prices.add_trace(
                go.Scatter(
                    x=normalized.index,
                    y=normalized[ticker],
                    mode="lines",
                    name=ticker
                )
            )

        benchmark = get_stock_data(["SPY"], period)
        benchmark_norm = benchmark / benchmark.iloc[0] * 100

        fig_prices.add_trace(
            go.Scatter(
                x=benchmark_norm.index,
                y=benchmark_norm["SPY"],
                mode="lines",
                name="Benchmark: SPY",
                line=dict(dash="dash")
            )
        )

        fig_prices.update_layout(
            title="Growth of $100 vs S&P 500 ETF",
            xaxis_title="Date",
            yaxis_title="Indexed Value"
        )

        fig_prices = apply_dark_theme(fig_prices)
        st.plotly_chart(fig_prices, use_container_width=True)

    # ---------------------------
    # Portfolio Analytics
    # ---------------------------

    with tab_portfolio:
        st.subheader("Portfolio Analytics")

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
            weights = weights_equal
        else:
            weights = np.array(weights) / total_weight

        expected_return, volatility, sharpe, returns = portfolio_metrics(prices, weights)
        health_score = portfolio_health_score(len(tickers), volatility, sharpe)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Expected Annual Return", f"{expected_return:.2%}")
        m2.metric("Annual Volatility", f"{volatility:.2%}")
        m3.metric("Sharpe Ratio", f"{sharpe:.2f}")
        m4.metric("Portfolio Health Score", f"{health_score}/100")

        st.markdown("### Correlation Matrix")

        corr = returns.corr()
        fig_corr = px.imshow(
            corr,
            text_auto=True,
            title="Asset Correlation Matrix",
            color_continuous_scale="RdBu"
        )
        fig_corr = apply_dark_theme(fig_corr)
        st.plotly_chart(fig_corr, use_container_width=True)

        st.markdown("### Optimization Studio")

        if st.button("Run Portfolio Optimization"):
            portfolios = random_portfolios(prices)

            best_portfolio = portfolios.loc[portfolios["Sharpe"].idxmax()]
            min_vol_portfolio = portfolios.loc[portfolios["Volatility"].idxmin()]

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
                    marker=dict(size=16, symbol="star"),
                    name="Max Sharpe"
                )
            )

            fig_frontier.add_trace(
                go.Scatter(
                    x=[min_vol_portfolio["Volatility"]],
                    y=[min_vol_portfolio["Return"]],
                    mode="markers",
                    marker=dict(size=14, symbol="diamond"),
                    name="Min Volatility"
                )
            )

            fig_frontier = apply_dark_theme(fig_frontier)
            st.plotly_chart(fig_frontier, use_container_width=True)

        st.markdown("### Monte Carlo Simulator")

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

            a, b, c = st.columns(3)
            a.metric("10th Percentile", f"${np.percentile(final_values, 10):,.0f}")
            b.metric("Median Outcome", f"${np.percentile(final_values, 50):,.0f}")
            c.metric("90th Percentile", f"${np.percentile(final_values, 90):,.0f}")

            fig_mc = go.Figure()

            for i in range(min(50, mc.shape[1])):
                fig_mc.add_trace(
                    go.Scatter(
                        y=mc.iloc[:, i],
                        mode="lines",
                        opacity=0.25,
                        showlegend=False
                    )
                )

            fig_mc.update_layout(
                title="Monte Carlo Portfolio Simulation",
                xaxis_title="Months",
                yaxis_title="Portfolio Value"
            )

            fig_mc = apply_dark_theme(fig_mc)
            st.plotly_chart(fig_mc, use_container_width=True)

    # ---------------------------
    # AI Advisor
    # ---------------------------

    with tab_ai:
        st.subheader("AI Recommendation Engine")

        ai_recs = enhanced_ai_recommendation(
            age,
            risk_tolerance,
            horizon,
            score,
            expected_return,
            volatility,
            sharpe,
            allocation
        )

        for rec in ai_recs:
            st.markdown(f"- {rec}")

        st.info(
            "This is a rule-based AI-style recommendation engine. "
            "In a real fintech product, this could be upgraded using machine learning models, "
            "client behavior data, market sentiment, and suitability rules."
        )

    # ---------------------------
    # Risk & Hedging Lab
    # ---------------------------

    with tab_risk:
        st.subheader("Risk & Hedging Lab")

        beta = calculate_portfolio_beta(prices, weights, period)

        r1, r2, r3 = st.columns(3)
        r1.metric("Portfolio Beta vs SPY", f"{beta:.2f}")
        r2.metric("Current Volatility", f"{volatility:.2%}")

        if beta > 1.2:
            hedge_signal = "High Market Risk"
        elif beta < 0.8:
            hedge_signal = "Defensive"
        else:
            hedge_signal = "Moderate Risk"

        r3.metric("Hedge Signal", hedge_signal)

        st.markdown("### Hedged Portfolio Simulation")

        hedge_result = hedge_portfolio_analysis(prices, weights, current_savings, period)

        if hedge_result is not None:
            hedge_comparison, hedge_weights_df = hedge_result

            st.write(
                "The app simulates a defensive hedge by shifting 20% of the portfolio into BND and GLD."
            )

            st.dataframe(hedge_comparison, use_container_width=True)

            st.markdown("### Suggested Hedged Allocation")
            st.dataframe(hedge_weights_df, use_container_width=True)

            fig_hedge = px.bar(
                hedge_weights_df,
                x="Asset",
                y="Hedged Weight (%)",
                title="Suggested Hedged Portfolio Allocation"
            )
            fig_hedge = apply_dark_theme(fig_hedge)
            st.plotly_chart(fig_hedge, use_container_width=True)

        st.markdown("### Stress Test Scenarios")

        stress_df = stress_test(weights)
        st.dataframe(stress_df, use_container_width=True)

        st.warning(
            "The hedging module is simplified for educational purposes. "
            "A real system would use options pricing, live market data, liquidity constraints, "
            "tax rules, and regulatory suitability checks."
        )

except Exception as e:
    st.error("Something went wrong while loading the app.")
    st.write(e)

st.divider()
st.caption("Built with Streamlit, yfinance, pandas, numpy, and plotly.")
