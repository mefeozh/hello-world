import pytest
import numpy as np
from core.orderbook_engine import (
    parse_order_side,
    truncate_book,
    process_side,
    compute_microstructure_metrics,
    generate_ladder_df
)

def test_parse_order_side():
    # Test valid dict
    raw = {"70000.5": 1.5, "69999.0": "2.0", "70001.0": 0.0, "invalid": None}
    parsed = parse_order_side(raw)
    assert parsed == {"70000.5": 1.5, "69999.0": 2.0}
    
    # Test valid JSON string
    json_str = '{"70000.5": 1.5, "69999.0": 2.0}'
    parsed_json = parse_order_side(json_str)
    assert parsed_json == {"70000.5": 1.5, "69999.0": 2.0}
    
    # Test None / Invalid
    assert parse_order_side(None) == {}
    assert parse_order_side("not a json") == {}

def test_truncate_book():
    bids = {"70000": 1.0, "70010": 2.0, "69990": 3.0}
    asks = {"70020": 1.5, "70030": 2.5, "70015": 0.5}
    
    trunc_bids, trunc_asks = truncate_book(bids, asks, n_levels=2)
    # Bids should have top 2 highest prices: 70010, 70000
    assert list(trunc_bids.keys()) == ["70010", "70000"]
    # Asks should have top 2 lowest prices: 70015, 70020
    assert list(trunc_asks.keys()) == ["70015", "70020"]

def test_truncate_book_invalid():
    bids = {"70000": 1.0}
    asks = {"70020": 1.0}
    with pytest.raises(ValueError, match="n_levels must be positive"):
        truncate_book(bids, asks, n_levels=0)

def test_process_side():
    side = {"70000": 1.0, "70010": 2.0, "69990": 3.0}
    
    # Bid side (descending)
    p_bid, s_bid, c_bid = process_side(side, is_bid=True)
    assert p_bid == [70010.0, 70000.0, 69990.0]
    assert s_bid == [2.0, 1.0, 3.0]
    assert c_bid == [2.0, 3.0, 6.0]
    
    # Ask side (ascending)
    p_ask, s_ask, c_ask = process_side(side, is_bid=False)
    assert p_ask == [69990.0, 70000.0, 70010.0]
    assert s_ask == [3.0, 1.0, 2.0]
    assert c_ask == [3.0, 4.0, 6.0]

def test_compute_microstructure_metrics():
    bids = {"70000.0": 2.0, "69990.0": 3.0}
    asks = {"70010.0": 1.0, "70020.0": 4.0}
    
    metrics = compute_microstructure_metrics(bids, asks, top_n=2)
    assert metrics["best_bid"] == 70000.0
    assert metrics["best_ask"] == 70010.0
    assert metrics["mid_price"] == 70005.0
    assert metrics["spread"] == 10.0
    assert np.isclose(metrics["spread_bps"], (10.0 / 70005.0) * 10000.0)
    
    # OBI = (5.0 - 5.0) / (5.0 + 5.0) = 0.0
    assert metrics["obi"] == 0.0
    
    # Micro-price with top level: (2.0 * 70010 + 1.0 * 70000) / 3.0 = (140020 + 70000) / 3 = 70006.6667
    assert np.isclose(metrics["micro_price"], 70006.66666666667)

def test_empty_book_edge_cases():
    metrics = compute_microstructure_metrics({}, {})
    assert metrics["best_bid"] == 0.0
    assert metrics["best_ask"] == 0.0
    assert metrics["mid_price"] == 0.0
    assert metrics["spread"] == 0.0
    assert metrics["obi"] == 0.0

def test_ladder_df():
    bids = {"70000.0": 2.0}
    asks = {"70010.0": 1.0}
    df = generate_ladder_df(bids, asks, n_levels=5)
    assert len(df) == 1
    assert "Bid Price ($)" in df.columns
    assert "Ask Price ($)" in df.columns
