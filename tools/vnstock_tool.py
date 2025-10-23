from datetime import datetime, timedelta
from vnstock import Vnstock
import pandas as pd
import re

def parse_time_from_query(query: str):
    """Phân tích giờ hoặc buổi trong câu hỏi."""
    query = query.lower()
    match = re.search(r'(\d{1,2})\s*h', query)
    if match:
        hour = int(match.group(1))
    else:
        # Suy luận theo ngữ cảnh buổi
        if "sáng" in query:
            hour = 9
        elif "trưa" in query:
            hour = 12
        elif "chiều" in query:
            hour = 15
        elif "tối" in query:
            hour = 19
        else:
            return None

    # điều chỉnh ngữ cảnh: nếu có từ khóa 'chiều' mà giờ nhỏ hơn 12 -> cộng 12h
    if "chiều" in query and hour < 12:
        hour += 12
    return hour

def get_stock_price(symbol: str, when: str = "latest", hour: int = None):
    try:
        vnstock = Vnstock()
        stock_obj = vnstock.stock(symbol=symbol, source='VCI')
        
        today = datetime.today().strftime("%Y-%m-%d")
        start_date = (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d")

        # Nếu có yêu cầu theo giờ
        if hour is not None:
            # chỉ hỗ trợ hôm nay
            if when != "today" and when != "latest":
                return f"Dữ liệu theo giờ chỉ khả dụng cho hôm nay. Với hôm qua, chỉ có giá đóng cửa."

            df = stock_obj.quote.intraday(start=today, end=today, interval='1m')
            if df.empty:
                return f"Không có dữ liệu intraday cho {symbol} hôm nay"

            df['time'] = pd.to_datetime(df['time'])
            target_time = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
            df['diff'] = abs(df['time'] - target_time)
            row = df.loc[df['diff'].idxmin()]

            price = row['close']
            timestamp = row['time']
            return f"Giá của {symbol} gần {hour}h là {price:,} VND (thời gian: {timestamp})"

        # Nếu chỉ muốn giá đóng cửa
        df = stock_obj.quote.history(start=start_date, end=today, interval='1D')
        if df.empty:
            return f"Không tìm thấy dữ liệu cho mã {symbol}"

        if when == "yesterday":
            price = df.iloc[-2]['close']
            date = df.iloc[-2]['time']
        else:
            price = df.iloc[-1]['close']
            date = df.iloc[-1]['time']

        return f"Giá đóng cửa của {symbol} vào ngày {date} là {price:,} VND"

    except Exception as e:
        return f"Lỗi khi truy vấn dữ liệu: {e}"