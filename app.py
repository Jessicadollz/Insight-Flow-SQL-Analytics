import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
import numpy as np

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Insight Flow SQL Analytics",
    page_icon="📊",
    layout="wide"
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

/* Main Background */
.main {
    background-color: #0E1117;
    color: white;
}

/* Headings */
h1, h2, h3 {
    color: white;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #161A23;
}

/* Metric Cards */
[data-testid="metric-container"] {
    background-color: #1E1E1E;
    border: 1px solid #2E8B57;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.3);
}

/* Text Input */
.stTextInput input {
    background-color: #1E1E1E;
    color: white;
    border: 2px solid #2E8B57;
    border-radius: 10px;
}

/* Green Glow */
.stTextInput input:focus {
    border-color: #00FF7F !important;
    box-shadow: 0 0 12px #00FF7F !important;
}

/* Buttons */
.stButton button {
    background-color: #2E8B57;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px 20px;
}

.stButton button:hover {
    background-color: #3CB371;
    color: white;
}

/* Selectbox */
.stSelectbox div[data-baseweb="select"] {
    background-color: #1E1E1E;
    color: white;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# DATABASE CONNECTION
# =========================================================

conn = sqlite3.connect('insightflow.db')

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown("""
# 📊 Insight Flow

### Business Intelligence Platform
""")

st.sidebar.title("📌 Filters")

states = pd.read_sql(
    "SELECT DISTINCT customer_state FROM fact_orders ORDER BY customer_state",
    conn
)

selected_state = st.sidebar.selectbox(
    "Select State",
    states['customer_state']
)

# =========================================================
# DATE FILTER
# =========================================================

st.sidebar.subheader("📅 Date Filter")

date_range = pd.read_sql("""
SELECT 
MIN(order_purchase_timestamp) AS min_date,
MAX(order_purchase_timestamp) AS max_date
FROM fact_orders
""", conn)

min_date = pd.to_datetime(date_range['min_date'][0])
max_date = pd.to_datetime(date_range['max_date'][0])

start_date = st.sidebar.date_input(
    "Start Date",
    min_date
)

end_date = st.sidebar.date_input(
    "End Date",
    max_date
)

if start_date > end_date:
    st.sidebar.error("⚠️ Start Date cannot be greater than End Date")
    st.stop()

# =========================================================
# TITLE
# =========================================================

st.title("📊 Insight Flow SQL Analytics")

# =========================================================
# TABS
# =========================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "📈 Revenue Analytics",
    "🎯 RFM Analysis",
    "🤖 Talk-To-AI",
    "🧠 AI Insights"
])

# =========================================================
# FILTERED DATA
# =========================================================

filtered_df = pd.read_sql(f"""
SELECT *
FROM fact_orders
WHERE customer_state = '{selected_state}'
AND DATE(order_purchase_timestamp)
BETWEEN '{start_date}' AND '{end_date}'
""", conn)

if filtered_df.empty:
    st.warning("⚠️ No data available for selected filters.")
    st.stop()

# =========================================================
# LOADING SPINNER
# =========================================================

with st.spinner("Loading analytics dashboard..."):
    st.success("Analytics loaded successfully!")

# =========================================================
# TAB 1 - DASHBOARD
# =========================================================

with tab1:

    total_revenue = round(filtered_df["total_payment"].sum(), 2)
    total_orders = filtered_df["order_id"].nunique()
    total_customers = filtered_df["customer_id"].nunique()

    avg_order_value = round(
        total_revenue / total_orders, 2
    ) if total_orders != 0 else 0

    repeat_customers = filtered_df["customer_id"].duplicated().sum()

    repeat_rate = round(
        (repeat_customers / total_customers) * 100,
        2
    ) if total_customers != 0 else 0

    # Orders over time query
    orders_time_query = f"""
    SELECT DATE(order_purchase_timestamp) AS date,
           COUNT(*) AS orders
    FROM fact_orders
    WHERE customer_state = '{selected_state}'
    AND DATE(order_purchase_timestamp)
    BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY date
    ORDER BY date
    """

    orders_df = pd.read_sql(orders_time_query, conn)

    avg_daily_orders = round(
        total_orders / max(len(orders_df), 1),
        2
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "💰 Total Revenue",
            f"${total_revenue:,.2f}"
        )

        st.metric(
            "🔁 Repeat Customer %",
            f"{repeat_rate}%"
        )

    with col2:
        st.metric(
            "📦 Total Orders",
            total_orders
        )

        st.metric(
            "📅 Avg Daily Orders",
            avg_daily_orders
        )

    with col3:
        st.metric(
            "👥 Customers",
            total_customers
        )

        st.metric(
            "🛒 Avg Order Value",
            f"${avg_order_value}"
        )

    st.divider()

    # ORDERS OVER TIME

    st.subheader(
        f"📈 Orders Over Time — {selected_state}"
    )

    fig2 = px.line(
        orders_df,
        x='date',
        y='orders',
        title=f'Orders Trend — {selected_state}',
        markers=True
    )

    st.plotly_chart(fig2, use_container_width=True)

# =========================================================
# TAB 2 - REVENUE ANALYTICS
# =========================================================

with tab2:

    # REVENUE BY STATE

    st.subheader("📍 Revenue by State")

    state_query = """
    SELECT customer_state,
           ROUND(SUM(total_payment),2) AS revenue
    FROM fact_orders
    GROUP BY customer_state
    ORDER BY revenue DESC
    LIMIT 10
    """

    state_df = pd.read_sql(state_query, conn)

    fig = px.bar(
        state_df,
        x='customer_state',
        y='revenue',
        color='revenue',
        title='Revenue by State'
    )

    st.plotly_chart(fig, use_container_width=True)

    # REVENUE DISTRIBUTION

    st.subheader("🧭 Revenue Distribution")

    payment_chart = pd.read_sql("""
    SELECT customer_state,
           SUM(total_payment) AS revenue
    FROM fact_orders
    GROUP BY customer_state
    ORDER BY revenue DESC
    LIMIT 10
    """, conn)

    fig_pie = px.pie(
        payment_chart,
        values='revenue',
        names='customer_state',
        title='Revenue Distribution by State'
    )

    st.plotly_chart(fig_pie, use_container_width=True)

    # MONTHLY REVENUE

    st.subheader(
        f"📅 Monthly Revenue Trend — {selected_state}"
    )

    monthly_query = f"""
    SELECT 
    strftime('%Y-%m', order_purchase_timestamp) AS month,
    ROUND(SUM(total_payment),2) AS revenue
    FROM fact_orders
    WHERE customer_state = '{selected_state}'
    GROUP BY month
    ORDER BY month
    """

    monthly_df = pd.read_sql(monthly_query, conn)

    fig_monthly = px.line(
        monthly_df,
        x='month',
        y='revenue',
        markers=True,
        title='Monthly Revenue Trend'
    )

    st.plotly_chart(fig_monthly, use_container_width=True)

    # WEEKDAY ORDERS

    st.subheader(
        f"📅 Orders by Weekday — {selected_state}"
    )

    weekday_query = f"""
    SELECT 
    CASE strftime('%w', order_purchase_timestamp)
        WHEN '1' THEN 'Monday'
        WHEN '2' THEN 'Tuesday'
        WHEN '3' THEN 'Wednesday'
        WHEN '4' THEN 'Thursday'
        WHEN '5' THEN 'Friday'
        WHEN '6' THEN 'Saturday'
        WHEN '0' THEN 'Sunday'
    END AS weekday,

    COUNT(*) AS orders,

    CASE strftime('%w', order_purchase_timestamp)
        WHEN '1' THEN 1
        WHEN '2' THEN 2
        WHEN '3' THEN 3
        WHEN '4' THEN 4
        WHEN '5' THEN 5
        WHEN '6' THEN 6
        WHEN '0' THEN 7
    END AS weekday_order

    FROM fact_orders

    WHERE customer_state = '{selected_state}'

    GROUP BY weekday, weekday_order

    ORDER BY weekday_order
    """

    weekday_df = pd.read_sql(weekday_query, conn)

    fig_weekday = px.bar(
        weekday_df,
        x='weekday',
        y='orders',
        color='orders',
        title='Orders by Weekday'
    )

    st.plotly_chart(fig_weekday, use_container_width=True)

    # TOP CITIES

    st.subheader(
        f"🏙️ Top Cities by Revenue — {selected_state}"
    )

    city_query = f"""
    SELECT customer_city,
           ROUND(SUM(total_payment),2) AS revenue
    FROM fact_orders
    WHERE customer_state = '{selected_state}'
    GROUP BY customer_city
    ORDER BY revenue DESC
    LIMIT 10
    """

    city_df = pd.read_sql(city_query, conn)

    fig_city = px.bar(
        city_df,
        x='revenue',
        y='customer_city',
        orientation='h',
        color='revenue',
        title='Top Cities by Revenue'
    )

    st.plotly_chart(fig_city, use_container_width=True)

    # HEATMAP

    st.subheader(
        f"🔥 Orders Heatmap — {selected_state}"
    )

    heatmap_query = f"""
    SELECT

    strftime('%m', order_purchase_timestamp) AS month,

    CASE strftime('%w', order_purchase_timestamp)
        WHEN '1' THEN 'Monday'
        WHEN '2' THEN 'Tuesday'
        WHEN '3' THEN 'Wednesday'
        WHEN '4' THEN 'Thursday'
        WHEN '5' THEN 'Friday'
        WHEN '6' THEN 'Saturday'
        WHEN '0' THEN 'Sunday'
    END AS weekday,

    COUNT(*) AS orders

    FROM fact_orders

    WHERE customer_state = '{selected_state}'

    GROUP BY month, weekday
    """

    heatmap_df = pd.read_sql(heatmap_query, conn)

    heatmap_pivot = heatmap_df.pivot(
        index='weekday',
        columns='month',
        values='orders'
    )

    fig_heatmap = px.imshow(
        heatmap_pivot,
        text_auto=True,
        aspect="auto",
        title="Orders Heatmap"
    )

    st.plotly_chart(fig_heatmap, use_container_width=True)

# =========================================================
# TAB 3 - RFM ANALYSIS
# =========================================================

with tab3:

    st.subheader(
        f"🎯 RFM Analysis — {selected_state}"
    )

    rfm_query = f"""
    SELECT customer_id,
           COUNT(order_id) AS frequency,
           ROUND(SUM(total_payment),2) AS monetary
    FROM fact_orders
    WHERE customer_state = '{selected_state}'
    GROUP BY customer_id
    ORDER BY monetary DESC
    LIMIT 20
    """

    rfm_df = pd.read_sql(rfm_query, conn)

    fig3 = px.scatter(
        rfm_df,
        x='frequency',
        y='monetary',
        hover_data=['customer_id'],
        title='Customer Segmentation'
    )

    st.plotly_chart(fig3, use_container_width=True)

# =========================================================
# TAB 4 - TALK TO AI
# =========================================================

with tab4:

    st.subheader(
        f"🤖 Talk-To-AI — {selected_state}"
    )

    question = st.text_input(
        "Ask a business question"
    )

    def ask_question(question):

        question = question.lower()

        if "revenue" in question:
            query = f"""
            SELECT ROUND(SUM(total_payment),2) AS revenue
            FROM fact_orders
            WHERE customer_state = '{selected_state}'
            """

        elif "top customers" in question:
            query = f"""
            SELECT customer_id,
                   ROUND(SUM(total_payment),2) AS revenue
            FROM fact_orders
            WHERE customer_state = '{selected_state}'
            GROUP BY customer_id
            ORDER BY revenue DESC
            LIMIT 5
            """

        elif "top cities" in question:
            query = f"""
            SELECT customer_city,
                   ROUND(SUM(total_payment),2) AS revenue
            FROM fact_orders
            WHERE customer_state = '{selected_state}'
            GROUP BY customer_city
            ORDER BY revenue DESC
            LIMIT 10
            """

        else:
            return "❌ Question not understood."

        return pd.read_sql(query, conn)

    if st.button("Run Query"):
        result = ask_question(question)
        st.write(result)

# =========================================================
# TAB 5 - AI INSIGHTS
# =========================================================

with tab5:

    st.subheader("🧠 AI Insights")

    top_state = state_df.iloc[0]['customer_state']
    top_state_revenue = state_df.iloc[0]['revenue']

    top_day = weekday_df.iloc[0]['weekday']
    top_day_orders = weekday_df.iloc[0]['orders']

    top_city = city_df.iloc[0]['customer_city']

    st.success(
        f"📈 {top_state} generated highest revenue "
        f"with ${top_state_revenue:,.2f}"
    )

    st.info(
        f"🛒 {top_day} recorded highest orders "
        f"({top_day_orders} orders)"
    )

    st.warning(
        f"🏙️ Top performing city is {top_city}"
    )

    st.markdown("### 💡 Smart Recommendations")

    if top_day == "Friday":

        st.write("""
        ✅ Friday has peak customer activity.
        Increase ad campaigns and discounts on Fridays.
        """)

    else:

        st.write(f"""
        ✅ {top_day} is the strongest sales day.
        Optimize promotions for this weekday.
        """)
# ============================================================
# MACHINE LEARNING SECTION
# ============================================================

st.markdown("---")
st.header("🤖 Machine Learning Analytics")

ml_tab1, ml_tab2 = st.tabs([
    "📈 Revenue Prediction",
    "🎯 Customer Segmentation"
])

# ============================================================
# 1. REVENUE PREDICTION
# ============================================================

with ml_tab1:

    st.subheader(
        f"📈 Revenue Forecasting for {selected_state}"
    )

    revenue_prediction_query = f"""
    SELECT 
        strftime('%Y-%m', order_purchase_timestamp) AS month,
        ROUND(SUM(total_payment),2) AS revenue
    FROM fact_orders
    WHERE customer_state = '{selected_state}'
    AND DATE(order_purchase_timestamp)
    BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY month
    ORDER BY month
    """

    prediction_df = pd.read_sql(
        revenue_prediction_query,
        conn
    )

    # ML MODEL

    prediction_df["month_number"] = np.arange(len(prediction_df))

    X = prediction_df[["month_number"]]
    y = prediction_df["revenue"]

    model = LinearRegression()
    model.fit(X, y)

    future_months = 6

    future_x = np.arange(
        len(prediction_df),
        len(prediction_df) + future_months
    ).reshape(-1, 1)

    predicted_revenue = model.predict(future_x)

    future_df = pd.DataFrame({
        "month_number": future_x.flatten(),
        "predicted_revenue": predicted_revenue
    })

    # CREATE FUTURE MONTH LABELS

    last_month = pd.to_datetime(
        prediction_df["month"].iloc[-1]
    )

    future_dates = pd.date_range(
        last_month,
        periods=future_months + 1,
        freq='M'
    )[1:]

    future_df["month"] = future_dates.strftime("%Y-%m")

    # CHART

    fig_prediction = px.line(
        prediction_df,
        x="month",
        y="revenue",
        markers=True,
        title=f"Actual Revenue Trend — {selected_state}"
    )

    fig_prediction.add_scatter(
        x=future_df["month"],
        y=future_df["predicted_revenue"],
        mode='lines+markers',
        name='Predicted Revenue'
    )

    fig_prediction.update_layout(
        plot_bgcolor="#0E1117",
        paper_bgcolor="#0E1117",
        font_color="white"
    )

    st.plotly_chart(
        fig_prediction,
        use_container_width=True
    )

    st.success(
        f"✅ Revenue forecast generated for next {future_months} months"
    )

# ============================================================
# 2. CUSTOMER SEGMENTATION
# ============================================================

with ml_tab2:

    st.subheader(
        f"🎯 AI Customer Segmentation — {selected_state}"
    )

    segmentation_query = f"""
    SELECT
        customer_id,
        COUNT(order_id) AS frequency,
        ROUND(SUM(total_payment),2) AS monetary
    FROM fact_orders
    WHERE customer_state = '{selected_state}'
    AND DATE(order_purchase_timestamp)
    BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY customer_id
    LIMIT 500
    """

    segmentation_df = pd.read_sql(
        segmentation_query,
        conn
    )

    # KMEANS

    features = segmentation_df[
        ["frequency", "monetary"]
    ]

    kmeans = KMeans(
        n_clusters=3,
        random_state=42
    )

    segmentation_df["cluster"] = kmeans.fit_predict(features)

    # RENAME SEGMENTS

    segment_names = {
        0: "Regular Customers",
        1: "Premium Customers",
        2: "High Value Customers"
    }

    segmentation_df["segment"] = segmentation_df[
        "cluster"
    ].map(segment_names)

    # SCATTER PLOT

    fig_cluster = px.scatter(
        segmentation_df,
        x="frequency",
        y="monetary",
        color="segment",
        hover_data=["customer_id"],
        title=f"AI Customer Segmentation — {selected_state}"
    )

    fig_cluster.update_layout(
        plot_bgcolor="#0E1117",
        paper_bgcolor="#0E1117",
        font_color="white"
    )

    st.plotly_chart(
        fig_cluster,
        use_container_width=True
    )

    # SEGMENT COUNTS

    segment_count = segmentation_df[
        "segment"
    ].value_counts().reset_index()

    segment_count.columns = [
        "Customer Segment",
        "Count"
    ]

    st.dataframe(
        segment_count,
        use_container_width=True
    )

    st.success(
        "✅ AI customer segmentation completed successfully"
    )
    
# =========================================================
# FOOTER
# =========================================================

st.markdown("""
<hr style='border:1px solid #2E8B57'>

<div style='text-align:center;
padding:10px;
color:gray;'>

Built with ❤️ using Streamlit • SQL • Plotly • Python

</div>
""", unsafe_allow_html=True)