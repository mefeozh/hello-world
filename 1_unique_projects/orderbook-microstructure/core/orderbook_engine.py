import json
import duckdb
import polars as pl
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Tuple, List, Optional, Any
from datetime import datetime

def load_snapshots_from_duckdb(
    db_path: str, 
    limit: int = 1000, 
    offset: int = 0
) -> pl.DataFrame:
    """
    Load snapshots from DuckDB safely using Polars integration.
    """
    conn = duckdb.connect(db_path, read_only=True)
    try:
        query = f"""
            SELECT exchange, symbol, timestamp, receipt_timestamp, bids, asks
            FROM book
            ORDER BY timestamp ASC
            LIMIT {limit} OFFSET {offset}
        """
        try:
            return conn.execute(query).pl()
        except Exception:
            data = conn.execute(query).fetchall()
            cols = ["exchange", "symbol", "timestamp", "receipt_timestamp", "bids", "asks"]
            if not data:
                return pl.DataFrame(schema={c: pl.Utf8 if c in ["exchange", "symbol", "bids", "asks"] else pl.Float64 for c in cols})
            return pl.DataFrame(data, schema=cols, orient="row")
    finally:
        conn.close()

def get_total_snapshot_count(db_path: str) -> int:
    """Return total number of rows in the duckdb book table."""
    conn = duckdb.connect(db_path, read_only=True)
    try:
        count = conn.execute("SELECT COUNT(*) FROM book").fetchone()[0]
        return count
    finally:
        conn.close()

def parse_order_side(side_data: Any) -> Dict[str, float]:
    """Parse JSON or dict data into float price-volume mapping."""
    if side_data is None:
        return {}
    if isinstance(side_data, str):
        try:
            side_data = json.loads(side_data)
        except Exception:
            return {}
    if isinstance(side_data, dict):
        return {str(k): float(v) for k, v in side_data.items() if v is not None and float(v) > 0}
    return {}

def truncate_book(
    bids: Dict[str, float], 
    asks: Dict[str, float], 
    n_levels: int = 50
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Keep only the top N levels closest to the spread to optimize memory and rendering performance.
    """
    if n_levels <= 0:
        raise ValueError("n_levels must be positive")
        
    b_items = [(float(p), p, s) for p, s in bids.items() if s is not None and float(s) > 0]
    a_items = [(float(p), p, s) for p, s in asks.items() if s is not None and float(s) > 0]
    
    # Bids sorted descending (highest price first)
    b_items.sort(key=lambda x: x[0], reverse=True)
    # Asks sorted ascending (lowest price first)
    a_items.sort(key=lambda x: x[0])
    
    trunc_bids = {orig_p: s for _, orig_p, s in b_items[:n_levels]}
    trunc_asks = {orig_p: s for _, orig_p, s in a_items[:n_levels]}
    
    return trunc_bids, trunc_asks

def process_side(side_dict: Dict[str, float], is_bid: bool = True) -> Tuple[List[float], List[float], List[float]]:
    """
    Extract prices, sizes, and compute cumulative sizes for depth curves.
    """
    if not side_dict:
        return [], [], []
        
    prices = []
    sizes = []
    for p, s in side_dict.items():
        if s is not None and float(s) > 0:
            prices.append(float(p))
            sizes.append(float(s))
            
    if not prices:
        return [], [], []
        
    # Sort prices: bids descending, asks ascending
    sorted_idx = sorted(range(len(prices)), key=lambda k: prices[k], reverse=is_bid)
    
    sorted_prices = [prices[i] for i in sorted_idx]
    sorted_sizes = [sizes[i] for i in sorted_idx]
    
    cumulative_sizes = []
    current_sum = 0.0
    for s in sorted_sizes:
        current_sum += s
        cumulative_sizes.append(current_sum)
        
    return sorted_prices, sorted_sizes, cumulative_sizes

def compute_microstructure_metrics(
    bids: Dict[str, float], 
    asks: Dict[str, float], 
    top_n: int = 20
) -> Dict[str, float]:
    """
    Compute key microstructure KPIs:
    - Best Bid (Pb), Best Ask (Pa)
    - Mid Price = (Pb + Pa) / 2
    - Spread = Pa - Pb
    - Spread bps = (Spread / Mid) * 10,000
    - Order Book Imbalance (OBI) = (Vb - Va) / (Vb + Va)
    - Micro-Price = (Vb * Pa + Va * Pb) / (Vb + Va)
    - Total Bid Volume & Ask Volume in top N
    """
    trunc_bids, trunc_asks = truncate_book(bids, asks, n_levels=top_n)
    
    b_prices, b_sizes, _ = process_side(trunc_bids, is_bid=True)
    a_prices, a_sizes, _ = process_side(trunc_asks, is_bid=False)
    
    if not b_prices or not a_prices:
        return {
            "best_bid": 0.0,
            "best_ask": 0.0,
            "mid_price": 0.0,
            "spread": 0.0,
            "spread_bps": 0.0,
            "obi": 0.0,
            "micro_price": 0.0,
            "total_bid_vol": 0.0,
            "total_ask_vol": 0.0,
        }
        
    best_bid = b_prices[0]
    best_ask = a_prices[0]
    
    if best_bid < 0 or best_ask < 0:
        raise ValueError("Prices cannot be negative")
        
    mid_price = (best_bid + best_ask) / 2.0
    spread = max(0.0, best_ask - best_bid)
    spread_bps = (spread / mid_price * 10000.0) if mid_price > 0 else 0.0
    
    v_b = sum(b_sizes)
    v_a = sum(a_sizes)
    
    # Order Book Imbalance in [-1.0, 1.0]
    total_vol = v_b + v_a
    obi = (v_b - v_a) / total_vol if total_vol > 0 else 0.0
    
    # Micro-price (weighted by top level or top N volume)
    top_vb = b_sizes[0] if b_sizes else 0.0
    top_va = a_sizes[0] if a_sizes else 0.0
    top_vol = top_vb + top_va
    micro_price = (top_vb * best_ask + top_va * best_bid) / top_vol if top_vol > 0 else mid_price
    
    return {
        "best_bid": best_bid,
        "best_ask": best_ask,
        "mid_price": mid_price,
        "spread": spread,
        "spread_bps": spread_bps,
        "obi": obi,
        "micro_price": micro_price,
        "total_bid_vol": v_b,
        "total_ask_vol": v_a,
    }

def create_depth_chart(
    bids: Dict[str, float], 
    asks: Dict[str, float], 
    n_levels: int = 50,
    timestamp_str: str = ""
) -> go.Figure:
    """Create high-definition cumulative order book depth chart."""
    trunc_bids, trunc_asks = truncate_book(bids, asks, n_levels=n_levels)
    
    bid_prices, _, bid_cumsums = process_side(trunc_bids, is_bid=True)
    ask_prices, _, ask_cumsums = process_side(trunc_asks, is_bid=False)
    
    # Sort bids ascending for continuous x-axis plotting
    if bid_prices:
        bid_plot_prices = bid_prices[::-1]
        bid_plot_cumsums = bid_cumsums[::-1]
    else:
        bid_plot_prices, bid_plot_cumsums = [], []
        
    fig = go.Figure()
    
    # Bids (Green)
    if bid_plot_prices:
        fig.add_trace(go.Scatter(
            x=bid_plot_prices,
            y=bid_plot_cumsums,
            fill='tozeroy',
            mode='lines',
            name='Bids (Buyers)',
            line=dict(color='#00e676', width=2.5),
            fillcolor='rgba(0, 230, 118, 0.25)',
            hovertemplate="<b>Bid Price</b>: %{x:,.2f}<br><b>Cumulative Vol</b>: %{y:,.4f} BTC<extra></extra>"
        ))
        
    # Asks (Red)
    if ask_prices:
        fig.add_trace(go.Scatter(
            x=ask_prices,
            y=ask_cumsums,
            fill='tozeroy',
            mode='lines',
            name='Asks (Sellers)',
            line=dict(color='#ff1744', width=2.5),
            fillcolor='rgba(255, 23, 68, 0.25)',
            hovertemplate="<b>Ask Price</b>: %{x:,.2f}<br><b>Cumulative Vol</b>: %{y:,.4f} BTC<extra></extra>"
        ))
        
    # Add Mid-Price vertical dashed line
    if bid_prices and ask_prices:
        mid_p = (bid_prices[0] + ask_prices[0]) / 2.0
        fig.add_vline(
            x=mid_p, 
            line_dash="dash", 
            line_color="#ffd600", 
            annotation_text=f"Mid: {mid_p:,.2f}",
            annotation_position="top"
        )
        
    title = f"Cumulative Order Book Depth {timestamp_str}" if timestamp_str else "Cumulative Order Book Depth"
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#ffffff")),
        xaxis=dict(
            title="Price (USDT)", 
            gridcolor="rgba(255,255,255,0.08)",
            tickformat=",.2f"
        ),
        yaxis=dict(
            title="Cumulative Volume (BTC)", 
            gridcolor="rgba(255,255,255,0.08)",
            tickformat=",.4f"
        ),
        template="plotly_dark",
        paper_bgcolor="#1e1e24",
        plot_bgcolor="#18181c",
        hovermode="x unified",
        margin=dict(l=50, r=30, t=50, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    return fig

def prepare_heatmap_df(df_window: pl.DataFrame, n_levels: int = 50) -> pd.DataFrame:
    """Transform snapshot slice into a flat DataFrame for density heatmap."""
    heatmap_rows = []
    
    for row in df_window.iter_rows(named=True):
        ts = row['timestamp']
        if isinstance(ts, (int, float)):
            dt = datetime.utcfromtimestamp(ts).strftime('%H:%M:%S')
        else:
            dt = str(ts)
            
        bids_raw = parse_order_side(row['bids'])
        asks_raw = parse_order_side(row['asks'])
        
        bids_dict, asks_dict = truncate_book(bids_raw, asks_raw, n_levels=n_levels)
        
        for p, s in bids_dict.items():
            if s > 0:
                heatmap_rows.append({"time": dt, "price": float(p), "volume": float(s), "side": "bid"})
                
        for p, s in asks_dict.items():
            if s > 0:
                heatmap_rows.append({"time": dt, "price": float(p), "volume": float(s), "side": "ask"})
                
    if not heatmap_rows:
        return pd.DataFrame(columns=["time", "price", "volume", "side"])
        
    return pd.DataFrame(heatmap_rows)

def create_heatmap_chart(df_window: pl.DataFrame, n_levels: int = 50) -> go.Figure:
    """Create high-frequency price level volume heatmap."""
    heat_df = prepare_heatmap_df(df_window, n_levels=n_levels)
    
    if heat_df.empty:
        fig = go.Figure()
        fig.update_layout(title="No data available for heatmap", template="plotly_dark")
        return fig
        
    fig = px.density_heatmap(
        heat_df,
        x="time",
        y="price",
        z="volume",
        histfunc="sum",
        nbinsx=min(120, len(heat_df['time'].unique())),
        nbinsy=100,
        color_continuous_scale="Viridis",
        title="Microstructure Price Level Liquidity Heatmap"
    )
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1e1e24",
        plot_bgcolor="#18181c",
        xaxis=dict(title="Time (UTC)", gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(title="Price (USDT)", gridcolor="rgba(255,255,255,0.08)", tickformat=",.2f"),
        coloraxis_colorbar=dict(title="Volume (BTC)"),
        margin=dict(l=50, r=30, t=50, b=40)
    )
    return fig

def create_percentiles_chart(df_window: pl.DataFrame, n_levels: int = 200) -> go.Figure:
    """Calculate and plot liquidity depth percentiles (0.1%, 0.5%, 1.0% distance)."""
    perc_rows = []
    
    for row in df_window.iter_rows(named=True):
        ts = row['timestamp']
        if isinstance(ts, (int, float)):
            dt = datetime.utcfromtimestamp(ts).strftime('%H:%M:%S')
        else:
            dt = str(ts)
            
        bids_raw = parse_order_side(row['bids'])
        asks_raw = parse_order_side(row['asks'])
        
        bids_dict, asks_dict = truncate_book(bids_raw, asks_raw, n_levels=n_levels)
        b_prices, b_sizes, _ = process_side(bids_dict, True)
        a_prices, a_sizes, _ = process_side(asks_dict, False)
        
        if not b_prices or not a_prices:
            continue
            
        mid = (b_prices[0] + a_prices[0]) / 2.0
        if mid <= 0:
            continue
            
        b_01 = sum(s for p, s in zip(b_prices, b_sizes) if p >= mid * 0.999)
        b_05 = sum(s for p, s in zip(b_prices, b_sizes) if p >= mid * 0.995)
        b_10 = sum(s for p, s in zip(b_prices, b_sizes) if p >= mid * 0.990)
        
        a_01 = sum(s for p, s in zip(a_prices, a_sizes) if p <= mid * 1.001)
        a_05 = sum(s for p, s in zip(a_prices, a_sizes) if p <= mid * 1.005)
        a_10 = sum(s for p, s in zip(a_prices, a_sizes) if p <= mid * 1.010)
        
        perc_rows.append({
            "time": dt,
            "Bid 0.1%": b_01,
            "Bid 0.5%": b_05,
            "Bid 1.0%": b_10,
            "Ask 0.1%": a_01,
            "Ask 0.5%": a_05,
            "Ask 1.0%": a_10,
        })
        
    if not perc_rows:
        fig = go.Figure()
        fig.update_layout(title="No data available for percentiles", template="plotly_dark")
        return fig
        
    p_df = pd.DataFrame(perc_rows)
    fig = go.Figure()
    
    # Bid curves
    fig.add_trace(go.Scatter(x=p_df['time'], y=p_df['Bid 0.1%'], mode='lines', name='Bid 0.1%', line=dict(color='#a7f3d0', width=1.5)))
    fig.add_trace(go.Scatter(x=p_df['time'], y=p_df['Bid 0.5%'], mode='lines', name='Bid 0.5%', line=dict(color='#34d399', width=2)))
    fig.add_trace(go.Scatter(x=p_df['time'], y=p_df['Bid 1.0%'], mode='lines', name='Bid 1.0%', line=dict(color='#059669', width=2.5)))
    
    # Ask curves
    fig.add_trace(go.Scatter(x=p_df['time'], y=p_df['Ask 0.1%'], mode='lines', name='Ask 0.1%', line=dict(color='#fecaca', width=1.5)))
    fig.add_trace(go.Scatter(x=p_df['time'], y=p_df['Ask 0.5%'], mode='lines', name='Ask 0.5%', line=dict(color='#f87171', width=2)))
    fig.add_trace(go.Scatter(x=p_df['time'], y=p_df['Ask 1.0%'], mode='lines', name='Ask 1.0%', line=dict(color='#dc2626', width=2.5)))
    
    fig.update_layout(
        title="Market Liquidity Depth within 0.1%, 0.5%, 1.0% of Mid Price",
        template="plotly_dark",
        paper_bgcolor="#1e1e24",
        plot_bgcolor="#18181c",
        xaxis=dict(title="Time (UTC)", gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(title="Cumulative Available Volume (BTC)", gridcolor="rgba(255,255,255,0.08)"),
        hovermode="x unified",
        margin=dict(l=50, r=30, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def generate_ladder_df(
    bids: Dict[str, float], 
    asks: Dict[str, float], 
    n_levels: int = 15
) -> pd.DataFrame:
    """Generate side-by-side L2 order book ladder table with depth percentage."""
    trunc_bids, trunc_asks = truncate_book(bids, asks, n_levels=n_levels)
    b_prices, b_sizes, b_cum = process_side(trunc_bids, is_bid=True)
    a_prices, a_sizes, a_cum = process_side(trunc_asks, is_bid=False)
    
    rows = []
    max_len = max(len(b_prices), len(a_prices))
    for i in range(max_len):
        bid_vol = b_sizes[i] if i < len(b_sizes) else None
        bid_p = b_prices[i] if i < len(b_prices) else None
        bid_c = b_cum[i] if i < len(b_cum) else None
        
        ask_p = a_prices[i] if i < len(a_prices) else None
        ask_vol = a_sizes[i] if i < len(a_sizes) else None
        ask_c = a_cum[i] if i < len(a_cum) else None
        
        rows.append({
            "Bid Cum": f"{bid_c:.4f}" if bid_c is not None else "-",
            "Bid Size": f"{bid_vol:.4f}" if bid_vol is not None else "-",
            "Bid Price ($)": f"{bid_p:,.2f}" if bid_p is not None else "-",
            "Ask Price ($)": f"{ask_p:,.2f}" if ask_p is not None else "-",
            "Ask Size": f"{ask_vol:.4f}" if ask_vol is not None else "-",
            "Ask Cum": f"{ask_c:.4f}" if ask_c is not None else "-"
        })
        
    return pd.DataFrame(rows)
