"""Predefined stock lists for common portfolios."""

# Vanguard Canadian ETFs (verified working) - use .TO suffix
VANGUARD_CANADA = [
    "VFV.TO",  # Vanguard S&P 500 Index ETF (CAD)
    "VUN.TO",  # Vanguard US Total Market Index ETF (CAD)
    "VEE.TO",  # Vanguard FTSE Emerging Markets Index ETF (CAD)
    "VUS.TO",  # Vanguard US Total Market Index ETF (CAD-hedged)
    "VCN.TO",  # Vanguard FTSE Canada Index ETF
    "VIU.TO",  # Vanguard FTSE International ex US Index ETF (CAD)
    "VRE.TO",  # Vanguard FTSE Canadian Real Estate Index ETF
    "VGRO.TO", # Vanguard Growth ETF Portfolio
    "VBAL.TO", # Vanguard Balanced ETF Portfolio
    "VDY.TO",  # Vanguard Dividend Yield Index ETF
]

# Vanguard US ETFs (verified working)
VANGUARD_US = [
    "VOO",  # Vanguard S&P 500 ETF
    "VTI",  # Vanguard Total Stock Market ETF
    "VEA",  # Vanguard FTSE Developed Markets ETF
    "VWO",  # Vanguard FTSE Emerging Markets ETF
    "VUG",  # Vanguard Growth ETF
    "VTV",  # Vanguard Value ETF
    "BND",  # Vanguard Total Bond Market ETF
    "VNQ",  # Vanguard Real Estate ETF
    "VIG",  # Vanguard Dividend Appreciation ETF
    "VCIT", # Vanguard Intermediate-Term Corporate Bond ETF
    "VCSH", # Vanguard Short-Term Corporate Bond ETF
    "SHY",  # Vanguard 1-3 Year Treasury Bond ETF
]

# iShares Canadian ETFs (for comparison)
ISHARES_CANADA = [
    "XUU",  # iShares Core S&P US Total Market Index ETF
    "XEF",  # iShares Core MSCI EAFE Index ETF
    "XIC",  # iShares Core MSCI Canada Index ETF
    "XSP",  # iShares Core S&P 500 Index ETF
    "XGRO", # iShares Growth ETF Portfolio
    "XBAL", # iShares Balanced ETF Portfolio
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
    "AMD",   # Advanced Micro Devices
    "INTC",  # Intel
    "CRM",   # Salesforce
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
    "DIS",   # Disney
    "NFLX",  # Netflix
    "KO",    # Coca-Cola
]

# Combined list (30 stocks)
ALL = VANGUARD_CANADA[:12] + VANGUARD_US[:8] + US_TECH[:5] + US_BLUE_CHIP[:5]

__all__ = [
    "VANGUARD_CANADA",
    "VANGUARD_US", 
    "ISHARES_CANADA",
    "US_TECH",
    "US_BLUE_CHIP",
    "ALL",
]
