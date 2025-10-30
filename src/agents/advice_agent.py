"""Advice agent for stock analysis and investment recommendations."""
from vnstock import Vnstock, Listing
import pandas as pd
import re
from datetime import datetime
import unicodedata
import traceback


# Load valid symbols once at module level
VALID_SYMBOLS = []
try:
    listing = Listing()
    df_listing = listing.all_symbols()
    if isinstance(df_listing, pd.DataFrame) and 'symbol' in df_listing.columns:
        VALID_SYMBOLS = [s.upper() for s in df_listing['symbol'].astype(str).tolist()]
        print(f"Loaded {len(VALID_SYMBOLS)} valid stock symbols from VN exchange")
    else:
        print("Warning: Listing.all_symbols() did not return valid DataFrame. VALID_SYMBOLS empty.")
except Exception as e:
    print(f"Error loading stock symbols: {e}")
    VALID_SYMBOLS = []


def normalize_text(text: str) -> str:
    """Normalize Vietnamese text: remove diacritics, convert to uppercase.
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    text = unicodedata.normalize('NFD', text)
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    return text.upper()


def extract_symbol_from_question(question: str) -> str:
    """Extract valid stock symbol from question.
    
    Args:
        question: User question string
        
    Returns:
        Stock symbol or None if not found
    """
    if not question:
        return None
    
    q_norm = normalize_text(question)
    q_norm = q_norm.upper()
    candidates = re.findall(r'\b[A-Z]{2,4}\b', q_norm)
    
    # Filter out common words that are not stock symbols
    excluded = {
        'MUA', 'BAN', 'GIU', 'NEN', 'CO', 'KHONG', 'HOM', 'NAY',
        'QUA', 'GIA', 'PHIEU', 'CP', 'CUA', 'NAO', 'GI',
        'PHAN', 'TICH', 'DAU', 'TU', 'MINH',
        'BUY', 'SELL', 'SHOULD', 'NOT', 'PRICE', 'STOCK', 'SYMBOL'
    }
    
    if VALID_SYMBOLS:
        for cand in reversed(candidates):
            if cand not in excluded and cand in VALID_SYMBOLS:
                print(f"Detected stock symbol in question: {cand}")
                return cand
    
    # Fallback if symbol list not loaded
    for cand in reversed(candidates):
        if cand not in excluded:
            return cand
    
    return None


def explain_decision(price_ratio: float, trend_5d: float, volatility: float, price_change_percent: float) -> str:
    """Generate explanation for investment decision.
    
    Args:
        price_ratio: Current price / 30-day average
        trend_5d: 5-day trend percentage
        volatility: 30-day volatility percentage
        price_change_percent: Latest session price change percentage
        
    Returns:
        Explanation text
    """
    reasons = []
    
    if price_ratio < 0.90:
        reasons.append("Price is below 30-day average (>10%) - potential accumulation zone.")
    elif price_ratio > 1.10:
        reasons.append("Price is above 30-day average (>10%) - may be overbought.")
    else:
        reasons.append("Price is around 30-day average - neutral signal.")
    
    if trend_5d > 2:
        reasons.append(f"5-day trend is UP {trend_5d:.2f}%.")
    elif trend_5d < -2:
        reasons.append(f"5-day trend is DOWN {trend_5d:.2f}%.")
    else:
        reasons.append("5-day trend is sideways.")
    
    if volatility > 10:
        reasons.append(f"30-day volatility is high ({volatility:.1f}%).")
    else:
        reasons.append(f"30-day volatility is low ({volatility:.1f}%).")
    
    reasons.append(f"Latest session change: {price_change_percent:+.2f}%.")
    return " ".join(reasons)


def analyze_stock(user_query: str) -> str:
    """Analyze stock and provide investment advice.
    
    Args:
        user_query: User query string
        
    Returns:
        Stock analysis report
    """
    try:
        symbol = extract_symbol_from_question(user_query)
        if symbol is None:
            return (
                "Could not find a valid stock symbol in your question.\n\n"
                "Please try asking:\n"
                "• 'What is the price of FPT stock today?'\n"
                "• 'Should I buy MWG?'\n"
                "• 'Analyze HPG stock for me.'"
            )
        
        print(f"Starting stock analysis for {symbol}...")
        
        vnstock = Vnstock()
        stock_obj = vnstock.stock(symbol=symbol, source='VCI')
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - pd.Timedelta(days=60)).strftime("%Y-%m-%d")
        hist = stock_obj.quote.history(start=start_date, end=end_date, interval='1D')
        
        if hist is None or hist.empty:
            return f"No historical data available for symbol {symbol}"
        
        # Calculate metrics
        current_price = float(hist.iloc[-1]['close'])
        prev_price = float(hist.iloc[-2]['close']) if len(hist) > 1 else current_price
        price_change = current_price - prev_price
        price_change_percent = (price_change / prev_price) * 100 if prev_price != 0 else 0.0
        
        # 30-day statistics
        last_30 = hist.tail(30)
        avg_30d = last_30['close'].mean()
        min_30d = last_30['close'].min()
        max_30d = last_30['close'].max()
        volatility = (max_30d - min_30d) / avg_30d * 100 if avg_30d != 0 else 0.0
        
        # 5-day trend
        trend_5d = 0.0
        if len(hist) >= 5:
            last_5 = hist.tail(5)['close'].astype(float)
            trend_5d = (last_5.iloc[-1] - last_5.iloc[0]) / last_5.iloc[0] * 100 if last_5.iloc[0] != 0 else 0.0
        
        price_ratio = current_price / avg_30d if avg_30d != 0 else 1.0
        
        # Build analysis report
        result = f"STOCK ANALYSIS: {symbol}\n{'='*50}\n"
        result += f"Current Price: {current_price:,.0f} VND\n"
        result += f"Change: {price_change:+,.0f} VND ({price_change_percent:+.2f}%)\n"
        result += f"30-day Average: {avg_30d:,.0f} VND\n"
        result += f"30-day Volatility: {volatility:.1f}%\n\n"
        
        # Trend analysis
        result += "TREND ANALYSIS:\n"
        if price_ratio < 0.95:
            result += "- Price is BELOW 30-day average\n"
        elif price_ratio > 1.05:
            result += "- Price is ABOVE 30-day average\n"
        else:
            result += "- Price is AROUND 30-day average\n"
        
        if trend_5d > 2:
            result += "- 5-day trend is UPWARD\n"
        elif trend_5d < -2:
            result += "- 5-day trend is DOWNWARD\n"
        else:
            result += "- 5-day trend is SIDEWAYS\n"
        
        # Recommendation
        result += "\nRECOMMENDATION:\n"
        if price_ratio < 0.90:
            decision = "Consider BUYING - price is in lower zone"
        elif price_ratio > 1.10:
            decision = "Be CAUTIOUS - price is in higher zone"
        else:
            decision = "NEUTRAL - no clear signal"
        result += f"{decision}\n\n"
        
        # Explanation
        result += "REASONING:\n"
        result += explain_decision(price_ratio, trend_5d, volatility, price_change_percent)
        
        result += "\n\nDISCLAIMER: This is automated analysis, NOT investment advice.\n"
        result += f"Analysis time: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        return result
    
    except Exception as e:
        print(f"Error in stock analysis:\n{traceback.format_exc()}")
        return f"Error analyzing stock: {str(e)}"

