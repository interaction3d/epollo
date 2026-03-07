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
        trading_days = int(days * 5 / 7) + 1
        past_price = hist['Close'].iloc[-trading_days]
        
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


def get_multi_period_changes(symbols: List[str], periods: List[int] = None) -> Dict[str, Dict[int, Optional[float]]]:
    """Get price changes for multiple symbols across multiple periods.
    
    Args:
        symbols: List of stock ticker symbols
        periods: List of day periods (default: [7, 30, 60, 90])
        
    Returns:
        Dict mapping symbol to dict of period -> change percentage
    """
    if periods is None:
        periods = [7, 30, 60, 90]
    
    results = {}
    
    for symbol in symbols:
        logger.info(f"Fetching {symbol}...")
        results[symbol] = {}
        for days in periods:
            results[symbol][days] = get_price_change(symbol, days)
    
    return results


def print_multi_period_table(symbols: List[str], periods: List[int] = None):
    """Print a formatted table of price changes across multiple periods.
    
    Args:
        symbols: List of stock ticker symbols
        periods: List of day periods to show
    """
    if periods is None:
        periods = [7, 30, 60, 90]
    
    data = get_multi_period_changes(symbols, periods)
    
    # Print header
    header = f"{'Symbol':<8}"
    for p in periods:
        header += f"{p:>10}d"
    print(header)
    print("-" * len(header))
    
    # Colors
    GREEN = "\033[92m"
    RED = "\033[91m"
    RESET = "\033[0m"
    
    # Print each row
    for symbol in symbols:
        row = f"{symbol:<8}"
        for p in periods:
            val = data[symbol].get(p)
            if val is not None:
                color = GREEN if val > 0 else RED if val < 0 else ""
                row += f" {color}{val:>+9.2f}%{RESET}"
            else:
                row += f" {'N/A':>9}"
        print(row)


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
    import argparse
    
    parser = argparse.ArgumentParser(description="Stock price change fetcher")
    parser.add_argument("symbols", nargs="*", help="Stock symbols (default: VFV VUS AAPL)")
    parser.add_argument("-p", "--periods", nargs="+", type=int, default=[7, 30, 60, 90],
                        help="Periods in days (default: 7 30 60 90)")
    
    args = parser.parse_args()
    
    symbols = args.symbols if args.symbols else ["VFV", "VUS", "AAPL"]
    
    print(f"Getting price changes for: {symbols}")
    print(f"Periods: {args.periods} days")
    print()
    
    print_multi_period_table(symbols, args.periods)
