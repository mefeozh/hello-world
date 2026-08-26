import asyncio
import traceback
import time
from cryptofeed import FeedHandler
from cryptofeed.exchanges import Binance
from cryptofeed.defines import L2_BOOK
from cryptofeed.backends.postgres import BookPostgres

def main():
    val = BookPostgres(
        host='db',
        port=5432,
        user='user',
        pw='password',
        db='orderbook',
        table='book_snapshots',
        snapshots_only=True
    )
    
    fh = FeedHandler()
    fh.add_feed(Binance(symbols=['BTC-USDT'], channels=[L2_BOOK], callbacks={L2_BOOK: val}))
    
    print("Starting data collection with PostgreSQL!")
    try:
        fh.run()
    except Exception as e:
        print("Encountered exception:", e)
        traceback.print_exc()
        time.sleep(60)

if __name__ == '__main__':
    main()
