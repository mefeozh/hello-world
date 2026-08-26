import streamlit as st
import psycopg2
import polars as pl
import json
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Order Book Analytics", layout="wide")

@st.cache_data(ttl=60)
def load_data():
    try:
        conn = psycopg2.connect(host="db", port=5432, user="user", password="password", dbname="orderbook")
        # Optimization: Only load the most recent 1000 snapshots to save RAM
        query = "SELECT * FROM (SELECT * FROM book_snapshots ORDER BY timestamp DESC LIMIT 1000) sub ORDER BY timestamp ASC"
        df = pl.read_database(query, connection=conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return None

st.title("Order Book Microstructure Visualisation")

df = load_data()

if df is None or len(df) == 0:
    st.warning("No data found in the database. Please run fetcher.py first to gather some data.")
    st.stop()

# Helper to parse JSON
def extract_side(data_col, side):
    if isinstance(data_col, str):
        data = json.loads(data_col)
    else:
        data = data_col
    return data.get('snapshot', {}).get(side, {})

st.sidebar.header("Filters")
num_snapshots = len(df)
st.sidebar.write(f"Total Snapshots: {num_snapshots}")

# Timestamp selection
timestamps = df['timestamp'].to_list()
selected_idx = st.sidebar.slider("Select Snapshot by Time", 0, num_snapshots - 1, 0)
selected_ts = timestamps[selected_idx]

# Layout using Tabs for a cleaner 'Shiny' like interface
tab1, tab2, tab3 = st.tabs(["Order Book Depth", "Price Level Heatmap", "Depth Percentiles"])

# --- Helper Functions ---
def truncate_book(bids, asks, n_levels=50):
    """Keep only the top N levels closest to the spread to massively reduce RAM and browser freeze."""
    # Store original keys to prevent string formatting mismatch when looking back up
    b_items = [(float(p), p, s) for p, s in bids.items() if s is not None and float(s) > 0]
    a_items = [(float(p), p, s) for p, s in asks.items() if s is not None and float(s) > 0]
    
    b_items.sort(key=lambda x: x[0], reverse=True)
    a_items.sort(key=lambda x: x[0])
    
    trunc_bids = {orig_p: s for _, orig_p, s in b_items[:n_levels]}
    trunc_asks = {orig_p: s for _, orig_p, s in a_items[:n_levels]}
        
    return trunc_bids, trunc_asks

def process_side(side_dict, is_bid=True):
    prices = []
    sizes = []
    for p, s in side_dict.items():
        if s is not None and float(s) > 0:
            prices.append(float(p))
            sizes.append(float(s))
            
    # Sort prices
    sorted_idx = sorted(range(len(prices)), key=lambda k: prices[k], reverse=is_bid)
    
    sorted_prices = [prices[i] for i in sorted_idx]
    sorted_sizes = [sizes[i] for i in sorted_idx]
    
    # Cumulative sum
    cumulative_sizes = []
    current_sum = 0
    for s in sorted_sizes:
        current_sum += s
        cumulative_sizes.append(current_sum)
        
    return sorted_prices, sorted_sizes, cumulative_sizes

def calculate_mid_price(b_prices, a_prices):
    best_bid = max(b_prices) if b_prices else 0
    best_ask = min(a_prices) if a_prices else float('inf')
    if best_bid > 0 and best_ask != float('inf'):
        return (best_bid + best_ask) / 2.0
    return 0

# --- TAB 1: Order Book Depth ---
with tab1:
    st.subheader(f"Cumulative Order Book Depth at {selected_ts.strftime('%H:%M:%S')}")
    snapshot = df.row(selected_idx, named=True)
    bids_raw = extract_side(snapshot['data'], 'bid')
    asks_raw = extract_side(snapshot['data'], 'ask')
    
    bids, asks = truncate_book(bids_raw, asks_raw, n_levels=50)
    
    bid_prices, bid_sizes, bid_cumsums = process_side(bids, True)
    ask_prices, ask_sizes, ask_cumsums = process_side(asks, False)
    
    fig_depth = go.Figure()
    fig_depth.add_trace(go.Scatter(
        x=bid_prices, y=bid_cumsums, fill='tozeroy', mode='lines', 
        name='Bids', fillcolor='rgba(0,255,128,0.3)', line=dict(color='#00ff80', width=2)
    ))
    fig_depth.add_trace(go.Scatter(
        x=ask_prices, y=ask_cumsums, fill='tozeroy', mode='lines', 
        name='Asks', fillcolor='rgba(255,64,64,0.3)', line=dict(color='#ff4040', width=2)
    ))
    
    fig_depth.update_layout(
        xaxis_title="Price (USDT)", 
        yaxis_title="Cumulative Volume (BTC)", 
        template="plotly_dark",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig_depth, use_container_width=True)

# --- TAB 2: Heatmap ---
with tab2:
    st.subheader("Price Level Volume Over Time")
    
    def prepare_heatmap_data(df):
        heatmap_rows = []
        # Process the last 200 snapshots to keep browser rendering fast
        sampled_df = df.tail(200)
        
        for row in sampled_df.iter_rows(named=True):
            ts = row['timestamp']
            bids_raw = extract_side(row['data'], 'bid')
            asks_raw = extract_side(row['data'], 'ask')
            
            bids_dict, asks_dict = truncate_book(bids_raw, asks_raw, n_levels=50)
            
            for p, s in bids_dict.items():
                if s is not None and float(s) > 0:
                    heatmap_rows.append({"timestamp": ts, "price": float(p), "volume": float(s), "side": "bid"})
                
            for p, s in asks_dict.items():
                if s is not None and float(s) > 0:
                    heatmap_rows.append({"timestamp": ts, "price": float(p), "volume": float(s), "side": "ask"})
                
        return pl.DataFrame(heatmap_rows)

    with st.spinner("Processing High-Res Heatmap..."):
        heatmap_df = prepare_heatmap_data(df)
        
        if len(heatmap_df) > 0:
            fig_heat = px.density_heatmap(
                heatmap_df.to_pandas(), 
                x="timestamp", 
                y="price", 
                z="volume", 
                histfunc="sum",
                nbinsx=100,
                nbinsy=100,
                color_continuous_scale="Inferno",
            )
            fig_heat.update_layout(
                template="plotly_dark", 
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis_title="Time",
                yaxis_title="Price Level"
            )
            st.plotly_chart(fig_heat, use_container_width=True)

# --- TAB 3: Depth Percentiles ---
with tab3:
    st.subheader("Market Liquidity (Depth Percentiles)")
    st.markdown("Shows the total volume of bids/asks available within X% of the mid price over time.")
    
    with st.spinner("Calculating percentiles..."):
        perc_rows = []
        sampled_df = df.tail(300) # Time series of last 300 points
        
        for row in sampled_df.iter_rows(named=True):
            ts = row['timestamp']
            bids_raw = extract_side(row['data'], 'bid')
            asks_raw = extract_side(row['data'], 'ask')
            
            # We need deep book for 1% spread, so pull 200 levels
            bids_dict, asks_dict = truncate_book(bids_raw, asks_raw, n_levels=200)
            
            b_prices, b_sizes, _ = process_side(bids_dict, True)
            a_prices, a_sizes, _ = process_side(asks_dict, False)
            
            mid = calculate_mid_price(b_prices, a_prices)
            if mid == 0: continue
            
            # Calculate volume within 0.1%, 0.5%, 1%
            b_vol_01 = sum(s for p, s in zip(b_prices, b_sizes) if p >= mid * 0.999)
            b_vol_05 = sum(s for p, s in zip(b_prices, b_sizes) if p >= mid * 0.995)
            b_vol_10 = sum(s for p, s in zip(b_prices, b_sizes) if p >= mid * 0.990)
            
            a_vol_01 = sum(s for p, s in zip(a_prices, a_sizes) if p <= mid * 1.001)
            a_vol_05 = sum(s for p, s in zip(a_prices, a_sizes) if p <= mid * 1.005)
            a_vol_10 = sum(s for p, s in zip(a_prices, a_sizes) if p <= mid * 1.010)
            
            perc_rows.append({"timestamp": ts, "0.1% Bid": b_vol_01, "0.5% Bid": b_vol_05, "1.0% Bid": b_vol_10,
                              "0.1% Ask": a_vol_01, "0.5% Ask": a_vol_05, "1.0% Ask": a_vol_10})
        
        perc_df = pl.DataFrame(perc_rows).to_pandas()
        
        if len(perc_df) > 0:
            fig_perc = go.Figure()
            
            colors = {"0.1%": "#ffbaba", "0.5%": "#ff5252", "1.0%": "#a70000",
                      "0.1% ": "#baffc9", "0.5% ": "#00ff80", "1.0% ": "#008a45"} # Space added for asks to separate keys
            
            for col in ["0.1% Bid", "0.5% Bid", "1.0% Bid"]:
                fig_perc.add_trace(go.Scatter(x=perc_df['timestamp'], y=perc_df[col], mode='lines', name=col, line=dict(color=colors[col.replace(' Bid', ' ')])))
                
            for col in ["0.1% Ask", "0.5% Ask", "1.0% Ask"]:
                fig_perc.add_trace(go.Scatter(x=perc_df['timestamp'], y=perc_df[col], mode='lines', name=col, line=dict(color=colors[col.replace(' Ask', '')])))
            
            fig_perc.update_layout(template="plotly_dark", xaxis_title="Time", yaxis_title="Cumulative Volume", hovermode="x unified")
            st.plotly_chart(fig_perc, use_container_width=True)

