# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO


# -------------------------- Page Config --------------------------
st.set_page_config(
    page_title="Zara Jackets Sales Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Zara Jackets: Seasonal, Material & Origin Performance")
st.markdown("### Interactive analysis of Seasonal • Season • Material • Origin • Sales Volume")

# -------------------------- Data Loading --------------------------
# Try to load the real dataset first (works locally + when deployed with the file)
try:
    # This works when salesdata.csv is in the same folder
    df = pd.read_csv("./Business_sales_EDA.csv", sep=None, engine="python")
    data_source = "./Business_sales_EDA.csv"
except FileNotFoundError:
    # Fallback: let user upload the file (useful when testing online without the CSV yet)
    st.warning("salesdata.csv not found in project folder → please upload it below")
    uploaded = st.file_uploader("./Business_sales_EDA.csv", type=["csv"])
    if uploaded is not None:
        df = pd.read_csv(uploaded, sep=None, engine="python")
        data_source = "uploaded file"
    else:
        st.info("Waiting for salesdata.csv upload...")
        st.stop()
else:
    st.success(f"Loaded {len(df):,} rows from {data_source}")

# -------------------------- Data Cleaning --------------------------
df['Sales Volume'] = pd.to_numeric(df['Sales Volume'], errors='coerce')
df['price'] = pd.to_numeric(df['price'], errors='coerce')

# Optional: compute revenue for extra insights
df['Revenue'] = df['price'] * df['Sales Volume']

# -------------------------- Sidebar Filters --------------------------
st.sidebar.header("Filters")

seasonal_filter = st.sidebar.multiselect(
    "Seasonal Collection", 
    options=sorted(df['Seasonal'].dropna().unique()),
    default=df['Seasonal'].dropna().unique()
)

season_filter = st.sidebar.multiselect(
    "Season", 
    options=sorted(df['season'].dropna().unique()),
    default=df['season'].dropna().unique()
)

material_filter = st.sidebar.multiselect(
    "Material", 
    options=sorted(df['material'].dropna().unique()),
    default=df['material'].dropna().unique()
)

origin_filter = st.sidebar.multiselect(
    "Country of Origin", 
    options=sorted(df['origin'].dropna().unique()),
    default=df['origin'].dropna().unique()
)

# Price range filter (optional but very useful)
price_range = st.sidebar.slider(
    "Price Range (USD)",
    min_value=0,
    max_value=int(df['price'].max()) if df['price'].max() else 200,
    value=(0, int(df['price'].max())) if df['price'].max() else (0, 200)
)

# Apply all filters
data = df[
    (df['Seasonal'].isin(seasonal_filter)) &
    (df['season'].isin(season_filter)) &
    (df['material'].isin(material_filter)) &
    (df['origin'].isin(origin_filter)) &
    (df['price'].between(price_range[0], price_range[1]))
].copy()

# -------------------------- Key Metrics --------------------------
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Units Sold", f"{data['Sales Volume'].sum():,}")
with col2:
    st.metric("Total Revenue", f"${data['Revenue'].sum():,.0f}")
with col3:
    st.metric("Number of SKUs", len(data))
with col4:
    st.metric("Top Material", data['material'].mode()[0] if not data.empty else "N/A")

st.markdown("---")

# -------------------------- GRAPH 1: Seasonal vs Non-Seasonal --------------------------
st.subheader("1. Do Seasonal Collections Actually Sell More?")
seasonal_sales = data.groupby('Seasonal')['Sales Volume'].sum().reset_index()
fig1 = px.bar(seasonal_sales, x='Seasonal', y='Sales Volume',
              color='Seasonal', text='Sales Volume',
              color_discrete_map={'Yes': '#FF6B6B', 'No': '#1A936F'},
              title="Sales Volume: Seasonal vs Regular Items")
fig1.update_traces(textposition='outside')
fig1.update_layout(showlegend=False)
st.plotly_chart(fig1, use_container_width=True)

# -------------------------- GRAPH 2: Season × Material Treemap --------------------------
st.subheader("2. Which Materials Win Each Season?")
season_mat = data.groupby(['season', 'material'])['Sales Volume'].sum().reset_index()

season_order = ['Spring', 'Summer', 'Autumn', 'Winter']
season_mat['season'] = pd.Categorical(season_mat['season'], categories=season_order, ordered=True)
season_mat = season_mat.sort_values('season')

fig2 = px.treemap(season_mat,
                  path=['season', 'material'],
                  values='Sales Volume',
                  color='Sales Volume',
                  color_continuous_scale='Oranges',
                  title="Sales Volume by Season & Material")
st.plotly_chart(fig2, use_container_width=True)

# -------------------------- GRAPH 3: Top 20 Best Sellers --------------------------
st.subheader("3. Top 20 Best-Selling Jackets")
top20 = data.nlargest(20, 'Sales Volume')

fig3 = px.bar(top20, y='name', x='Sales Volume',
              color='season',
              hover_data=['material', 'origin', 'price', 'Seasonal'],
              text='Sales Volume',
              orientation='h',
              title="Top 20 Best-Selling Jackets")
fig3.update_layout(height=700, yaxis={'categoryorder': 'total ascending'})
fig3.update_traces(textposition='outside')
st.plotly_chart(fig3, use_container_width=True)

# -------------------------- GRAPH 4: Origin Country Performance --------------------------
st.subheader("4. Which Countries Produce the Best Sellers?")
origin_sales = data.groupby('origin')['Sales Volume'].sum().sort_values(ascending=False).reset_index()
fig4 = px.bar(origin_sales, x='origin', y='Sales Volume',
              color='origin', text='Sales Volume',
              title="Sales Volume by Country of Origin")
fig4.update_traces(textposition='outside')
st.plotly_chart(fig4, use_container_width=True)

# -------------------------- Detailed Table --------------------------
st.markdown("---")
st.subheader("Filtered Data Table")
display_cols = ['name', 'Sales Volume', 'Revenue', 'price', 'season', 'material', 'origin', 'Seasonal', 'section']
st.dataframe(
    data[display_cols].sort_values('Sales Volume', ascending=False).reset_index(drop=True),
    use_container_width=True
)

# -------------------------- Download Filtered Data --------------------------
csv = data.to_csv(index=False, sep=',')
st.download_button(
    label="Download filtered data as CSV",
    data=csv,
    file_name="zara_filtered_sales.csv",
    mime="text/csv"
)

