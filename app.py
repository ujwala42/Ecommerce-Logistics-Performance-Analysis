import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="E-Commerce Logistics Dashboard",
    page_icon="📦",
    layout="wide"
)

@st.cache_data
def load_data():
    df = pd.read_csv("data/processed_orders.csv")

    df['Order_Date'] = pd.to_datetime(df['Order_Date'])
    df['Month'] = df['Order_Date'].dt.strftime('%b %Y')

    return df

orders = load_data()

st.title("📦 E-Commerce Logistics Performance Dashboard")

st.write(
    "Analyze shipping performance, delivery delays, "
    "shipping modes, and regional performance."
)

# ---------------- FILTERS ----------------

st.sidebar.header("Dashboard Filters")

shipping_modes = st.sidebar.multiselect(
    "Shipping Mode",
    options=orders['Shipping_Mode'].unique(),
    default=orders['Shipping_Mode'].unique()
)

regions = st.sidebar.multiselect(
    "Region",
    options=orders['Order_Region'].unique(),
    default=orders['Order_Region'].unique()
)

states = st.sidebar.multiselect(
    "State",
    options=orders['Order_State'].unique(),
    default=orders['Order_State'].unique()
)

date_min = orders['Order_Date'].min().date()
date_max = orders['Order_Date'].max().date()

date_range = st.sidebar.date_input(
    "Order Date Range",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max
)

filtered_orders = orders[
    (orders['Shipping_Mode'].isin(shipping_modes)) &
    (orders['Order_Region'].isin(regions)) &
    (orders['Order_State'].isin(states))
].copy()

if len(date_range) == 2:

    start_date, end_date = date_range

    filtered_orders = filtered_orders[
        (filtered_orders['Order_Date'] >= pd.Timestamp(start_date)) &
        (filtered_orders['Order_Date'] < pd.Timestamp(end_date) + pd.Timedelta(days=1))
    ]

# ---------------- KPI CALCULATIONS ----------------

total_orders = len(filtered_orders)

if total_orders > 0:

    average_shipping = filtered_orders['Actual_Shipping_Days'].mean()

    on_time = filtered_orders['Delivery_Status'].isin(
        ['Advance shipping', 'Shipping on time']
    ).sum()

    delayed = (
        filtered_orders['Delivery_Status'] == 'Late delivery'
    ).sum()

    on_time_rate = on_time / total_orders * 100

    delay_rate = delayed / total_orders * 100

else:

    average_shipping = 0
    on_time_rate = 0
    delay_rate = 0

# ---------------- KPI CARDS ----------------

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Orders", f"{total_orders:,}")

col2.metric(
    "Average Shipping Days",
    f"{average_shipping:.2f} days"
)

col3.metric(
    "On-Time Delivery",
    f"{on_time_rate:.2f}%"
)

col4.metric(
    "Delayed Delivery",
    f"{delay_rate:.2f}%"
)

st.divider()

# ---------------- CHARTS ----------------

col1, col2 = st.columns(2)

with col1:

    status_data = filtered_orders['Delivery_Status'].value_counts().reset_index()

    fig = px.pie(
        status_data,
        names='Delivery_Status',
        values='count',
        title='Delivery Status Distribution'
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:

    mode_data = filtered_orders.groupby('Shipping_Mode').agg(
        Average_Days=('Actual_Shipping_Days', 'mean')
    ).reset_index()

    fig = px.bar(
        mode_data,
        x='Shipping_Mode',
        y='Average_Days',
        title='Average Shipping Days by Mode',
        color='Average_Days'
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------- MONTHLY ANALYSIS ----------------

filtered_orders['Month_Date'] = (
    filtered_orders['Order_Date'].dt.to_period('M').dt.to_timestamp()
)

monthly = filtered_orders.groupby('Month_Date').agg(
    Average_Days=('Actual_Shipping_Days', 'mean'),
    Total_Orders=('Order_ID', 'count')
).reset_index()

fig = px.line(
    monthly,
    x='Month_Date',
    y='Average_Days',
    markers=True,
    title='Monthly Average Shipping Duration'
)

st.plotly_chart(fig, use_container_width=True)

# ---------------- REGIONAL ANALYSIS ----------------

region = filtered_orders.groupby('Order_Region').agg(
    Total_Orders=('Order_ID', 'count'),
    Average_Days=('Actual_Shipping_Days', 'mean'),
    Delayed_Orders=('Delivery_Status', lambda x: (x == 'Late delivery').sum())
).reset_index()

region['Delay_Percentage'] = (
    region['Delayed_Orders'] / region['Total_Orders'] * 100
)

fig = px.bar(
    region,
    x='Order_Region',
    y='Delay_Percentage',
    color='Delay_Percentage',
    title='Delay Percentage by Region'
)

st.plotly_chart(fig, use_container_width=True)

# ---------------- DATA TABLE ----------------

st.subheader("Filtered Order Data")

st.dataframe(filtered_orders, use_container_width=True)

# ---------------- DOWNLOAD ----------------

csv = filtered_orders.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Download Filtered Data",
    data=csv,
    file_name="filtered_logistics_data.csv",
    mime="text/csv"
)

# ---------------- INSIGHTS ----------------

st.subheader("Business Insights")

if not filtered_orders.empty:

    slowest_mode = (
        filtered_orders.groupby('Shipping_Mode')['Actual_Shipping_Days']
        .mean()
        .idxmax()
    )

    highest_delay_region = region.loc[
        region['Delay_Percentage'].idxmax(),
        'Order_Region'
    ]

    st.write(
        f"• The slowest shipping mode based on average duration is **{slowest_mode}**."
    )

    st.write(
        f"• The region with the highest delay percentage is **{highest_delay_region}**."
    )

    st.write(
        f"• The overall delivery delay rate for the selected filters is **{delay_rate:.2f}%**."
    )