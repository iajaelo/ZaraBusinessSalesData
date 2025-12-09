# app.py - Zara Clothing Sales Dashboard (Works with Full Dataset)
import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO

# -------------------------- Page Setup --------------------------
st.set_page_config(page_title="Zara Sales Dashboard", layout="wide", initial_sidebar_state="expanded")
st.title("Zara Clothing Sales Dashboard")

# st.markdown("Upload your full `salesdata.csv` or any similar fashion sales dataset to explore insights interactively.")



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
# Make a copy to avoid warnings
df = df.copy()

# Standardize common column names (case-insensitive match)
df.columns = df.columns.str.strip()
col_map = {
    'product_name': 'name',
    'productname': 'name',
    'item': 'name',
    'price': 'price',
    'sales_volume': 'Sales Volume',
    'salesvolume': 'Sales Volume',
    'units_sold': 'Sales Volume',
    'unitssold': 'Sales Volume',
    'quantity': 'Sales Volume',
    'revenue': 'Revenue',
    'promotion': 'Promotion',
    'product_position': 'Product Position',
    'position': 'Product Position',
    'seasonal': 'Seasonal',
    'section': 'section',
    'gender': 'section',
    'season': 'season',
    'material': 'material',
    'fabric': 'material'
}

for old, new in col_map.items():
    for col in df.columns:
        if col.lower() == old:
            df.rename(columns={col: new}, inplace=True)

# Convert price and sales volume
df['price'] = pd.to_numeric(df['price'], errors='coerce')
if 'Sales Volume' not in df.columns:
    possible_sales_cols = ['units_sold', 'quantity', 'sales_volume', 'sales', 'units']
    for col in possible_sales_cols:
        if col in df.columns.str.lower():
            df['Sales Volume'] = pd.to_numeric(df[df.columns[df.columns.str.lower() == col].iloc[0]], errors='coerce')
            break

df['Sales Volume'] = pd.to_numeric(df.get('Sales Volume', 0), errors='coerce')

# Drop rows with no price or sales (critical)
df.dropna(subset=['price', 'Sales Volume'], inplace=True)

# Calculate Revenue
df['Revenue'] = df['price'] * df['Sales Volume']

# Fill missing categorical values
cat_cols = ['Promotion', 'Product Position', 'Seasonal', 'section', 'season', 'material', 'name']
for col in cat_cols:
    if col in df.columns:
        df[col] = df[col].fillna("Unknown").astype(str)
    else:
        df[col] = "Unknown"

# Ensure 'name' exists
if 'name' not in df.columns:
    df['name'] = df.get('product_name', 'Product ' + df.index.astype(str))

# -------------------------- Sidebar Filters --------------------------
st.sidebar.header("Filters")

# Get unique values safely
def get_unique(col):
    return sorted([x for x in df[col].unique() if pd.notna(x)])

promotion_opts = get_unique('Promotion')
position_opts = get_unique('Product Position')
seasonal_opts = get_unique('Seasonal')
section_opts = get_unique('section')
season_opts = get_unique('season')
material_opts = get_unique('material')

promotion = st.sidebar.multiselect("Promotion", options=promotion_opts, default=promotion_opts)
position = st.sidebar.multiselect("Product Position", options=position_opts, default=position_opts)
seasonal = st.sidebar.multiselect("Seasonal", options=seasonal_opts, default=seasonal_opts)
section = st.sidebar.multiselect("Section (Gender)", options=section_opts, default=section_opts)
season = st.sidebar.multiselect("Season", options=season_opts, default=season_opts)
material = st.sidebar.multiselect("Material", options=material_opts, default=material_opts)

# Price range
price_min, price_max = float(df['price'].min()), float(df['price'].max())
price_range = st.sidebar.slider(
    "Price Range ($)",
    min_value=price_min,
    max_value=price_max,
    value=(price_min, price_max),
    step=1.0
)

# Apply all filters
filtered_df = df[
    (df['Promotion'].isin(promotion)) &
    (df['Product Position'].isin(position)) &
    (df['Seasonal'].isin(seasonal)) &
    (df['section'].isin(section)) &
    (df['season'].isin(season)) &
    (df['material'].isin(material)) &
    (df['price'].between(price_range[0], price_range[1]))
].copy()

# -------------------------- Dashboard Metrics --------------------------
st.markdown("## Key Metrics")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Products", f"{len(filtered_df):,}")
c2.metric("Total Units Sold", f"{filtered_df['Sales Volume'].sum():,}")
c3.metric("Total Revenue", f"${filtered_df['Revenue'].sum():,.0f}")
c4.metric("Average Price", f"${filtered_df['price'].mean():.2f}")

st.markdown("---")

# -------------------------- Charts --------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Sales Volume by Product Position")
    pos_data = filtered_df.groupby('Product Position')['Sales Volume'].sum().sort_values(ascending=False)
    fig1 = px.bar(x=pos_data.index, y=pos_data.values, text=pos_data.values,
                  color=pos_data.index, labels={'x': 'Position', 'y': 'Units Sold'})
    fig1.update_traces(textposition='outside')
    fig1.update_layout(showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Revenue Share by Season")
    season_data = filtered_df.groupby('season')['Revenue'].sum()
    if not season_data.empty:
        fig2 = px.pie(values=season_data.values, names=season_data.index,
                      color_discrete_sequence=px.colors.sequential.Plasma)
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 10 Best-Selling Products")
    top10 = filtered_df.nlargest(10, 'Sales Volume')
    fig3 = px.bar(top10, x='name', y='Sales Volume', color='price',
                  text='Sales Volume', hover_data=['section', 'Promotion'])
    fig3.update_xaxes(tickangle=45)
    fig3.update_traces(textposition='outside')
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    st.subheader("Price vs Sales Volume (Size = Revenue)")
    fig4 = px.scatter(filtered_df, x='price', y='Sales Volume',
                      size='Revenue', color='Promotion',
                      hover_name='name', hover_data=['section', 'season', 'material'],
                      size_max=60)
    fig4.update_layout(xaxis_title="Price ($)", yaxis_title="Units Sold")
    st.plotly_chart(fig4, use_container_width=True)


# -------------------------- GRAPH: Origin Country Performance --------------------------
st.subheader("Which Countries Produce the Best Sellers?")
origin_sales = df.groupby('origin')['Sales Volume'].sum().sort_values(ascending=False).reset_index()
fig4 = px.bar(origin_sales, x='origin', y='Sales Volume',
              color='origin', text='Sales Volume',
              title="Sales Volume by Country of Origin")
fig4.update_traces(textposition='outside')
st.plotly_chart(fig4, use_container_width=True)


# -------------------------- Data Table & Export --------------------------
st.markdown("---")
st.subheader(f"Filtered Data Table ({len(filtered_df):,} rows)")
st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True, height=400)

st.download_button(
    label="Download Filtered Data as CSV",
    data=filtered_df.to_csv(index=False),
    file_name=f"zara_filtered_sales_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

st.success("Dashboard ready! Your full dataset is loaded and interactive.")