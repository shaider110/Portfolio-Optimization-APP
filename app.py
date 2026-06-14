import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="FinPilot AI", layout="wide")

# ---------------- STYLE ----------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #F1FBF6 0%, #FFFFFF 38%, #F6F8FB 100%);
    color: #102A43;
}
.block-container {
    padding-top: 1.5rem;
    max-width: 1250px;
}
.hero {
    background: linear-gradient(135deg, #DFF7EA 0%, #EAF4FF 55%, #FFFFFF 100%);
    padding: 42px;
    border-radius: 32px;
    border: 1px solid #D8EEE4;
    box-shadow: 0 18px 45px rgba(16, 42, 67, 0.08);
    margin-bottom: 24px;
}
.pill {
    display: inline-block;
    background: #BFF4D2;
    color: #065F46;
    padding: 8px 16px;
    border-radius: 999px;
    font-size: 14px;
    font-weight: 800;
    margin-bottom: 14px;
}
.hero-title {
    font-size: 48px;
    font-weight: 900;
    color: #062E2E;
    line-height: 1.05;
    max-width: 850px;
}
.hero-subtitle {
    font-size: 18px;
    color: #42606A;
    max-width: 820px;
    margin-top: 15px;
}
.feature-card {
    background: #FFFFFF;
    padding: 24px;
    border-radius: 26px;
    border: 1px solid #E3EAF0;
    box-shadow: 0px 12px 32px rgba(16, 42, 67, 0.07);
    margin-bottom: 18px;
}
.card-title {
    font-size: 22px;
    font-weight: 850;
    color: #102A43;
    margin-bottom: 6px;
}
.card-text {
    font-size: 15px;
    color: #52616B;
}
.accent-box {
    background: linear-gradient(135deg, #ECFDF5, #EFF6FF);
    border: 1px solid #D7F2E4;
    padding: 18px;
    border-radius: 22px;
    margin-bottom: 16px;
}
.risk-box {
    background: linear-gradient(135deg, #FFF7ED, #FEF2F2);
    border: 1px solid #FED7AA;
    padding: 18px;
    border-radius: 22px;
    margin-bottom: 16px;
}
div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E3EAF0;
    padding: 18px;
    border-radius: 22px;
    box-shadow: 0px 10px 26px rgba(16, 42, 67, 0.06);
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0px 16px 34px rgba(16, 42, 67, 0.12);
    transition: 0.25s ease;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 12px;
    background: #FFFFFF;
    padding: 10px;
    border-radius: 999px;
    border: 1px solid #E3EAF0;
    box-shadow: 0px 10px 30px rgba(16, 42, 67, 0.07);
    margin-bottom: 24px;
}
.stTabs [data-baseweb="tab"] {
    height: 50px;
    padding: 10px 22px;
    border-radius: 999px;
    color: #102A43;
    font-weight: 800;
    background: transparent;
    transition: all 0.25s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    background: #ECFDF5;
    color: #047857;
    transform: translateY(-2px);
    box-shadow: inset 0 0 0 1px #A7F3D0;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #10B981, #0EA5E9) !important;
    color: white !important;
    box-shadow: 0px 10px 24px rgba(16, 185, 129, 0.35);
}
[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E3EAF0;
}
.stButton > button {
    background: linear-gradient(135deg, #10B981, #0EA5E9);
    color: white;
    border: none;
    border-radius: 999px;
    padding: 0.7rem 1.4rem;
    font-weight: 800;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0px 12px 25px rgba(14, 165, 233, 0.25);
    transition: 0.25s ease;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="pill">AI-powered wealth management prototype</div>
    <div class="hero-title">Build wealth automatically with smarter portfolio guidance.</div>
    <div class="hero-subtitle">
        FinPilot AI creates a personalized investment plan, tracks portfolios, projects salary and contribution growth,
        simulates future wealth, analyzes dividends, optimizes allocations, and stress-tests portfolios under macro uncertainty.
    </div>
</div>
""", unsafe_allow_html=True)

st.caption("Educational prototype only. Not financial advice.")

# ---------------- FUNCTIONS ----------------

def apply_clean_theme(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#102A43"),
        title_font=dict(size=22, color="#102A43"),
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(bgcolor="rgba(255,255,255,0)", borderwidth=0)
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


@st.cache_data(ttl=3600)
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


def contribution_for_month(base_monthly_savings, contribution_growth_rate, month):
    year_number = month // 12
    return base_monthly_savings * ((1 + contribution_growth_rate) ** year_number)


def wealth_projection_with_growth(current_savings, monthly_savings, annual_return, years, contribution_growth_rate):
    months = years * 12
    monthly_return = annual_return / 12
    portfolio_value = current_savings
    values = []

    for month in range(months + 1):
        current_contribution = contribution_for_month(monthly_savings, contribution_growth_rate, month)

        values.append({
            "Month": month,
            "Year": month / 12,
            "Monthly Contribution": current_contribution,
            "Projected Value": portfolio_value
        })

        portfolio_value = portfolio_value * (1 + monthly_return) + current_contribution

    return pd.DataFrame(values)


def income_growth_schedule(annual_income, monthly_savings, salary_growth_rate, contribution_growth_rate, years):
    rows = []

    for year in range(years + 1):
        salary = annual_income * ((1 + salary_growth_rate) ** year)
        monthly_contribution = monthly_savings * ((1 + contribution_growth_rate) ** year)
        annual_contribution = monthly_contribution * 12
        contribution_rate = annual_contribution / salary if salary > 0 else 0

        rows.append({
            "Year": year,
            "Projected Salary": salary,
            "Monthly Contribution": monthly_contribution,
            "Annual Contribution": annual_contribution,
            "Contribution Rate": contribution_rate
        })

    return pd.DataFrame(rows)


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


def monte_carlo_simulation(start_value, monthly_savings, expected_return, volatility, years, contribution_growth_rate, simulations=500):
    months = years * 12
    monthly_return = expected_return / 12
    monthly_volatility = volatility / np.sqrt(12)
    all_paths = []

    for _ in range(simulations):
        value = start_value
        path = []

        for month in range(months + 1):
            path.append(value)
            current_contribution = contribution_for_month(monthly_savings, contribution_growth_rate, month)
            random_return = np.random.normal(monthly_return, monthly_volatility)
            value = value * (1 + random_return) + current_contribution

        all_paths.append(path)

    return pd.DataFrame(all_paths).T


def calculate_var(returns, weights, portfolio_value, confidence=0.95):
    portfolio_returns = returns.dot(weights)
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

    return covariance / variance if variance != 0 else 0


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

    _, current_var_amount = calculate_var(returns, weights, portfolio_value)
    _, hedged_var_amount = calculate_var(hedged_returns, hedge_weights, portfolio_value)

    comparison = pd.DataFrame({
        "Metric": ["Expected Annual Return", "Annual Volatility", "Sharpe Ratio", "Daily 95% VaR"],
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


def macro_scenario_assumptions(scenario):
    scenarios = {
        "Normal Market Environment": {
            "return_adjustment": 0.00,
            "volatility_multiplier": 1.00,
            "risk_label": "Low",
            "explanation": "Markets are assumed to behave near historical averages."
        },
        "Elevated Policy Uncertainty": {
            "return_adjustment": -0.02,
            "volatility_multiplier": 1.25,
            "risk_label": "Moderate",
            "explanation": "Higher policy uncertainty may reduce risk appetite and increase volatility."
        },
        "Trade War / Tariff Shock": {
            "return_adjustment": -0.04,
            "volatility_multiplier": 1.45,
            "risk_label": "High",
            "explanation": "Trade uncertainty can pressure global supply chains, margins, and equity valuations."
        },
        "Geopolitical Crisis": {
            "return_adjustment": -0.06,
            "volatility_multiplier": 1.70,
            "risk_label": "Very High",
            "explanation": "Geopolitical stress may create sharp market moves and demand for defensive assets."
        },
        "Recession Stress": {
            "return_adjustment": -0.08,
            "volatility_multiplier": 1.90,
            "risk_label": "Severe",
            "explanation": "A recession scenario assumes weak returns, higher volatility, and elevated drawdown risk."
        }
    }

    return scenarios[scenario]


def macro_uncertainty_score(epu, tpu, gpr):
    epu_score = min(epu / 500, 1) * 40
    tpu_score = min(tpu / 5000, 1) * 30
    gpr_score = min(gpr / 500, 1) * 30

    total = epu_score + tpu_score + gpr_score

    if total < 35:
        label = "Low Macro Risk"
    elif total < 60:
        label = "Moderate Macro Risk"
    elif total < 80:
        label = "High Macro Risk"
    else:
        label = "Extreme Macro Risk"

    return int(total), label


@st.cache_data(ttl=3600)
def get_dividend_data(tickers):
    dividend_rows = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            dividends = stock.dividends

            try:
                info = stock.info
                price = info.get("regularMarketPrice", np.nan)
            except Exception:
                price = np.nan

            if dividends is not None and not dividends.empty:
                last_date = dividends.index.max()
                one_year_ago = last_date - pd.DateOffset(years=1)
                annual_dividend = dividends[dividends.index >= one_year_ago].sum()
                dividend_yield = annual_dividend / price if price and price > 0 else 0
            else:
                annual_dividend = 0
                dividend_yield = 0

            dividend_rows.append({
                "Ticker": ticker,
                "Last Annual Dividend": annual_dividend,
                "Estimated Price": price,
                "Dividend Yield": dividend_yield
            })

        except Exception:
            dividend_rows.append({
                "Ticker": ticker,
                "Last Annual Dividend": 0,
                "Estimated Price": np.nan,
                "Dividend Yield": 0
            })

    return pd.DataFrame(dividend_rows)


def weighted_dividend_yield(dividend_df, tickers, weights):
    yields = []

    for ticker in tickers:
        row = dividend_df[dividend_df["Ticker"] == ticker]
        if not row.empty:
            yields.append(float(row["Dividend Yield"].iloc[0]))
        else:
            yields.append(0)

    return float(np.dot(weights, np.array(yields)))


def dividend_reinvestment_projection(
    starting_value,
    monthly_savings,
    expected_return,
    dividend_yield,
    dividend_growth_rate,
    contribution_growth_rate,
    years
):
    months = years * 12
    monthly_price_return = expected_return / 12

    value_with_reinvestment = starting_value
    value_without_reinvestment = starting_value
    annual_dividend_income = starting_value * dividend_yield

    rows = []

    for month in range(months + 1):
        year = month / 12
        current_contribution = contribution_for_month(monthly_savings, contribution_growth_rate, month)

        rows.append({
            "Year": year,
            "Monthly Contribution": current_contribution,
            "With Dividend Reinvestment": value_with_reinvestment,
            "Without Dividend Reinvestment": value_without_reinvestment,
            "Estimated Annual Dividend Income": annual_dividend_income
        })

        current_dividend_yield = dividend_yield * ((1 + dividend_growth_rate) ** year)
        monthly_dividend = value_with_reinvestment * (current_dividend_yield / 12)

        value_with_reinvestment = (
            value_with_reinvestment * (1 + monthly_price_return)
            + current_contribution
            + monthly_dividend
        )

        value_without_reinvestment = (
            value_without_reinvestment * (1 + monthly_price_return)
            + current_contribution
        )

        annual_dividend_income = value_with_reinvestment * current_dividend_yield

    return pd.DataFrame(rows)


def enhanced_ai_recommendation(
    age,
    risk_tolerance,
    horizon,
    score,
    expected_return,
    volatility,
    sharpe,
    allocation,
    macro_label,
    dividend_yield,
    salary_growth_rate,
    contribution_growth_rate
):
    recs = []

    recs.append(f"Your risk score is {score}/100, placing you in a {risk_tolerance.lower()} investor profile.")

    if horizon >= 10:
        recs.append("Your long time horizon supports higher equity exposure because you have more time to absorb volatility.")
    else:
        recs.append("Your shorter horizon means capital protection matters more, so the model favors a more defensive allocation.")

    if contribution_growth_rate > 0:
        recs.append(
            f"Your contributions are assumed to grow by {contribution_growth_rate:.1%} annually, which can meaningfully improve long-term wealth accumulation."
        )

    if salary_growth_rate > 0:
        recs.append(
            f"Your salary is assumed to grow by {salary_growth_rate:.1%} annually, allowing the model to create a more realistic planning path."
        )

    if volatility > 0.30:
        recs.append("Your current portfolio volatility is high. Adding defensive assets such as bonds, gold, or broad ETFs may help.")
    elif volatility < 0.15:
        recs.append("Your portfolio volatility is low, which reduces risk but may limit long-term growth.")
    else:
        recs.append("Your portfolio volatility appears balanced for a diversified strategy.")

    if sharpe > 1:
        recs.append("Your Sharpe ratio is strong, meaning the portfolio is producing attractive return relative to risk.")
    elif sharpe < 0.5:
        recs.append("Your Sharpe ratio is weak, meaning the portfolio may not be efficiently rewarding you for the risk taken.")
    else:
        recs.append("Your Sharpe ratio is reasonable, but optimization may improve risk-adjusted returns.")

    if dividend_yield > 0.03:
        recs.append("Your portfolio has meaningful dividend income potential, which can improve compounding if reinvested.")
    elif dividend_yield > 0:
        recs.append("Your portfolio has some dividend exposure, but most expected growth may still come from capital appreciation.")
    else:
        recs.append("Your portfolio has little dividend income exposure, so projected growth mainly depends on price appreciation.")

    if "High" in macro_label or "Extreme" in macro_label:
        recs.append("Macro uncertainty is elevated, so the model recommends stronger downside protection and lower concentration risk.")
    elif "Moderate" in macro_label:
        recs.append("Macro uncertainty is moderate, so the model recommends balanced exposure with some defensive allocation.")
    else:
        recs.append("Macro uncertainty is low, so the model does not require major defensive adjustments.")

    recs.append(
        f"The recommended strategic allocation is {allocation['Equity']}% equities, "
        f"{allocation['Bonds / Fixed Income']}% fixed income, and {allocation['Cash']}% cash."
    )

    return recs


def stress_test(weights):
    scenarios = {
        "COVID-style market shock": -0.20,
        "2022 inflation and rate shock": -0.18,
        "Trade war shock": -0.16,
        "Geopolitical crisis": -0.22,
        "Mild recession": -0.10,
        "Strong bull market": 0.15
    }

    return pd.DataFrame({
        "Scenario": list(scenarios.keys()),
        "Estimated Portfolio Impact": [f"{shock * np.sum(weights):.2%}" for shock in scenarios.values()]
    })


# ---------------- SIDEBAR ----------------

st.sidebar.title("FinPilot Controls")

st.sidebar.header("Investor Profile")
age = st.sidebar.number_input("Age", min_value=18, max_value=100, value=25)
annual_income = st.sidebar.number_input("Annual Income", min_value=0, value=60000, step=5000)
current_savings = st.sidebar.number_input("Current Savings", min_value=0, value=10000, step=1000)
monthly_savings = st.sidebar.number_input("Starting Monthly Contribution", min_value=0, value=1000, step=100)
risk_tolerance = st.sidebar.selectbox("Risk Tolerance", ["Conservative", "Moderate", "Aggressive"])
horizon = st.sidebar.slider("Investment Horizon", 1, 40, 10)

st.sidebar.header("Income Growth")
salary_growth_rate = st.sidebar.slider("Expected Annual Salary Growth (%)", 0, 20, 5) / 100
link_contribution_to_salary = st.sidebar.checkbox("Increase contributions with salary growth", value=True)

if link_contribution_to_salary:
    contribution_growth_rate = salary_growth_rate
else:
    contribution_growth_rate = st.sidebar.slider("Annual Contribution Growth (%)", 0, 20, 5) / 100

st.sidebar.header("Portfolio")
ticker_input = st.sidebar.text_input("Tickers", "AAPL, MSFT, NVDA, SPY, VYM")
period = st.sidebar.selectbox("Market Data Period", ["6mo", "1y", "2y", "5y"], index=1)

st.sidebar.header("Macro Risk")
macro_scenario = st.sidebar.selectbox(
    "Macro Scenario",
    [
        "Normal Market Environment",
        "Elevated Policy Uncertainty",
        "Trade War / Tariff Shock",
        "Geopolitical Crisis",
        "Recession Stress"
    ]
)

epu_input = st.sidebar.slider("Economic Policy Uncertainty Index", 50, 700, 200)
tpu_input = st.sidebar.slider("Trade Policy Uncertainty Index", 100, 6000, 1500)
gpr_input = st.sidebar.slider("Geopolitical Risk Index", 50, 700, 180)

tickers = [ticker.strip().upper() for ticker in ticker_input.split(",") if ticker.strip()]

allocation = recommend_allocation(age, risk_tolerance, horizon)
score = risk_score(age, risk_tolerance, horizon, monthly_savings, annual_income)
macro_score, macro_label = macro_uncertainty_score(epu_input, tpu_input, gpr_input)
scenario_data = macro_scenario_assumptions(macro_scenario)

# ---------------- APP ----------------

try:
    prices = get_stock_data(tickers, period)

    if prices.empty:
        st.error("No market data found. Please check the ticker symbols.")
        st.stop()

    normalized = prices / prices.iloc[0] * 100

    st.sidebar.header("Portfolio Weights")
    use_custom_weights = st.sidebar.checkbox("Use custom weights", value=False)

    if use_custom_weights:
        raw_weights = []
        for ticker in tickers:
            raw_weights.append(
                st.sidebar.number_input(
                    f"{ticker} weight (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=round(100 / len(tickers), 2),
                    step=1.0
                )
            )

        if sum(raw_weights) == 0:
            weights = np.array([1 / len(tickers)] * len(tickers))
        else:
            weights = np.array(raw_weights) / sum(raw_weights)
    else:
        weights = np.array([1 / len(tickers)] * len(tickers))

    expected_return, volatility, sharpe, returns = portfolio_metrics(prices, weights)
    adjusted_return = expected_return + scenario_data["return_adjustment"]
    adjusted_volatility = volatility * scenario_data["volatility_multiplier"]

    dividend_df = get_dividend_data(tickers)
    portfolio_dividend_yield = weighted_dividend_yield(dividend_df, tickers, weights)

    top1, top2, top3, top4 = st.columns(4)
    top1.metric("Risk Score", f"{score}/100")
    top2.metric("Expected Return", f"{expected_return:.2%}")
    top3.metric("Dividend Yield", f"{portfolio_dividend_yield:.2%}")
    top4.metric("Macro Risk", macro_label)

    tab_plan, tab_invest, tab_income, tab_analyze, tab_optimize, tab_macro, tab_protect = st.tabs([
        "Plan",
        "Invest",
        "Income",
        "Analyze",
        "Optimize",
        "Macro Risk",
        "Protect"
    ])

    with tab_plan:
        st.markdown("""
        <div class="feature-card">
            <div class="card-title">Your personalized wealth plan</div>
            <div class="card-text">
                Create a long-term investment path using savings, income growth, contribution growth, and risk profile.
            </div>
        </div>
        """, unsafe_allow_html=True)

        allocation_df = pd.DataFrame({
            "Asset Class": list(allocation.keys()),
            "Allocation (%)": list(allocation.values())
        })

        col1, col2 = st.columns(2)

        with col1:
            st.dataframe(allocation_df, use_container_width=True)

        with col2:
            fig_alloc = px.pie(
                allocation_df,
                names="Asset Class",
                values="Allocation (%)",
                hole=0.55,
                title="Recommended Allocation",
                color="Asset Class",
                color_discrete_sequence=["#10B981", "#0EA5E9", "#F59E0B"]
            )
            st.plotly_chart(apply_clean_theme(fig_alloc), use_container_width=True)

        st.markdown("""
        <div class="accent-box">
            <b>Salary and contribution growth:</b> The projection increases monthly contributions each year based on the selected growth assumption.
        </div>
        """, unsafe_allow_html=True)

        assumed_return = st.slider("Planning Return Assumption (%)", 1, 15, 7) / 100

        projection = wealth_projection_with_growth(
            current_savings=current_savings,
            monthly_savings=monthly_savings,
            annual_return=assumed_return,
            years=horizon,
            contribution_growth_rate=contribution_growth_rate
        )

        income_schedule = income_growth_schedule(
            annual_income=annual_income,
            monthly_savings=monthly_savings,
            salary_growth_rate=salary_growth_rate,
            contribution_growth_rate=contribution_growth_rate,
            years=horizon
        )

        p1, p2, p3 = st.columns(3)
        p1.metric("Projected Portfolio Value", f"${projection['Projected Value'].iloc[-1]:,.0f}")
        p2.metric("Final Monthly Contribution", f"${projection['Monthly Contribution'].iloc[-1]:,.0f}")
        p3.metric("Final Projected Salary", f"${income_schedule['Projected Salary'].iloc[-1]:,.0f}")

        fig_projection = px.area(
            projection,
            x="Year",
            y="Projected Value",
            title="Projected Wealth Growth With Rising Contributions",
            color_discrete_sequence=["#10B981"]
        )
        st.plotly_chart(apply_clean_theme(fig_projection), use_container_width=True)

        st.markdown("### Income and Contribution Schedule")
        display_income_schedule = income_schedule.copy()
        display_income_schedule["Projected Salary"] = display_income_schedule["Projected Salary"].apply(lambda x: f"${x:,.0f}")
        display_income_schedule["Monthly Contribution"] = display_income_schedule["Monthly Contribution"].apply(lambda x: f"${x:,.0f}")
        display_income_schedule["Annual Contribution"] = display_income_schedule["Annual Contribution"].apply(lambda x: f"${x:,.0f}")
        display_income_schedule["Contribution Rate"] = display_income_schedule["Contribution Rate"].apply(lambda x: f"{x:.1%}")
        st.dataframe(display_income_schedule, use_container_width=True)

        fig_contribution = go.Figure()
        fig_contribution.add_trace(go.Scatter(
            x=income_schedule["Year"],
            y=income_schedule["Projected Salary"],
            mode="lines+markers",
            name="Projected Salary",
            line=dict(width=4, color="#0EA5E9")
        ))
        fig_contribution.add_trace(go.Scatter(
            x=income_schedule["Year"],
            y=income_schedule["Annual Contribution"],
            mode="lines+markers",
            name="Annual Contribution",
            line=dict(width=4, color="#10B981")
        ))
        fig_contribution.update_layout(
            title="Projected Salary vs Annual Contributions",
            xaxis_title="Year",
            yaxis_title="Amount"
        )
        st.plotly_chart(apply_clean_theme(fig_contribution), use_container_width=True)

    with tab_invest:
        st.markdown("""
        <div class="feature-card">
            <div class="card-title">Market and portfolio tracking</div>
            <div class="card-text">
                Track selected stocks and ETFs against a broad market benchmark.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(prices.tail(), use_container_width=True)

        fig_prices = go.Figure()
        colors = ["#10B981", "#0EA5E9", "#8B5CF6", "#F59E0B", "#EF4444", "#14B8A6", "#6366F1"]

        for i, ticker in enumerate(normalized.columns):
            fig_prices.add_trace(go.Scatter(
                x=normalized.index,
                y=normalized[ticker],
                mode="lines",
                name=ticker,
                line=dict(width=3, color=colors[i % len(colors)])
            ))

        benchmark = get_stock_data(["SPY"], period)
        benchmark_norm = benchmark / benchmark.iloc[0] * 100

        fig_prices.add_trace(go.Scatter(
            x=benchmark_norm.index,
            y=benchmark_norm["SPY"],
            mode="lines",
            name="Benchmark: SPY",
            line=dict(width=3, dash="dash", color="#111827")
        ))

        fig_prices.update_layout(
            title="Growth of $100 vs S&P 500 ETF",
            xaxis_title="Date",
            yaxis_title="Indexed Value"
        )
        st.plotly_chart(apply_clean_theme(fig_prices), use_container_width=True)

    with tab_income:
        st.markdown("""
        <div class="feature-card">
            <div class="card-title">Dividend income engine</div>
            <div class="card-text">
                Estimate dividend yield, annual income, dividend growth, and the long-term impact of reinvesting dividends.
            </div>
        </div>
        """, unsafe_allow_html=True)

        display_dividend_df = dividend_df.copy()
        display_dividend_df["Dividend Yield"] = display_dividend_df["Dividend Yield"].apply(lambda x: f"{x:.2%}")
        display_dividend_df["Last Annual Dividend"] = display_dividend_df["Last Annual Dividend"].apply(lambda x: f"${x:.2f}")
        display_dividend_df["Estimated Price"] = display_dividend_df["Estimated Price"].apply(
            lambda x: f"${x:.2f}" if pd.notna(x) else "N/A"
        )
        st.dataframe(display_dividend_df, use_container_width=True)

        estimated_annual_income = current_savings * portfolio_dividend_yield

        d1, d2, d3 = st.columns(3)
        d1.metric("Portfolio Dividend Yield", f"{portfolio_dividend_yield:.2%}")
        d2.metric("Estimated Annual Dividend Income", f"${estimated_annual_income:,.0f}")
        d3.metric("Monthly Dividend Income", f"${estimated_annual_income / 12:,.0f}")

        fig_div_yield = px.bar(
            dividend_df,
            x="Ticker",
            y="Dividend Yield",
            title="Estimated Dividend Yield by Asset",
            color="Ticker",
            color_discrete_sequence=["#10B981", "#0EA5E9", "#8B5CF6", "#F59E0B", "#EF4444", "#14B8A6", "#6366F1"]
        )
        fig_div_yield.update_yaxes(tickformat=".2%")
        st.plotly_chart(apply_clean_theme(fig_div_yield), use_container_width=True)

        st.markdown("""
        <div class="accent-box">
            <b>Dividend reinvestment simulator:</b> Compare portfolio growth when dividends are reinvested versus not reinvested.
        </div>
        """, unsafe_allow_html=True)

        dividend_growth_rate = st.slider("Assumed Annual Dividend Growth Rate (%)", 0, 10, 3) / 100

        dividend_projection = dividend_reinvestment_projection(
            starting_value=current_savings,
            monthly_savings=monthly_savings,
            expected_return=expected_return,
            dividend_yield=portfolio_dividend_yield,
            dividend_growth_rate=dividend_growth_rate,
            contribution_growth_rate=contribution_growth_rate,
            years=horizon
        )

        final_with_reinvestment = dividend_projection["With Dividend Reinvestment"].iloc[-1]
        final_without_reinvestment = dividend_projection["Without Dividend Reinvestment"].iloc[-1]
        reinvestment_benefit = final_with_reinvestment - final_without_reinvestment

        r1, r2, r3 = st.columns(3)
        r1.metric("With Reinvestment", f"${final_with_reinvestment:,.0f}")
        r2.metric("Without Reinvestment", f"${final_without_reinvestment:,.0f}")
        r3.metric("Reinvestment Benefit", f"${reinvestment_benefit:,.0f}")

        fig_reinvest = go.Figure()
        fig_reinvest.add_trace(go.Scatter(
            x=dividend_projection["Year"],
            y=dividend_projection["With Dividend Reinvestment"],
            mode="lines",
            name="With Dividend Reinvestment",
            line=dict(width=4, color="#10B981")
        ))
        fig_reinvest.add_trace(go.Scatter(
            x=dividend_projection["Year"],
            y=dividend_projection["Without Dividend Reinvestment"],
            mode="lines",
            name="Without Dividend Reinvestment",
            line=dict(width=4, dash="dash", color="#0EA5E9")
        ))
        fig_reinvest.update_layout(
            title="Portfolio Growth: Dividends Reinvested vs Not Reinvested",
            xaxis_title="Year",
            yaxis_title="Portfolio Value"
        )
        st.plotly_chart(apply_clean_theme(fig_reinvest), use_container_width=True)

        fig_income_growth = px.area(
            dividend_projection,
            x="Year",
            y="Estimated Annual Dividend Income",
            title="Projected Annual Dividend Income Growth",
            color_discrete_sequence=["#F59E0B"]
        )
        st.plotly_chart(apply_clean_theme(fig_income_growth), use_container_width=True)

        st.info(
            "Dividend estimates use recent dividend history and user-selected dividend growth. "
            "Actual dividends can change depending on company earnings, ETF distributions, and market conditions."
        )

    with tab_analyze:
        st.markdown("""
        <div class="feature-card">
            <div class="card-title">Portfolio analytics dashboard</div>
            <div class="card-text">
                Analyze return, volatility, Sharpe ratio, diversification, and correlations using the selected portfolio weights.
            </div>
        </div>
        """, unsafe_allow_html=True)

        health_score = portfolio_health_score(len(tickers), volatility, sharpe)

        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Expected Return", f"{expected_return:.2%}")
        a2.metric("Volatility", f"{volatility:.2%}")
        a3.metric("Sharpe Ratio", f"{sharpe:.2f}")
        a4.metric("Health Score", f"{health_score}/100")

        weights_df = pd.DataFrame({
            "Ticker": tickers,
            "Portfolio Weight": weights
        })
        weights_df["Portfolio Weight"] = weights_df["Portfolio Weight"].apply(lambda x: f"{x:.2%}")
        st.markdown("### Current Portfolio Weights")
        st.dataframe(weights_df, use_container_width=True)

        corr = returns.corr()

        fig_corr = px.imshow(
            corr,
            text_auto=True,
            title="Asset Correlation Matrix",
            color_continuous_scale=["#10B981", "#FFFFFF", "#EF4444"]
        )
        st.plotly_chart(apply_clean_theme(fig_corr), use_container_width=True)

    with tab_optimize:
        st.markdown("""
        <div class="feature-card">
            <div class="card-title">Optimization studio</div>
            <div class="card-text">
                Run Monte Carlo simulations and find portfolios with stronger risk-adjusted performance.
            </div>
        </div>
        """, unsafe_allow_html=True)

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
                color_continuous_scale="Viridis"
            )

            fig_frontier.add_trace(go.Scatter(
                x=[best_portfolio["Volatility"]],
                y=[best_portfolio["Return"]],
                mode="markers",
                marker=dict(size=18, symbol="star", color="#F59E0B"),
                name="Max Sharpe"
            ))

            fig_frontier.add_trace(go.Scatter(
                x=[min_vol_portfolio["Volatility"]],
                y=[min_vol_portfolio["Return"]],
                mode="markers",
                marker=dict(size=15, symbol="diamond", color="#0EA5E9"),
                name="Min Volatility"
            ))

            st.plotly_chart(apply_clean_theme(fig_frontier), use_container_width=True)

        if st.button("Run Standard Monte Carlo Simulation"):
            mc = monte_carlo_simulation(
                start_value=current_savings,
                monthly_savings=monthly_savings,
                expected_return=expected_return,
                volatility=volatility,
                years=horizon,
                contribution_growth_rate=contribution_growth_rate,
                simulations=500
            )

            final_values = mc.iloc[-1]

            m1, m2, m3 = st.columns(3)
            m1.metric("10th Percentile", f"${np.percentile(final_values, 10):,.0f}")
            m2.metric("Median", f"${np.percentile(final_values, 50):,.0f}")
            m3.metric("90th Percentile", f"${np.percentile(final_values, 90):,.0f}")

            fig_mc = go.Figure()
            for i in range(min(50, mc.shape[1])):
                fig_mc.add_trace(go.Scatter(
                    y=mc.iloc[:, i],
                    mode="lines",
                    opacity=0.22,
                    line=dict(color="#10B981"),
                    showlegend=False
                ))

            fig_mc.update_layout(
                title="Standard Monte Carlo Portfolio Paths With Rising Contributions",
                xaxis_title="Months",
                yaxis_title="Portfolio Value"
            )
            st.plotly_chart(apply_clean_theme(fig_mc), use_container_width=True)

    with tab_macro:
        st.markdown("""
        <div class="feature-card">
            <div class="card-title">Macro Risk Simulator</div>
            <div class="card-text">
                Stress-test the portfolio under policy uncertainty, trade uncertainty, geopolitical risk, and recession-style scenarios.
            </div>
        </div>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Macro Score", f"{macro_score}/100")
        m2.metric("Macro Regime", macro_label)
        m3.metric("Scenario", macro_scenario)
        m4.metric("Scenario Risk", scenario_data["risk_label"])

        st.markdown(f"""
        <div class="risk-box">
            <b>Scenario explanation:</b> {scenario_data["explanation"]}
        </div>
        """, unsafe_allow_html=True)

        macro_inputs_df = pd.DataFrame({
            "Indicator": ["Economic Policy Uncertainty", "Trade Policy Uncertainty", "Geopolitical Risk"],
            "Input Value": [epu_input, tpu_input, gpr_input]
        })

        fig_macro = px.bar(
            macro_inputs_df,
            x="Indicator",
            y="Input Value",
            color="Indicator",
            title="Macro Uncertainty Indicators",
            color_discrete_sequence=["#10B981", "#0EA5E9", "#EF4444"]
        )
        st.plotly_chart(apply_clean_theme(fig_macro), use_container_width=True)

        scenario_df = pd.DataFrame({
            "Metric": ["Base Expected Return", "Macro-Adjusted Return", "Base Volatility", "Macro-Adjusted Volatility"],
            "Value": [
                f"{expected_return:.2%}",
                f"{adjusted_return:.2%}",
                f"{volatility:.2%}",
                f"{adjusted_volatility:.2%}"
            ]
        })

        st.dataframe(scenario_df, use_container_width=True)

        if st.button("Run Macro-Adjusted Monte Carlo Simulation"):
            macro_mc = monte_carlo_simulation(
                start_value=current_savings,
                monthly_savings=monthly_savings,
                expected_return=adjusted_return,
                volatility=adjusted_volatility,
                years=horizon,
                contribution_growth_rate=contribution_growth_rate,
                simulations=500
            )

            final_values = macro_mc.iloc[-1]

            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Stress Case 10th Percentile", f"${np.percentile(final_values, 10):,.0f}")
            mc2.metric("Median Outcome", f"${np.percentile(final_values, 50):,.0f}")
            mc3.metric("Upside Case 90th Percentile", f"${np.percentile(final_values, 90):,.0f}")

            fig_macro_mc = go.Figure()
            for i in range(min(50, macro_mc.shape[1])):
                fig_macro_mc.add_trace(go.Scatter(
                    y=macro_mc.iloc[:, i],
                    mode="lines",
                    opacity=0.22,
                    line=dict(color="#EF4444"),
                    showlegend=False
                ))

            fig_macro_mc.update_layout(
                title=f"Macro-Adjusted Monte Carlo Simulation: {macro_scenario}",
                xaxis_title="Months",
                yaxis_title="Portfolio Value"
            )
            st.plotly_chart(apply_clean_theme(fig_macro_mc), use_container_width=True)

        st.info(
            "This module uses scenario-based assumptions rather than a formal econometric model. "
            "It is designed to be explainable and useful for a class project."
        )

    with tab_protect:
        st.markdown("""
        <div class="feature-card">
            <div class="card-title">Protection and hedging lab</div>
            <div class="card-text">
                Estimate beta, downside risk, hedged allocation, and stress-test portfolio performance.
            </div>
        </div>
        """, unsafe_allow_html=True)

        beta = calculate_portfolio_beta(prices, weights, period)

        p1, p2, p3 = st.columns(3)
        p1.metric("Beta vs SPY", f"{beta:.2f}")
        p2.metric("Current Volatility", f"{volatility:.2%}")

        if beta > 1.2:
            hedge_signal = "High Market Risk"
        elif beta < 0.8:
            hedge_signal = "Defensive"
        else:
            hedge_signal = "Moderate Risk"

        p3.metric("Hedge Signal", hedge_signal)

        hedge_result = hedge_portfolio_analysis(prices, weights, current_savings, period)

        if hedge_result is not None:
            hedge_comparison, hedge_weights_df = hedge_result

            st.markdown("""
            <div class="accent-box">
                The hedge simulation shifts 20% of the portfolio into defensive assets: 10% BND and 10% GLD.
            </div>
            """, unsafe_allow_html=True)

            st.dataframe(hedge_comparison, use_container_width=True)

            fig_hedge = px.bar(
                hedge_weights_df,
                x="Asset",
                y="Hedged Weight (%)",
                title="Suggested Hedged Allocation",
                color="Asset",
                color_discrete_sequence=["#10B981", "#0EA5E9", "#8B5CF6", "#F59E0B", "#EF4444", "#14B8A6"]
            )
            st.plotly_chart(apply_clean_theme(fig_hedge), use_container_width=True)

        st.markdown("### Stress Test Scenarios")
        st.dataframe(stress_test(weights), use_container_width=True)

        st.info(
            "This hedging module is simplified for educational purposes. "
            "A real platform would use live options data, liquidity, taxes, and regulatory suitability checks."
        )

    st.markdown("""
    <div class="feature-card">
        <div class="card-title">AI Advisor Summary</div>
        <div class="card-text">
            A rule-based recommendation engine explains risk profile, contribution growth, dividend potential,
            portfolio efficiency, allocation suitability, and macro-risk exposure.
        </div>
    </div>
    """, unsafe_allow_html=True)

    ai_recs = enhanced_ai_recommendation(
        age=age,
        risk_tolerance=risk_tolerance,
        horizon=horizon,
        score=score,
        expected_return=expected_return,
        volatility=volatility,
        sharpe=sharpe,
        allocation=allocation,
        macro_label=macro_label,
        dividend_yield=portfolio_dividend_yield,
        salary_growth_rate=salary_growth_rate,
        contribution_growth_rate=contribution_growth_rate
    )

    for rec in ai_recs:
        st.markdown(f"- {rec}")

except Exception as e:
    st.error("Something went wrong while loading the app.")
    st.write(e)

st.divider()
st.caption("Built with Streamlit, yfinance, pandas, numpy, and plotly.")
