import requests
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal

class MarketPriceInfo:
    """Helper class to process market prices."""
    
    @staticmethod
    def get_probability_from_price(price: str) -> float:
        """Convert price to probability."""
        try:
            return float(Decimal(price))
        except:
            return 0.0

    @staticmethod
    def get_multi_outcome_prices(market_id: str, outcomes: List[Dict]) -> Dict[str, Any]:
        """
        Fetch prices for markets with multiple outcomes.
        
        Args:
            market_id: The market identifier
            outcomes: List of outcome objects containing outcome info
            
        Returns:
            Dictionary containing price information for each outcome
        """
        price_data = {}
        
        try:
            # Fetch order book data
            url = f"https://clob.polymarket.com/orderbook/book/{market_id}"
            response = requests.get(url)
            response.raise_for_status()
            order_book = response.json()
            
            total_implied_probability = 0
            outcome_prices = {}
            
            # Process each outcome
            for outcome in outcomes:
                outcome_id = outcome.get('id')
                outcome_name = outcome.get('name')
                
                # Get best bid/ask for this outcome
                bids = order_book.get(f'bids_{outcome_id}', [{'price': '0'}])
                asks = order_book.get(f'asks_{outcome_id}', [{'price': '1'}])
                
                best_bid = MarketPriceInfo.get_probability_from_price(bids[0]['price'])
                best_ask = MarketPriceInfo.get_probability_from_price(asks[0]['price'])
                
                # Calculate mid price
                mid_price = (best_bid + best_ask) / 2
                
                outcome_prices[outcome_name] = {
                    'probability': mid_price,
                    'best_bid': best_bid,
                    'best_ask': best_ask,
                    'bid_ask_spread': best_ask - best_bid
                }
                
                total_implied_probability += mid_price
            
            # Calculate normalized probabilities
            if total_implied_probability > 0:
                for outcome_name in outcome_prices:
                    outcome_prices[outcome_name]['normalized_probability'] = (
                        outcome_prices[outcome_name]['probability'] / total_implied_probability
                    )
            
            price_data = {
                'outcome_prices': outcome_prices,
                'total_implied_probability': total_implied_probability,
                'market_efficiency': abs(1 - total_implied_probability),  # How far from 100%
                'average_spread': sum(o['bid_ask_spread'] for o in outcome_prices.values()) / len(outcomes)
            }
            
        except Exception as e:
            print(f"Error fetching multi-outcome prices for market {market_id}: {e}")
            price_data = {
                'outcome_prices': {outcome['name']: {
                    'probability': 0,
                    'normalized_probability': 0,
                    'best_bid': 0,
                    'best_ask': 1,
                    'bid_ask_spread': 1
                } for outcome in outcomes},
                'total_implied_probability': 0,
                'market_efficiency': 1,
                'average_spread': 1
            }
            
        return price_data

    @staticmethod
    def get_market_prices(market_id: str, outcomes: List[Dict]) -> Dict[str, Any]:
        """
        Get prices based on number of outcomes.
        """
        if len(outcomes) == 2 and any(o['name'].lower() in ['yes', 'no'] for o in outcomes):
            # Binary market
            return MarketPriceInfo.get_binary_market_prices(market_id)
        else:
            # Multi-outcome market
            return MarketPriceInfo.get_multi_outcome_prices(market_id, outcomes)

    @staticmethod
    def get_binary_market_prices(market_id: str) -> Dict[str, Any]:
        """Fetch latest prices for a binary (Yes/No) market."""
        url = f"https://clob.polymarket.com/orderbook/book/{market_id}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Get best bid/ask for YES
            yes_best_bid = data.get('bids', [{}])[0].get('price', '0')
            yes_best_ask = data.get('asks', [{}])[0].get('price', '1')
            
            # Calculate mid price
            yes_mid = (MarketPriceInfo.get_probability_from_price(yes_best_bid) + 
                      MarketPriceInfo.get_probability_from_price(yes_best_ask)) / 2
            
            return {
                'outcome_prices': {
                    'Yes': {
                        'probability': yes_mid,
                        'normalized_probability': yes_mid,
                        'best_bid': MarketPriceInfo.get_probability_from_price(yes_best_bid),
                        'best_ask': MarketPriceInfo.get_probability_from_price(yes_best_ask),
                        'bid_ask_spread': (MarketPriceInfo.get_probability_from_price(yes_best_ask) - 
                                         MarketPriceInfo.get_probability_from_price(yes_best_bid))
                    },
                    'No': {
                        'probability': 1 - yes_mid,
                        'normalized_probability': 1 - yes_mid,
                        'best_bid': 1 - MarketPriceInfo.get_probability_from_price(yes_best_ask),
                        'best_ask': 1 - MarketPriceInfo.get_probability_from_price(yes_best_bid),
                        'bid_ask_spread': (MarketPriceInfo.get_probability_from_price(yes_best_ask) - 
                                         MarketPriceInfo.get_probability_from_price(yes_best_bid))
                    }
                },
                'total_implied_probability': 1,
                'market_efficiency': 0,
                'average_spread': (MarketPriceInfo.get_probability_from_price(yes_best_ask) - 
                                 MarketPriceInfo.get_probability_from_price(yes_best_bid))
            }
        except Exception as e:
            print(f"Error fetching prices for market {market_id}: {e}")
            return {
                'outcome_prices': {
                    'Yes': {'probability': 0, 'normalized_probability': 0, 'best_bid': 0, 'best_ask': 1, 'bid_ask_spread': 1},
                    'No': {'probability': 0, 'normalized_probability': 0, 'best_bid': 0, 'best_ask': 1, 'bid_ask_spread': 1}
                },
                'total_implied_probability': 0,
                'market_efficiency': 1,
                'average_spread': 1
            }

def get_compact_market_info(market: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant market information including prices."""
    market_id = market.get('id')
    outcomes = market.get('outcomes', [])
    prices = MarketPriceInfo.get_market_prices(market_id, outcomes)
    
    return {
        "id": market_id,
        "question": market.get('question'),
        "description": market.get('description'),
        "outcomes": [outcome.get('name') for outcome in outcomes],
        "volume_24h": float(market.get('volume24h', 0)),
        "end_date": market.get('endDate'),
        "category": market.get('category'),
        "tags": market.get('tags', []),
        "prices": prices,
        "liquidity_score": float(market.get('liquidity', 0)),
        "timestamp": datetime.now().isoformat()
    }

# Rest of the code remains the same...


def fetch_active_markets(required_tags: List[str] = ["Politics"]) -> List[Dict[str, Any]]:
    """
    Fetch all active markets that contain ALL specified tags.
    
    Args:
        required_tags: List of tags that must all be present in a market
    
    Returns:
        List of markets containing all required tags
    """
    all_markets = []
    next_cursor = ""
    
    while next_cursor != "LTE=":
        url = f"https://clob.polymarket.com/markets"
        if next_cursor:
            url += f"?next_cursor={next_cursor}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Filter for active, non-closed markets with ALL required tags
            filtered_markets = [
                get_compact_market_info(market) 
                for market in data.get('data', [])
                if (not market.get('closed', True) 
                    and market.get('active', False)
                    and all(tag in market.get('tags', []) for tag in required_tags))
            ]
            
            all_markets.extend(filtered_markets)
            next_cursor = data.get('next_cursor', "LTE=")
            print(f"Fetched {len(filtered_markets)} markets with tags {required_tags}. Total: {len(all_markets)}")
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching markets: {e}")
            break
    
    return all_markets

def save_markets_to_file(markets: List[Dict[str, Any]], 
                        filename: str,
                        required_tags: List[str]) -> None:
    """
    Save markets to JSON file with timestamp and tag information.
    
    Args:
        markets: List of market data to save
        filename: Base filename to use
        required_tags: List of tags used to filter markets
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tags_str = "_".join(required_tags).lower()
    filename = f"{filename}_{tags_str}_{timestamp}.json"
    
    with open(filename, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "required_tags": required_tags,
            "market_count": len(markets),
            "markets": markets
        }, f, indent=2)
    
    print(f"Saved {len(markets)} markets to {filename}")

if __name__ == "__main__":
    # Example usage with multiple tags
    required_tags = ["Ukraine"]  # Markets must have both tags
    markets = fetch_active_markets(required_tags=required_tags)
    save_markets_to_file(markets, "polymarket_markets", required_tags)
