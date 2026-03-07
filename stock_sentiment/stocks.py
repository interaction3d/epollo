"""Stock data fetcher for getting price change percentages."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

try:
    import yfinance as yf
except ImportError:
    logger.warning("yfinance not installed. Install with: pip install yfinance")


def get_price_change(symbol: str, days: int = 30) -> Optional[float]:
    """Get the price change percentage over the last N days.
    
    Args:
        symbol: Stock ticker symbol (e.g., "VFV", "VUS", "AAPL")
               Canadian stocks can use suffix (e.g., "VFV.TO")
        days: Number of days to look back (default: 30)
        
    Returns:
        Percentage change as float, or None if error
    """
    try:
        ticker = yf.Ticker(symbol)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 10)
        
        hist = ticker.history(start=start_date, end=end_date)
        
        if hist.empty or len(hist) < 2:
            if not symbol.endswith('.TO'):
                return get_price_change(symbol + '.TO', days)
            logger.warning(f"No data found for {symbol}")
            return None
        
        current_price = hist['Close'].iloc[-1]
        past_price = hist['Close'].iloc[0]
        
        change_pct = ((current_price - past_price) / past_price) * 100
        
        return round(change_pct, 2)
    
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return None


def get_price_changes(symbols: List[str], days: int = 30) -> Dict[str, Optional[float]]:
    """Get price changes for multiple symbols.
    
    Args:
        symbols: List of stock ticker symbols
        days: Number of days to look back (default: 30)
        
    Returns:
        Dict mapping symbol to change percentage
    """
    results = {}
    
    for symbol in symbols:
        logger.info(f"Fetching {symbol}...")
        results[symbol] = get_price_change(symbol, days)
    
    return results


def get_stock_info(symbol: str) -> Optional[Dict]:
    """Get current stock info.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Dict with stock info or None if error
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            "symbol": symbol,
            "name": info.get("shortName", info.get("longName", "N/A")),
            "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
            "day_change": info.get("regularMarketDayChange"),
            "day_change_pct": info.get("regularMarketDayChange"),
            "market_cap": info.get("marketCap"),
            "volume": info.get("volume"),
            "pe_ratio": info.get("trailingPE"),
        }
    
    except Exception as e:
        logger.error(f"Error fetching info for {symbol}: {e}")
        return None


if __name__ == "__main__":
    import sys
    
    symbols = sys.argv[1:] if len(sys.argv) > 1 else ["VFV", "VUS", "AAPL"]
    days = 30
    
    print(f"Getting {days}-day price changes for: {symbols}\n")
    
    changes = get_price_changes(symbols, days)
    
    print("=" * 40)
    for symbol, change in changes.items():
        if change is not None:
            arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
            color = "\033[92m" if change > 0 else "\033[91m" if change < 0 else "\033[0m"
            reset = "\033[0m"
            print(f"{symbol}: {arrow} {color}{change:+.2f}%{reset}")
        else:
            print(f"{symbol}: Error fetching data")
    print("=" * 40)
