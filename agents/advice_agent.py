from vnstock import Vnstock, Listing
import pandas as pd
import re
from datetime import datetime
import unicodedata
import traceback

VALID_SYMBOLS = []
try:
    listing = Listing()
    df_listing = listing.all_symbols()
    if isinstance(df_listing, pd.DataFrame) and 'symbol' in df_listing.columns:
        VALID_SYMBOLS = [s.upper() for s in df_listing['symbol'].astype(str).tolist()]
        print(f"✅ Đã tải {len(VALID_SYMBOLS)} mã cổ phiếu hợp lệ từ sàn VN")
    else:
        print("Listing.all_symbols() không trả về DataFrame hợp lệ. VALID_SYMBOLS rỗng.")
except Exception as e:
    print(f"Không thể tải danh sách mã cổ phiếu: {e}")
    VALID_SYMBOLS = []


def normalize_text(text: str):
    """Chuẩn hóa chuỗi: bỏ dấu tiếng Việt, chuyển về uppercase."""
    text = unicodedata.normalize('NFD', text)
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    return text.upper()


def extract_symbol_from_question(question: str):
    """Phát hiện mã cổ phiếu hợp lệ từ câu hỏi."""
    if not question:
        return None

    q_norm = normalize_text(question)
    q_norm = q_norm.upper()
    candidates = re.findall(r'\b[A-Z]{2,4}\b', q_norm)

    # Bộ lọc loại trừ các từ không phải mã chứng khoán
    excluded = {
        'MUA', 'BAN', 'GIU', 'NEN', 'CO', 'KHONG', 'HOM', 'NAY',
        'QUA', 'GIA', 'CO', 'PHIEU', 'CP', 'CUA', 'NAO', 'GI',
        'PHAN', 'TICH', 'DAU', 'TU', 'MINH', 'KHONG'
    }

    if VALID_SYMBOLS:
        for cand in reversed(candidates):
            if cand not in excluded and cand in VALID_SYMBOLS:
                print(f"🔍 Phát hiện mã cổ phiếu trong câu hỏi: {cand}")
                return cand

    # fallback nếu chưa có danh sách symbol
    for cand in reversed(candidates):
        if cand not in excluded:
            return cand

    return None

def explain_decision(price_ratio, trend_5d, volatility, price_change_percent):
    reasons = []
    if price_ratio < 0.90:
        reasons.append("Giá thấp hơn trung bình 30 ngày (>10%) — vùng tích lũy tiềm năng.")
    elif price_ratio > 1.10:
        reasons.append("Giá cao hơn trung bình 30 ngày (>10%) — có thể đã vào vùng quá mua.")
    else:
        reasons.append("Giá quanh mức trung bình 30 ngày — tín hiệu trung tính.")

    if trend_5d > 2:
        reasons.append(f"Xu hướng 5 ngày TĂNG {trend_5d:.2f}%.")
    elif trend_5d < -2:
        reasons.append(f"Xu hướng 5 ngày GIẢM {trend_5d:.2f}%.")
    else:
        reasons.append("Xu hướng 5 ngày đi ngang.")

    if volatility > 10:
        reasons.append(f"Biến động 30 ngày cao ({volatility:.1f}%).")
    else:
        reasons.append(f"Biến động 30 ngày thấp ({volatility:.1f}%).")

    reasons.append(f"Thay đổi phiên gần nhất: {price_change_percent:+.2f}%.")
    return " ".join(reasons)


def analyze_stock(user_query: str):
    try:
        symbol = extract_symbol_from_question(user_query)
        if symbol is None:
            return (
                "⚠️ Mình không tìm thấy mã cổ phiếu hợp lệ trong câu hỏi của bạn.\n\n"
                "💡 Hãy thử hỏi như:\n"
                "• 'Giá cổ phiếu FPT hôm nay bao nhiêu?'\n"
                "• 'Có nên mua MWG không?'\n"
                "• 'Phân tích cổ phiếu HPG giúp mình.'"
            )

        print(f"📊 Bắt đầu phân tích cổ phiếu {symbol}...")

        vnstock = Vnstock()
        stock_obj = vnstock.stock(symbol=symbol, source='VCI')

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - pd.Timedelta(days=60)).strftime("%Y-%m-%d")
        hist = stock_obj.quote.history(start=start_date, end=end_date, interval='1D')

        if hist is None or hist.empty:
            return f"⚠️ Không có dữ liệu lịch sử cho mã {symbol}"

        current_price = float(hist.iloc[-1]['close'])
        prev_price = float(hist.iloc[-2]['close']) if len(hist) > 1 else current_price
        price_change = current_price - prev_price
        price_change_percent = (price_change / prev_price) * 100 if prev_price != 0 else 0.0

        last_30 = hist.tail(30)
        avg_30d = last_30['close'].mean()
        min_30d = last_30['close'].min()
        max_30d = last_30['close'].max()
        volatility = (max_30d - min_30d) / avg_30d * 100 if avg_30d != 0 else 0.0

        # xu hướng 5 ngày
        trend_5d = 0.0
        if len(hist) >= 5:
            last_5 = hist.tail(5)['close'].astype(float)
            trend_5d = (last_5.iloc[-1] - last_5.iloc[0]) / last_5.iloc[0] * 100 if last_5.iloc[0] != 0 else 0.0

        price_ratio = current_price / avg_30d if avg_30d != 0 else 1.0

        # 🧠 tạo bản phân tích
        result = f"📊 PHÂN TÍCH CỔ PHIẾU {symbol}\n{'='*50}\n"
        result += f"💰 Giá hiện tại: {current_price:,.0f} VND\n"
        result += f"🔺 Thay đổi: {price_change:+,.0f} VND ({price_change_percent:+.2f}%)\n"
        result += f"📆 Trung bình 30 ngày: {avg_30d:,.0f} VND\n"
        result += f"📊 Dao động 30 ngày: {volatility:.1f}%\n\n"

        # 📈 xu hướng
        result += "📈 XU HƯỚNG:\n"
        if price_ratio < 0.95:
            result += "- Giá THẤP hơn trung bình 30 ngày\n"
        elif price_ratio > 1.05:
            result += "- Giá CAO hơn trung bình 30 ngày\n"
        else:
            result += "- Giá QUANH mức trung bình\n"

        if trend_5d > 2:
            result += "- Xu hướng TĂNG trong 5 ngày\n"
        elif trend_5d < -2:
            result += "- Xu hướng GIẢM trong 5 ngày\n"
        else:
            result += "- Xu hướng đi NGANG\n"

        # 💡 khuyến nghị
        result += "\n🤔 KHUYẾN NGHỊ:\n"
        if price_ratio < 0.90:
            decision = "✅ Có thể MUA - giá đang ở vùng thấp"
        elif price_ratio > 1.10:
            decision = "⚠️ Cẩn trọng - giá đang ở vùng cao"
        else:
            decision = "🤔 Cân nhắc - chưa có tín hiệu rõ"
        result += f"{decision}\n\n"

        # 🔍 giải thích
        result += "🔍 Lý do:\n"
        result += explain_decision(price_ratio, trend_5d, volatility, price_change_percent)

        result += "\n\n💡 Lưu ý: Đây là phân tích tự động, KHÔNG phải khuyến nghị đầu tư.\n"
        result += f"🕒 Thời gian phân tích: {datetime.now().strftime('%d/%m/%Y %H:%M')}"

        return result

    except Exception as e:
        print("❌ Lỗi chi tiết:\n", traceback.format_exc())
        return f"❌ Lỗi khi phân tích cổ phiếu: {str(e)}"
