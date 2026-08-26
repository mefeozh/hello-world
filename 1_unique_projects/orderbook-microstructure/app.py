import os
import time
from datetime import datetime
from pathlib import Path

from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_plotly
import shinyswatch
import polars as pl
import pandas as pd

from core.orderbook_engine import (
    load_snapshots_from_duckdb,
    get_total_snapshot_count,
    parse_order_side,
    truncate_book,
    process_side,
    compute_microstructure_metrics,
    create_depth_chart,
    create_heatmap_chart,
    create_percentiles_chart,
    generate_ladder_df,
)

# Resolve DB Path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "orderbook.duckdb")

# Preload initial dataset from DuckDB (Limit to recent snapshots for high speed)
TOTAL_AVAILABLE_SNAPSHOTS = get_total_snapshot_count(DB_PATH) if os.path.exists(DB_PATH) else 0
INITIAL_LOAD_LIMIT = min(TOTAL_AVAILABLE_SNAPSHOTS, 1000)

app_ui = ui.page_fluid(
    ui.tags.style("""
        body {
            background-color: #121316;
            color: #e2e8f0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        .card {
            background-color: #1a1c23;
            border: 1px solid #2d3748;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
            margin-bottom: 1rem;
        }
        .metric-card {
            background: linear-gradient(145deg, #1e212b, #171922);
            border-left: 4px solid #3b82f6;
            padding: 14px 18px;
            border-radius: 8px;
            text-align: center;
        }
        .metric-title {
            font-size: 0.82rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }
        .metric-value {
            font-size: 1.45rem;
            font-weight: 700;
            color: #f8fafc;
        }
        .metric-sub {
            font-size: 0.78rem;
            color: #64748b;
            margin-top: 2px;
        }
        .badge-binance {
            background-color: #f0b90b;
            color: #0b0e11;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
        }
        .table-ladder {
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.85rem;
        }
    """),
    
    # Header
    ui.div(
        ui.div(
            ui.h3("⚡ Order Book Microstructure Terminal", style="margin-bottom: 0px; font-weight: 800;"),
            ui.p("High-frequency Level-2 Order Book analytics powered by Shiny for Python, DuckDB & Polars", 
                 style="color: #94a3b8; font-size: 0.9rem; margin-top: 4px; margin-bottom: 0;"),
        ),
        ui.div(
            ui.span("BINANCE", class_="badge-binance"),
            ui.span("BTC-USDT", style="font-weight: 700; margin-left: 8px; font-size: 1rem; color: #38bdf8;"),
            style="display: flex; align-items: center; justify-content: flex-end;"
        ),
        style="display: flex; justify-content: space-between; align-items: center; padding: 15px 0px; border-bottom: 1px solid #2d3748; margin-bottom: 15px;"
    ),

    # Main Layout with Sidebar
    ui.layout_sidebar(
        ui.sidebar(
            ui.h5("Control Panel", style="color: #38bdf8; font-weight: 700;"),
            ui.hr(style="margin: 8px 0; border-color: #334155;"),
            
            ui.input_select(
                "n_levels", 
                "Depth Levels (Top N):", 
                choices={"20": "Top 20 Levels", "50": "Top 50 Levels (Fast)", "100": "Top 100 Levels", "200": "Top 200 Levels"},
                selected="50"
            ),
            
            ui.input_select(
                "window_size", 
                "History Window Size:", 
                choices={"50": "50 Snapshots", "100": "100 Snapshots", "200": "200 Snapshots (Default)", "400": "400 Snapshots"},
                selected="200"
            ),

            ui.hr(style="margin: 8px 0; border-color: #334155;"),
            ui.h6("Snapshot Playback", style="color: #e2e8f0; font-weight: 600;"),
            
            ui.input_slider(
                "snapshot_idx", 
                "Select Snapshot:", 
                min=0, 
                max=max(0, INITIAL_LOAD_LIMIT - 1), 
                value=0, 
                step=1
            ),
            
            ui.div(
                ui.input_action_button("btn_prev", "⏮ Prev", class_="btn-secondary btn-sm"),
                ui.input_action_button("btn_play", "▶ Play", class_="btn-primary btn-sm"),
                ui.input_action_button("btn_next", "⏭ Next", class_="btn-secondary btn-sm"),
                style="display: flex; gap: 8px; justify-content: center; margin-top: 10px;"
            ),
            
            ui.div(
                ui.input_slider(
                    "play_speed", 
                    "Replay Interval (seconds):", 
                    min=0.2, 
                    max=2.0, 
                    value=0.5, 
                    step=0.1
                ),
                style="margin-top: 10px;"
            ),

            ui.hr(style="margin: 8px 0; border-color: #334155;"),
            ui.div(
                ui.output_text("db_status_text"),
                style="font-size: 0.78rem; color: #94a3b8;"
            ),
            width=320,
            bg="#181a20"
        ),

        # Right Column Content: KPI Cards + Tabs
        ui.div(
            # Top KPI Summary Cards Row
            ui.row(
                ui.column(2, ui.div(
                    ui.div("Best Bid", class_="metric-title"),
                    ui.div(ui.output_text("val_best_bid"), class_="metric-value", style="color: #00e676;"),
                    ui.div("Buyer Max Price", class_="metric-sub"),
                    class_="metric-card"
                )),
                ui.column(2, ui.div(
                    ui.div("Best Ask", class_="metric-title"),
                    ui.div(ui.output_text("val_best_ask"), class_="metric-value", style="color: #ff1744;"),
                    ui.div("Seller Min Price", class_="metric-sub"),
                    class_="metric-card"
                )),
                ui.column(2, ui.div(
                    ui.div("Mid Price", class_="metric-title"),
                    ui.div(ui.output_text("val_mid_price"), class_="metric-value"),
                    ui.div("Spread Midpoint", class_="metric-sub"),
                    class_="metric-card"
                )),
                ui.column(2, ui.div(
                    ui.div("Spread", class_="metric-title"),
                    ui.div(ui.output_text("val_spread"), class_="metric-value", style="color: #facc15;"),
                    ui.div(ui.output_text("val_spread_bps"), class_="metric-sub"),
                    class_="metric-card"
                )),
                ui.column(2, ui.div(
                    ui.div("Micro-Price", class_="metric-title"),
                    ui.div(ui.output_text("val_micro_price"), class_="metric-value", style="color: #38bdf8;"),
                    ui.div("Volume-Weighted", class_="metric-sub"),
                    class_="metric-card"
                )),
                ui.column(2, ui.div(
                    ui.div("Imbalance (OBI)", class_="metric-title"),
                    ui.div(ui.output_text("val_obi"), class_="metric-value"),
                    ui.div(ui.output_text("val_obi_label"), class_="metric-sub"),
                    class_="metric-card"
                )),
                style="margin-bottom: 18px;"
            ),

            # Visualizations Tabset
            ui.navset_card_tab(
                ui.nav_panel(
                    "📈 Cumulative Order Book Depth",
                    output_widget("depth_plot", height="520px")
                ),
                ui.nav_panel(
                    "🔥 Liquidity Heatmap",
                    output_widget("heatmap_plot", height="520px")
                ),
                ui.nav_panel(
                    "📊 Depth Percentiles",
                    output_widget("percentiles_plot", height="520px")
                ),
                ui.nav_panel(
                    "📑 Level-2 Depth Ladder",
                    ui.div(
                        ui.output_table("ladder_table"),
                        class_="table-ladder",
                        style="max-height: 520px; overflow-y: auto; padding: 10px;"
                    )
                )
            )
        )
    ),
    theme=shinyswatch.theme.darkly()
)


def server(input, output, session):
    # Reactive state for playback
    is_playing = reactive.value(False)
    
    # Load dataset
    @reactive.calc
    def dataset():
        if not os.path.exists(DB_PATH):
            return pl.DataFrame()
        return load_snapshots_from_duckdb(DB_PATH, limit=INITIAL_LOAD_LIMIT, offset=0)

    # Status text
    @output
    @render.text
    def db_status_text():
        df = dataset()
        return f"Loaded: {len(df):,} / Total {TOTAL_AVAILABLE_SNAPSHOTS:,} snapshots"

    # Playback Button Handler
    @reactive.effect
    @reactive.event(input.btn_play)
    def toggle_play():
        new_state = not is_playing()
        is_playing.set(new_state)
        label = "⏸ Pause" if new_state else "▶ Play"
        btn_class = "btn-warning btn-sm" if new_state else "btn-primary btn-sm"
        ui.update_action_button("btn_play", label=label)

    # Next / Prev Button Handlers
    @reactive.effect
    @reactive.event(input.btn_next)
    def on_next():
        df = dataset()
        if len(df) == 0:
            return
        curr = input.snapshot_idx()
        if curr < len(df) - 1:
            ui.update_slider("snapshot_idx", value=curr + 1)

    @reactive.effect
    @reactive.event(input.btn_prev)
    def on_prev():
        curr = input.snapshot_idx()
        if curr > 0:
            ui.update_slider("snapshot_idx", value=curr - 1)

    # Periodic timer for automatic playback
    @reactive.effect
    def auto_play_timer():
        if is_playing():
            reactive.invalidate_later(input.play_speed())
            df = dataset()
            if len(df) > 0:
                curr = input.snapshot_idx()
                next_val = (curr + 1) % len(df)
                ui.update_slider("snapshot_idx", value=next_val)

    # Current snapshot row
    @reactive.calc
    def current_snapshot():
        df = dataset()
        if len(df) == 0:
            return None
        idx = min(input.snapshot_idx(), len(df) - 1)
        return df.row(idx, named=True)

    # Current snapshot metrics
    @reactive.calc
    def current_metrics():
        snap = current_snapshot()
        if not snap:
            return {
                "best_bid": 0.0, "best_ask": 0.0, "mid_price": 0.0,
                "spread": 0.0, "spread_bps": 0.0, "obi": 0.0,
                "micro_price": 0.0, "total_bid_vol": 0.0, "total_ask_vol": 0.0
            }
        bids = parse_order_side(snap['bids'])
        asks = parse_order_side(snap['asks'])
        top_n = int(input.n_levels())
        return compute_microstructure_metrics(bids, asks, top_n=top_n)

    # Metrics Outputs
    @output
    @render.text
    def val_best_bid():
        return f"${current_metrics()['best_bid']:,.2f}"

    @output
    @render.text
    def val_best_ask():
        return f"${current_metrics()['best_ask']:,.2f}"

    @output
    @render.text
    def val_mid_price():
        return f"${current_metrics()['mid_price']:,.2f}"

    @output
    @render.text
    def val_spread():
        return f"${current_metrics()['spread']:,.2f}"

    @output
    @render.text
    def val_spread_bps():
        return f"{current_metrics()['spread_bps']:.2f} bps"

    @output
    @render.text
    def val_micro_price():
        return f"${current_metrics()['micro_price']:,.2f}"

    @output
    @render.text
    def val_obi():
        obi = current_metrics()['obi']
        sign = "+" if obi > 0 else ""
        return f"{sign}{obi:.3f}"

    @output
    @render.text
    def val_obi_label():
        obi = current_metrics()['obi']
        if obi > 0.1:
            return "Buyer Dominated 🟢"
        elif obi < -0.1:
            return "Seller Dominated 🔴"
        return "Balanced ⚪"

    # Tab 1: Depth Plot
    @output
    @render_plotly
    def depth_plot():
        snap = current_snapshot()
        if not snap:
            return None
        bids = parse_order_side(snap['bids'])
        asks = parse_order_side(snap['asks'])
        n_levels = int(input.n_levels())
        ts = snap['timestamp']
        ts_str = f"({datetime.utcfromtimestamp(ts).strftime('%H:%M:%S.%f')[:-3]} UTC)" if isinstance(ts, (int, float)) else ""
        return create_depth_chart(bids, asks, n_levels=n_levels, timestamp_str=ts_str)

    # Tab 2: Heatmap Plot
    @output
    @render_plotly
    def heatmap_plot():
        df = dataset()
        if len(df) == 0:
            return None
        w_size = int(input.window_size())
        curr_idx = min(input.snapshot_idx(), len(df) - 1)
        start_idx = max(0, curr_idx - w_size + 1)
        df_slice = df.slice(start_idx, curr_idx - start_idx + 1)
        n_levels = min(int(input.n_levels()), 50)
        return create_heatmap_chart(df_slice, n_levels=n_levels)

    # Tab 3: Percentiles Plot
    @output
    @render_plotly
    def percentiles_plot():
        df = dataset()
        if len(df) == 0:
            return None
        w_size = int(input.window_size())
        curr_idx = min(input.snapshot_idx(), len(df) - 1)
        start_idx = max(0, curr_idx - w_size + 1)
        df_slice = df.slice(start_idx, curr_idx - start_idx + 1)
        return create_percentiles_chart(df_slice, n_levels=100)

    # Tab 4: Ladder Table
    @output
    @render.table
    def ladder_table():
        snap = current_snapshot()
        if not snap:
            return pd.DataFrame()
        bids = parse_order_side(snap['bids'])
        asks = parse_order_side(snap['asks'])
        return generate_ladder_df(bids, asks, n_levels=15)


app = App(app_ui, server)
