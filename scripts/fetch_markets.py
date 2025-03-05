import os
from src.data.polymarket_client import PolymarketClient
from src.data.storage import MarketStorage
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    try:
        client = PolymarketClient()
        storage = MarketStorage()
        tags = ["Politics", "Ukraine"]
        
        logger.info(f"Fetching markets with tags: {tags}")
        markets = client.get_all_markets(tags=tags)
        logger.info(f"Fetched {len(markets)} markets")
        
        output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "markets")
        storage.save_markets_to_file(
            markets=markets,
            required_tags=tags,
            output_dir=output_dir
        )
        
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")

if __name__ == "__main__":
    main()
