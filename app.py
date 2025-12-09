# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO

# Page config
st.set_page_config(page_title="Zara Sales Dashboard", layout="wide")
st.title("Zara Clothing Sales Dashboard")

# Sidebar - Data input
st.sidebar.header("Upload or Paste Data")

# Option to upload file
uploaded_file = st.sidebar.file_uploader("Upload your CSV/TSV file", type=["csv", "tsv"])

# Option to paste TSV data
data_source = st.sidebar.radio(
    "Or paste TSV data below:",
    options=["Upload file", "Paste TSV data"]
)

df = None

# Load data based on user choice
if data_source == "Upload file" and uploaded_file is not None:
    try:
        # Auto-detect delimiter
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        st.success(f"File '{uploaded_file.name}' loaded successfully!")
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

elif data_source == "Paste TSV data":
    pasted = st.sidebar.text_area("Paste your TSV data here (tab-separated)", height=300)
    if pasted.strip():
        try:
            df = pd.read_csv(StringIO(pasted), sep='\t')
            st.success("Pasted data loaded successfully!")
        except Exception as e:
            st.error(f"Error reading pasted data: {e}. Make sure it's tab-separated.")
            st.stop()

# If no data loaded yet
if df is None:
    st.info("Upload a CSV/TSV file or paste TSV data in the sidebar to begin.")
    st.stop()

# Basic cleaning
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['Sales Volume'] = pd.to_numeric(df['Sales Volume'], errors='coerce')

# Drop rows where critical numeric columns failed to convert
df = df.dropna(subset=['price', 'Sales Volume'])

# Calculate Revenue
df['Revenue'] = df['price'] * df['Sales Volume']

# Sidebar filters
st.sidebar.header("Filters")

# Ensure categorical columns exist and handle missing values
categorical_cols = ['Promotion', 'Product Position', 'Seasonal', 'section', 'season', 'material']
for col in categorical_cols:
    if col not in df.columns:
        df[col] = "Unknown"
    df[col] = df[col].fillna("Unknown").astype(str)

# Multi-select filters with safe defaults
promotion = st.sidebar.multiselect(
    "Promotion", 
    options=sorted(df['Promotion'].unique()), 
    default=sorted(df['Promotion'].unique())
)

position = st.sidebar.multiselect(
    "Product Position", 
    options=sorted(df['Product Position'].unique()), 
    default=sorted(df['Product Position'].unique())
)

seasonal = st.sidebar.multiselect(
    "Seasonal", 
    options=sorted(df['Seasonal'].unique()), 
    default=sorted(df['Seasonal'].unique())
)

section = st.sidebar.multiselect(
    "Section (Gender)", 
    options=sorted(df['section'].unique()), 
    default=sorted(df['section'].unique())
)

season = st.sidebar.multiselect(
    "Season", 
    options=sorted(df['season'].unique()), 
    default=sorted(df['season'].unique())
)

material = st.sidebar.multiselect(
    "Material", 
    options=sorted(df['material'].unique()), 
    default=sorted(df['material'].unique())
)

# Price range slider (only if price has valid values)
if df['price'].nunique() > 0:
    price_min = float(df['price'].min())
    price_max = float(df['price'].max())
    price_range = st.sidebar.slider(
        "Price Range", 
        min_value=price_min, 
        max_value=price_max, 
        value=(price_min, price_max)
    )
else:
    price_range = (0, 1000)  # fallback
    st.sidebar.warning("No valid price data found.")

# Apply filters
filtered_df = df[
    (df['Promotion'].isin(promotion)) &
    (df['Product Position'].isin(position)) &
    (df['Seasonal'].isin(seasonal)) &
    (df['section'].isin(section)) &
    (df['season'].isin(season)) &
    (df['material'].isin(material)) &
    (df['price'].between(price_range[0], price_range[1]))
].copy()

# Main dashboard metrics
st.markdown("### Key Metrics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Products", len(filtered_df))
with col2:
    st.metric("Total Sales Volume", f"{filtered_df['Sales Volume'].sum():,}")
with col3:
    total_rev = filtered_df['Revenue'].sum()
    st.metric("Total Revenue", f"${total_rev:,.0f}")
with col4:
    avg_price = filtered_df['price'].mean()
    st.metric("Average Price", f"${avg_price:.2f}" if pd.notna(avg_price) else "N/A")

st.markdown("---")

# Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("Sales Volume by Product Position")
    pos_sales = filtered_df.groupby('Product Position')['Sales Volume'].sum().sort_values(ascending=False).reset_index()
    fig1 = px.bar(pos_sales, x='Product Position', y='Sales Volume', 
                  color='Product Position', text='Sales Volume',
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig1.update_traces(textposition='outside')
    fig1.update_layout(showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Revenue Share by Season")
    season_rev = filtered_df.groupby('season')['Revenue'].sum().reset_index()
    if not season_rev.empty:
        fig2 = px.pie(season_rev, values='Revenue', names='season', 
                      color_discrete_sequence=px.colors.sequential.Plasma)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.write("No data for pie chart.")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 10 Best-Selling Products")
    top10 = filtered_df.sort_values('Sales Volume', ascending=False).head(10)
    if not top10.empty:
        fig3 = px.bar(top10, x='name', y='Sales Volume', color='price',
                      hover_data=['Product Position', 'Promotion', 'section', 'season'],
                      text='Sales Volume', color_continuous_scale='Viridis')
        fig3.update_layout(xaxis_title="Product Name", yaxis_title="Units Sold")
        fig3.update_traces(textposition='outside')
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.write("No data to display.")

with col2:
    st.subheader("Price vs Sales Volume (Bubble Size = Revenue)")
    if not filtered_df.empty:
        fig4 = px.scatter(filtered_df, x='price', y='Sales Volume', size='Revenue',
                          color='Promotion', hover_name='name',
                          hover_data=['section', 'season', 'material', 'Product Position'],
                          size_max=60)
        fig4.update_layout(xaxis_title="Price (USD)", yaxis_title="Units Sold")
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.write("No data for scatter plot.")

st.markdown("---")

# Detailed table
st.subheader("Filtered Data Table")
st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)

# Download button
csv_tsv = filtered_df.to_csv(index=False, sep='\t')
st.download_button(
    label="Download filtered data as TSV",
    data=csv_tsv,
    file_name="filtered_zara_sales.tsv",
    mime="text/tab-separated-values"
)