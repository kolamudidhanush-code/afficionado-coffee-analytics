
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Afficionado Coffee Analytics",
    page_icon="☕",
    layout="wide"
)

# ---------- Professional Coffee Theme ----------
st.markdown("""
<style>
    /* Main app background and typography */
    .stApp {
        background-color: #FAF7F2;
        color: #35251D;
    }

    h1, h2, h3 {
        color: #4B2E24 !important;
    }

    /* KPI metric cards */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E8DCCF;
        padding: 18px 20px;
        border-radius: 14px;
        box-shadow: 0 3px 10px rgba(75, 46, 36, 0.06);
    }

    div[data-testid="stMetricLabel"] {
        color: #795548;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        color: #4B2E24;
        font-weight: 700;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #F0E6D8;
    }

    /* Buttons */
    .stDownloadButton button {
        background-color: #6F4E37;
        color: white;
        border: none;
        border-radius: 8px;
    }

    .stDownloadButton button:hover {
        background-color: #4B2E24;
        color: white;
        border: none;
    }

    /* Section separators */
    hr {
        border-color: #E3D5C6;
    }

    /* Data tables */
    div[data-testid="stDataFrame"] {
        border: 1px solid #E8DCCF;
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)


# ---------- Load data ----------
@st.cache_data
def load_data():
    df = pd.read_csv("afficionado_cleaned_data.csv")

    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    required = [
        "transaction_id", "transaction_qty", "unit_price",
        "store_id", "store_location", "product_id",
        "product_category", "product_type", "product_detail"
    ]

    missing = [col for col in required if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["transaction_qty"] = pd.to_numeric(
        df["transaction_qty"], errors="raise"
    )
    df["unit_price"] = pd.to_numeric(
        df["unit_price"], errors="raise"
    )
    df["revenue"] = df["transaction_qty"] * df["unit_price"]

    return df


df = load_data()

# ---------- Header ----------
st.title("☕ Afficionado Coffee Roasters")
st.subheader("Product Optimization & Revenue Contribution Analysis")
st.caption(
    "Explore product performance, revenue contribution, "
    "category mix, and store-level sales."
)

# ---------- Sidebar filters ----------
st.sidebar.header("Dashboard Filters")

categories = sorted(df["product_category"].dropna().unique())

selected_categories = st.sidebar.multiselect(
    "Product categories",
    categories,
    default=categories,
    placeholder="Choose categories",
    help="Select one or more categories to filter the dashboard."
)


locations = sorted(df["store_location"].dropna().unique())
selected_locations = st.sidebar.multiselect(
    "Store locations",
    locations,
    default=locations
)

types = sorted(df["product_type"].dropna().unique())
selected_types = st.sidebar.multiselect(
    "Product types",
    types,
    default=types
)

top_n = st.sidebar.slider(
    "Number of products to display",
    min_value=5,
    max_value=20,
    value=10
)

filtered = df[
    df["product_category"].isin(selected_categories)
    & df["store_location"].isin(selected_locations)
    & df["product_type"].isin(selected_types)
].copy()

if filtered.empty:
    st.warning("No records match your selected filters.")
    st.stop()

# ---------- KPI cards ----------
total_revenue = filtered["revenue"].sum()
total_units = filtered["transaction_qty"].sum()
transaction_records = len(filtered)
unique_products = filtered["product_id"].nunique()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Revenue", f"{total_revenue:,.2f}")
c2.metric("Units Sold", f"{total_units:,.0f}")
c3.metric("Transaction Records", f"{transaction_records:,}")
c4.metric("Products", f"{unique_products:,}")

st.divider()

# ---------- Category analysis ----------

# Consistent colors for interactive charts
COFFEE_COLORS = [
    "#6F4E37",  # Coffee brown
    "#B08968",  # Latte
    "#DDB892",  # Caramel
    "#7F5539",  # Roasted brown
    "#A3B18A",  # Muted green
    "#CB997E",  # Warm clay
    "#9C6644",  # Mocha
    "#E6CCB2",  # Cream
    "#774936"   # Dark roast
]

st.header("Category Performance")

category_data = (
    filtered.groupby("product_category", as_index=False)
    .agg(
        Revenue=("revenue", "sum"),
        Units=("transaction_qty", "sum")
    )
    .sort_values("Revenue", ascending=False)
)

left, right = st.columns(2)

with left:
    fig = px.bar(
        category_data,
        x="product_category",
        y="Revenue",
        color="Revenue",
        title="Revenue by Category",
        labels={
            "product_category": "Category",
            "Revenue": "Revenue"
        }
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    fig = px.pie(
    category_data,
    names="product_category",
    values="Revenue",
    title="Category Revenue Share",
    hole=0.45,
    color_discrete_sequence=COFFEE_COLORS
)
    st.plotly_chart(fig, use_container_width=True)

# ---------- Product analysis ----------
st.header("Product Performance")

product_data = (
    filtered.groupby(
        ["product_id", "product_detail", "product_category"],
        as_index=False
    )
    .agg(
        Units=("transaction_qty", "sum"),
        Revenue=("revenue", "sum")
    )
)

product_data["Revenue Share (%)"] = (
    product_data["Revenue"] / total_revenue * 100
)

left, right = st.columns(2)

with left:
    top_revenue = product_data.nlargest(top_n, "Revenue")

    fig = px.bar(
        top_revenue.sort_values("Revenue"),
        x="Revenue",
        y="product_detail",
        color="product_category",
        orientation="h",
        title=f"Top {top_n} Products by Revenue"
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    top_volume = product_data.nlargest(top_n, "Units")

    fig = px.bar(
        top_volume.sort_values("Units"),
        x="Units",
        y="product_detail",
        color="product_category",
        orientation="h",
        title=f"Top {top_n} Products by Units Sold"
    )
    st.plotly_chart(fig, use_container_width=True)

# Popularity versus revenue
fig = px.scatter(
    product_data,
    x="Units",
    y="Revenue",
    color="product_category",
    hover_name="product_detail",
    size="Revenue",
    title="Product Popularity vs Revenue"
)
st.plotly_chart(fig, use_container_width=True)

# ---------- Store analysis ----------
st.header("Store Performance")

store_data = (
    filtered.groupby("store_location", as_index=False)
    .agg(
        Revenue=("revenue", "sum"),
        Units=("transaction_qty", "sum")
    )
    .sort_values("Revenue", ascending=False)
)

fig = px.bar(
    store_data,
    x="store_location",
    y="Revenue",
    color="store_location",
    title="Revenue by Store"
)
st.plotly_chart(fig, use_container_width=True)

# ---------- Product details ----------
st.header("Product Drill-Down")

display_data = product_data.sort_values(
    "Revenue", ascending=False
).copy()

display_data["Revenue"] = display_data["Revenue"].round(2)
display_data["Revenue Share (%)"] = (
    display_data["Revenue Share (%)"].round(2)
)

st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True
)

csv = display_data.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download Product Analysis CSV",
    data=csv,
    file_name="product_analysis_filtered.csv",
    mime="text/csv"
)

st.caption(
    "Revenue is quantity multiplied by unit price. "
    "Revenue does not represent profit because product costs "
    "are not available in the dataset."
)


# ---------- Pareto and Revenue Concentration ----------
st.header("Revenue Concentration & Pareto Analysis")


pareto = product_data.sort_values(
    "Revenue", ascending=False
).copy()

pareto["Revenue Share (%)"] = (
    pareto["Revenue"] / pareto["Revenue"].sum()
) * 100

pareto["Cumulative Revenue (%)"] = (
    pareto["Revenue Share (%)"].cumsum()
)

products_for_80 = int(
    (pareto["Cumulative Revenue (%)"] < 80).sum() + 1
)

actual_share = pareto["Cumulative Revenue (%)"].iloc[
    products_for_80 - 1
]

p1, p2, p3 = st.columns(3)
p1.metric("Products Analyzed", f"{len(pareto)}")
p2.metric("Products for 80% Revenue", f"{products_for_80}")
p3.metric("Revenue Share Reached", f"{actual_share:.2f}%")

fig = px.bar(
    pareto,
    x="product_detail",
    y="Revenue",
    title="Product Revenue Concentration",
    labels={
        "product_detail": "Product",
        "Revenue": "Revenue"
    },
    color_discrete_sequence=["#6F4E37"]
)

fig.add_scatter(
    x=pareto["product_detail"],
    y=pareto["Cumulative Revenue (%)"],
    name="Cumulative Revenue",
    mode="lines",
    yaxis="y2",
    line=dict(color="#C17C3A", width=3)
)

fig.update_layout(
    yaxis=dict(title="Revenue"),
    yaxis2=dict(
        title="Cumulative Revenue (%)",
        overlaying="y",
        side="right",
        range=[0, 105]
    ),
    xaxis_tickangle=-60,
    margin=dict(b=150),
    legend=dict(orientation="h", y=1.12)
)

fig.add_hline(
    y=80,
    yref="y2",
    line_dash="dash",
    line_color="#A33B20",
    annotation_text="80% threshold"
)

st.plotly_chart(fig, use_container_width=True)

# Long-tail products
st.subheader("Products Contributing Less Than 1% of Revenue")

long_tail = pareto[
    pareto["Revenue Share (%)"] < 1
].copy()

st.write(
    f"{len(long_tail)} products contribute less than 1% "
    "of the currently filtered revenue individually."
)

st.dataframe(
    long_tail[
        ["product_detail", "product_category",
         "Units", "Revenue", "Revenue Share (%)"]
    ].round(2),
    use_container_width=True,
    hide_index=True
)

