import math
import random
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dateutil.relativedelta import relativedelta

# Page config
st.set_page_config(
    page_title="Monthly Billing Statement Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Constants
REQUIRED_COLUMNS = [
    "statement_date",
    "bank_name",
    "bank_specific_name",
    "product_line",
    "unit_price",
    "volume",
    "currency",
    "unit_of_measure",
]

OPTIONAL_COLUMNS = ["fee_type", "region"]

PRODUCT_LINES = [
    "Payments",
    "FX",
    "Trade Finance",
    "Liquidity",
    "Custody",
    "Securities Lending",
    "Cash Management",
    "Cards",
    "Loans Servicing",
    "Reporting",
]

BANKS = [
    "Alpha Bank",
    "Continental Capital",
    "First National",
    "Global Trust",
    "Union Bank",
    "Metro Finance",
    "Northern Mutual",
]

CURRENCIES = ["USD", "EUR", "GBP"]

FEE_TYPES = ["Fixed", "Variable", "Tiered"]
REGIONS = ["NA", "EMEA", "APAC", "LATAM"]

random.seed(42)
np.random.seed(42)


def generate_mock_data(target_month: date, num_rows: int = 1500) -> pd.DataFrame:
    start = target_month.replace(day=1)
    end = (start + relativedelta(months=1)) - timedelta(days=1)

    all_days = pd.date_range(start=start, end=end, freq="D")

    product_choices = np.random.choice(PRODUCT_LINES, size=num_rows, p=_normalize([9, 7, 5, 3, 4, 2, 6, 5, 3, 2]))
    bank_choices = np.random.choice(BANKS, size=num_rows)
    currency_choices = np.random.choice(CURRENCIES, size=num_rows, p=_normalize([10, 5, 3]))
    fee_choices = np.random.choice(FEE_TYPES, size=num_rows)
    region_choices = np.random.choice(REGIONS, size=num_rows)
    dates = np.random.choice(all_days, size=num_rows)

    # Base price per product line
    base_price_map = {
        "Payments": 0.08,
        "FX": 12.0,
        "Trade Finance": 45.0,
        "Liquidity": 5.0,
        "Custody": 2.5,
        "Securities Lending": 1.1,
        "Cash Management": 0.02,
        "Cards": 0.15,
        "Loans Servicing": 3.0,
        "Reporting": 0.01,
    }

    # Unit of measure per product line
    uom_map = {
        "Payments": "transactions",
        "FX": "trades",
        "Trade Finance": "instruments",
        "Liquidity": "days",
        "Custody": "positions",
        "Securities Lending": "positions",
        "Cash Management": "transactions",
        "Cards": "transactions",
        "Loans Servicing": "loans",
        "Reporting": "reports",
    }

    unit_prices = []
    volumes = []
    bank_specific_names = []

    for pl in product_choices:
        base = base_price_map[pl]
        # Add noise and tiering effect
        price = max(0.001, np.random.lognormal(mean=math.log(base + 0.001), sigma=0.35))
        unit_prices.append(round(price, 4))

        # Volume varies by product
        if pl in {"Payments", "Cash Management", "Cards"}:
            vol = int(np.random.lognormal(mean=8.5, sigma=0.6))
        elif pl in {"Custody", "Securities Lending"}:
            vol = int(np.random.lognormal(mean=6.8, sigma=0.7))
        elif pl in {"FX", "Trade Finance"}:
            vol = int(np.random.lognormal(mean=4.0, sigma=0.7))
        elif pl == "Reporting":
            vol = int(np.random.lognormal(mean=3.5, sigma=0.4))
        else:
            vol = int(np.random.lognormal(mean=5.0, sigma=0.6))
        volumes.append(max(1, vol))

        bank_specific_names.append(f"{pl[:3].upper()}-{np.random.randint(100, 999)}")

    df = pd.DataFrame(
        {
            "statement_date": pd.to_datetime(dates).date,
            "bank_name": bank_choices,
            "bank_specific_name": bank_specific_names,
            "product_line": product_choices,
            "unit_price": unit_prices,
            "volume": volumes,
            "currency": currency_choices,
            "unit_of_measure": [uom_map[pl] for pl in product_choices],
            "fee_type": fee_choices,
            "region": region_choices,
        }
    )

    # Currency FX for mock (rough, not for real use)
    fx_map = {"USD": 1.0, "EUR": 1.07, "GBP": 1.25}
    df["amount"] = (df["unit_price"] * df["volume"]).round(2)
    df["amount_usd"] = (df["amount"] * df["currency"].map(fx_map)).round(2)

    return df


def _normalize(weights):
    total = float(sum(weights))
    return [w / total for w in weights]


def load_uploaded_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing) + ".\n"
            "Expected columns: " + ", ".join(REQUIRED_COLUMNS)
        )

    # Coerce dtypes
    df["statement_date"] = pd.to_datetime(df["statement_date"]).dt.date
    for c in ["unit_price", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    if "amount" not in df.columns:
        df["amount"] = (df["unit_price"] * df["volume"]).round(2)

    if "amount_usd" not in df.columns:
        fx_map = {"USD": 1.0, "EUR": 1.07, "GBP": 1.25}
        df["amount_usd"] = (df["amount"] * df["currency"].map(fx_map).fillna(1.0)).round(2)

    return df


# Sidebar controls
st.sidebar.title("Billing Statement Controls")

month_options = [
    (date.today() - relativedelta(months=m)).replace(day=1) for m in range(0, 12)
]
selected_month = st.sidebar.selectbox(
    "Statement month",
    options=month_options,
    format_func=lambda d: d.strftime("%b %Y"),
    index=0,
)

uploaded = st.sidebar.file_uploader(
    "Upload CSV (optional)",
    type=["csv"],
    help=(
        "Columns: "
        + ", ".join(REQUIRED_COLUMNS)
        + ". Optional: "
        + ", ".join(OPTIONAL_COLUMNS)
    ),
)

# Load data
try:
    if uploaded is not None:
        data = load_uploaded_csv(uploaded)
    else:
        data = generate_mock_data(selected_month, num_rows=2000)
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# Filter panel
with st.sidebar.expander("Filters", expanded=True):
    banks = st.multiselect("Banks", options=sorted(data["bank_name"].unique().tolist()))
    products = st.multiselect("Product lines", options=sorted(data["product_line"].unique().tolist()))
    currencies = st.multiselect("Currencies", options=sorted(data["currency"].unique().tolist()))
    fee_types = st.multiselect(
        "Fee types", options=sorted(data.get("fee_type", pd.Series(dtype=str)).unique().tolist())
    )

# Apply month filter
start_of_month = selected_month.replace(day=1)
end_of_month = (start_of_month + relativedelta(months=1)) - timedelta(days=1)
mask = (
    (pd.to_datetime(data["statement_date"]) >= pd.to_datetime(start_of_month))
    & (pd.to_datetime(data["statement_date"]) <= pd.to_datetime(end_of_month))
)
filtered = data.loc[mask].copy()

# Apply other filters
if banks:
    filtered = filtered[filtered["bank_name"].isin(banks)]
if products:
    filtered = filtered[filtered["product_line"].isin(products)]
if currencies:
    filtered = filtered[filtered["currency"].isin(currencies)]
if fee_types and "fee_type" in filtered.columns:
    filtered = filtered[filtered["fee_type"].isin(fee_types)]

# Header
st.title("Monthly Billing Statement")
sub = f"{start_of_month.strftime('%b %Y')}"
st.caption(f"Statement period: {sub}")

if filtered.empty:
    st.warning("No data for the selected filters.")
    st.stop()

# KPIs
total_billed = filtered["amount_usd"].sum()
total_volume = filtered["volume"].sum()
avg_unit_price = (filtered["unit_price"].mean())
num_banks = filtered["bank_name"].nunique()
num_products = filtered["bank_specific_name"].nunique()

kpi_cols = st.columns(5)
kpi_cols[0].metric("Total Billed (USD)", f"${total_billed:,.2f}")
kpi_cols[1].metric("Total Volume", f"{int(total_volume):,}")
kpi_cols[2].metric("Avg. Unit Price", f"${avg_unit_price:,.4f}")
kpi_cols[3].metric("Banks", f"{num_banks}")
kpi_cols[4].metric("Bank Products", f"{num_products}")

st.divider()

# Aggregations
by_product = (
    filtered.groupby("product_line", as_index=False)["amount_usd"].sum().sort_values("amount_usd", ascending=False)
)
by_bank = (
    filtered.groupby("bank_name", as_index=False)["amount_usd"].sum().sort_values("amount_usd", ascending=False)
)
by_day = (
    filtered.assign(day=pd.to_datetime(filtered["statement_date"]).dt.to_period("D").dt.to_timestamp())
    .groupby("day", as_index=False)["amount_usd"].sum()
)

# Charts row 1
c1, c2 = st.columns((3, 2), gap="large")
with c1:
    fig1 = px.bar(
        by_product,
        x="product_line",
        y="amount_usd",
        color="product_line",
        title="Billing by Product Line (USD)",
        text=by_product["amount_usd"].apply(lambda v: f"${v:,.0f}"),
    )
    fig1.update_traces(textposition="outside")
    fig1.update_layout(showlegend=False, yaxis_title="Amount (USD)")
    st.plotly_chart(fig1, use_container_width=True, theme="streamlit")

with c2:
    fig2 = px.treemap(
        filtered,
        path=["bank_name", "product_line"],
        values="amount_usd",
        title="Contribution by Bank and Product",
    )
    st.plotly_chart(fig2, use_container_width=True, theme="streamlit")

# Charts row 2
c3, c4 = st.columns((3, 2), gap="large")
with c3:
    fig3 = px.line(
        by_day,
        x="day",
        y="amount_usd",
        markers=True,
        title="Daily Billing Trend (USD)",
    )
    fig3.update_layout(xaxis_title="Date", yaxis_title="Amount (USD)")
    st.plotly_chart(fig3, use_container_width=True, theme="streamlit")

with c4:
    fig4 = px.scatter(
        filtered,
        x="volume",
        y="unit_price",
        size="amount_usd",
        color="product_line",
        hover_data=["bank_name", "bank_specific_name", "currency"],
        title="Unit Price vs Volume (bubble size = billed USD)",
    )
    fig4.update_layout(xaxis_title="Volume", yaxis_title="Unit Price")
    st.plotly_chart(fig4, use_container_width=True, theme="streamlit")

# Charts row 3: Heatmap of product x bank
pivot = (
    filtered.pivot_table(
        index="product_line",
        columns="bank_name",
        values="amount_usd",
        aggfunc="sum",
        fill_value=0.0,
    )
    .round(2)
)

heatmap_fig = go.Figure(
    data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale="Teal",
        colorbar=dict(title="USD"),
        hovertemplate="Bank: %{x}<br>Product: %{y}<br>USD: %{z:,.0f}<extra></extra>",
    )
)
heatmap_fig.update_layout(title="Heatmap: Billing by Product x Bank (USD)")
st.plotly_chart(heatmap_fig, use_container_width=True, theme="streamlit")

st.divider()

# Detailed tables
st.subheader("Detailed Line Items")

display_cols = [
    "statement_date",
    "bank_name",
    "bank_specific_name",
    "product_line",
    "unit_price",
    "unit_of_measure",
    "volume",
    "currency",
    "amount",
    "amount_usd",
]
extra_cols = [c for c in ["fee_type", "region"] if c in filtered.columns]

ordered_cols = display_cols + extra_cols

styled = filtered[ordered_cols].sort_values(["bank_name", "product_line", "statement_date"]).copy()

st.dataframe(
    styled,
    use_container_width=True,
    hide_index=True,
    column_config={
        "unit_price": st.column_config.NumberColumn("Unit Price", format="$%.4f"),
        "amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
        "amount_usd": st.column_config.NumberColumn("Amount (USD)", format="$%.2f"),
        "volume": st.column_config.NumberColumn("Volume", format="%d"),
        "statement_date": st.column_config.DateColumn("Date"),
    },
)

# Grouped summary table
st.subheader("Summary by Bank and Product Line (USD)")
summary = (
    filtered.groupby(["bank_name", "product_line"], as_index=False)[["volume", "amount_usd"]]
    .sum()
    .sort_values(["bank_name", "amount_usd"], ascending=[True, False])
)

st.dataframe(
    summary,
    use_container_width=True,
    hide_index=True,
    column_config={
        "amount_usd": st.column_config.NumberColumn("Amount (USD)", format="$%.2f"),
        "volume": st.column_config.NumberColumn("Volume", format="%d"),
    },
)

# Downloads
def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 6])
col_dl1.download_button(
    "Download Line Items CSV",
    data=to_csv_bytes(styled),
    file_name=f"billing_line_items_{start_of_month.strftime('%Y_%m')}.csv",
    mime="text/csv",
)
col_dl2.download_button(
    "Download Summary CSV",
    data=to_csv_bytes(summary),
    file_name=f"billing_summary_{start_of_month.strftime('%Y_%m')}.csv",
    mime="text/csv",
)

with st.expander("Sample CSV Template"):
    template = pd.DataFrame(
        {
            "statement_date": [start_of_month.strftime("%Y-%m-%d")],
            "bank_name": ["Alpha Bank"],
            "bank_specific_name": ["PAY-101"],
            "product_line": ["Payments"],
            "unit_price": [0.08],
            "volume": [10000],
            "currency": ["USD"],
            "unit_of_measure": ["transactions"],
            "fee_type": ["Variable"],
            "region": ["NA"],
        }
    )
    st.dataframe(template, hide_index=True, use_container_width=True)
    st.download_button(
        "Download Template CSV",
        data=to_csv_bytes(template),
        file_name="billing_template.csv",
        mime="text/csv",
    )

st.caption(
    "All amounts converted to USD for comparability using illustrative FX rates (mock data)."
)