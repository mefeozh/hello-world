# ⚡ High-Throughput Level 2 Order Book Analytics & Microstructure Terminal

**Author:** Mehmet Efe Özhan  
**Tech Stack:** Shiny for Python, DuckDB, Polars, PyArrow, Plotly, Cryptofeed, PyTest

---

## 📌 Overview

A cryptocurrency market microstructure analytics terminal built with **Shiny for Python**, **DuckDB**, and **Polars**. The application ingests, warehouses, and visualizes high-frequency Level-2 (L2) Limit Order Book depth snapshots from Binance (`BTC-USDT`) with zero-copy analytics and interactive playback.

---

## 🚀 Key Features

1. **Reactive Microstructure Terminal (`app.py`):**
   - Built with **Shiny for Python** and styled with `shinyswatch.theme.darkly`.
   - Real-time KPI cards: Best Bid, Best Ask, Mid-Price, Spread (bps), Micro-Price, and Order Book Imbalance (OBI).
   - Dynamic Snapshot Replay: Interactive slider, auto-play with adjustable replay frequency, and step forward/backward navigation.

2. **Multi-Perspective Visualizations:**
   - **Cumulative Depth Curves:** Interactive Plotly chart with bid/ask depth volume fills, midpoint price, and spread indicators.
   - **2D Liquidity Heatmap:** High-resolution density heatmap tracking liquidity walls and queue size variations across price levels over time.
   - **Depth Percentiles:** Liquidity curves tracking depth available within `0.1%`, `0.5%`, and `1.0%` distances from the mid-price.
   - **Level-2 Depth Ladder:** Real-time side-by-side order ladder with price and size allocations.

3. **High-Performance Data Infrastructure:**
   - **DuckDB Vectorized Engine:** Sub-millisecond snapshot querying over 4,000+ snapshots stored locally in `orderbook.duckdb`.
   - **Polars & PyArrow Integration:** Zero-copy DataFrame transformations and memory-efficient order book truncation.
   - **Async Cryptofeed Ingest (`fetcher.py` / `backend_duckdb.py`):** High-throughput orderbook streaming backend.

4. **Rigorous Numerical Integrity:**
   - Automated `pytest` suite validating edge cases, empty books, physical non-negativity, and mathematical accuracy.

---

## 📐 Governing Microstructure Formulations

- **Mid-Price:**
  $$P_{\text{mid}} = \frac{P_{\text{ask}} + P_{\text{bid}}}{2}$$

- **Spread in Basis Points (bps):**
  $$\text{Spread (bps)} = \left( \frac{P_{\text{ask}} - P_{\text{bid}}}{P_{\text{mid}}} \right) \times 10{,}000$$

- **Order Book Imbalance (OBI):**
  $$\text{OBI}_N = \frac{\sum_{i=1}^N V_{\text{bid}}^{(i)} - \sum_{j=1}^N V_{\text{ask}}^{(j)}}{\sum_{i=1}^N V_{\text{bid}}^{(i)} + \sum_{j=1}^N V_{\text{ask}}^{(j)}} \in [-1.0, 1.0]$$

- **Micro-Price:**
  $$P_{\text{micro}} = \frac{V_{\text{bid}}^{(1)} \cdot P_{\text{ask}}^{(1)} + V_{\text{ask}}^{(1)} \cdot P_{\text{bid}}^{(1)}}{V_{\text{bid}}^{(1)} + V_{\text{ask}}^{(1)}}$$

---

## 📁 Repository Structure

```
orderbook-microstructure/
├── app.py                    # Shiny for Python reactive terminal application
├── backend_duckdb.py         # Async DuckDB callback backend for Cryptofeed
├── fetcher.py                # Cryptofeed Binance L2 collector
├── orderbook.duckdb          # Embedded DuckDB database with L2 book snapshots
├── requirements.txt          # Python dependencies
├── core/
│   ├── __init__.py
│   └── orderbook_engine.py   # Vectorized metrics, truncation, and Plotly builders
└── tests/
    ├── __init__.py
    └── test_orderbook_engine.py  # Pytest test suite
```

---

## 💻 Installation & Usage

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Shiny Microstructure Terminal
```bash
shiny run --reload --port 8000 app.py
```
Then open your browser at `http://127.0.0.1:8000`.

### 3. Run Automated Tests
```bash
pytest tests/
```
