"""Predefined stock lists for common portfolios."""

# Canadian ETFs (use .TO suffix automatically)
CANADIAN_ETFS = [
    "VFV",  # Vanguard S&P 500
    "VUN",  # Vanguard US Total Market
    "VEE",  # Vanguard FTSE Emerging Markets
    "VUS",  # Vanguard US Total Market (CAD-hedged)
    "VCN",  # Vanguard FTSE Canada
    "VIU",  # Vanguard FTSE International ex-US
    "VXUS", # Vanguard Total International Stock
    "XUU",  # iShares Core S&P US Total Market
    "XEF",  # iShares Core MSCI EAFE
    "XIC",  # iShares Core MSCI Canada
]

# US Tech Stocks
US_TECH = [
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "GOOGL", # Alphabet
    "AMZN",  # Amazon
    "NVDA",  # NVIDIA
    "META",  # Meta
    "TSLA",  # Tesla
]

# US Blue Chip
US_BLUE_CHIP = [
    "JPM",   # JPMorgan
    "JNJ",   # Johnson & Johnson
    "V",     # Visa
    "PG",    # Procter & Gamble
    "UNH",   # UnitedHealth
    "HD",    # Home Depot
    "MA",    # Mastercard
]

# Combined list (20 stocks)
ALL = CANADIAN_ETFS[:10] + US_TECH[:5] + US_BLUE_CHIP[:5]

__all__ = [
    "CANADIAN_ETFS",
    "US_TECH",
    "US_BLUE_CHIP", 
    "ALL",
]
