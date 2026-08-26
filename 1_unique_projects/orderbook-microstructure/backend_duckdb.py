import asyncio
import json
from collections import defaultdict
from typing import Tuple
from cryptofeed.backends.backend import BackendBookCallback, BackendQueue
import duckdb

class BookDuckDB(BackendQueue, BackendBookCallback):
    def __init__(self, db_path: str, table: str = 'book', snapshots_only=True, snapshot_interval=10, **kwargs):
        self.db_path = db_path
        self.table = table
        self.snapshots_only = snapshots_only
        self.snapshot_interval = snapshot_interval
        self.snapshot_count = defaultdict(int)
        self.conn = None
        self.running = True
        
        # Numeric type and none bounds
        self.numeric_type = float
        self.none_to = None

        # Create table if not exists using a temporary sync connection
        with duckdb.connect(self.db_path) as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table} (
                    exchange VARCHAR,
                    symbol VARCHAR,
                    timestamp DOUBLE,
                    receipt_timestamp DOUBLE,
                    bids JSON,
                    asks JSON
                )
            """)
        
        super().__init__(**kwargs)

    async def writer(self):
        # We use a dedicated connection for the writer task
        self.conn = duckdb.connect(self.db_path)
        
        while self.running:
            async with self.read_queue() as updates:
                if len(updates) > 0:
                    batch = []
                    for data in updates:
                        exchange = data.get('exchange', 'Binance')
                        symbol = data.get('symbol', 'BTC-USDT')
                        timestamp = data.get('timestamp')
                        receipt_timestamp = data.get('receipt_timestamp')
                        
                        book_data = data.get('book', {})
                        bids = json.dumps(book_data.get('bid', {}))
                        asks = json.dumps(book_data.get('ask', {}))
                        
                        batch.append((exchange, symbol, timestamp, receipt_timestamp, bids, asks))
                        
                    # Insert in batch
                    self.conn.executemany(f"""
                        INSERT INTO {self.table} (exchange, symbol, timestamp, receipt_timestamp, bids, asks) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, batch)
                    
        if self.conn:
            self.conn.close()

    async def _write_snapshot(self, book, receipt_timestamp: float):
        data = book.to_dict(numeric_type=self.numeric_type, none_to=self.none_to)
        if not book.timestamp:
            data['timestamp'] = receipt_timestamp
        data['receipt_timestamp'] = receipt_timestamp
        data['exchange'] = book.exchange
        data['symbol'] = book.symbol
        await self.write(data)

    async def __call__(self, book, receipt_timestamp: float):
        if self.snapshots_only:
            await self._write_snapshot(book, receipt_timestamp)
        else:
            data = book.to_dict(delta=book.delta is not None, numeric_type=self.numeric_type, none_to=self.none_to)
            if not book.timestamp:
                data['timestamp'] = receipt_timestamp
            data['receipt_timestamp'] = receipt_timestamp
            data['exchange'] = book.exchange
            data['symbol'] = book.symbol

            if book.delta is None:
                pass
            else:
                self.snapshot_count[book.symbol] += 1
                
            if self.snapshot_interval <= self.snapshot_count[book.symbol] and book.delta:
                await self._write_snapshot(book, receipt_timestamp)
                self.snapshot_count[book.symbol] = 0
