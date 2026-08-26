# 📈 High-Throughput Level 2 Order Book Analytics & Visualization

**Author:** Mehmet Efe Özhan  
**Tech Stack:** Cryptofeed, DuckDB, Polars, Streamlit, Plotly

---

## 📌 Features

1. **Streaming Ingestion:** Real-time Level 2 (L2) market depth collector streaming live bid/ask deltas via `cryptofeed`.
2. **Columnar Warehousing:** High-throughput batch writes into embedded `DuckDB` (`orderbook.duckdb`).
3. **Microstructure Analytics:** Fast zero-copy aggregations using `polars` for cumulative depth curves, bid-ask spread percentiles, and liquidity heatmaps over time.
4. **Dashboard:** Interactive 3-tab Streamlit dashboard.

---

## 💻 Usage

```bash
streamlit run dashboard.py
```
