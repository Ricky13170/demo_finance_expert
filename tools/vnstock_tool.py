from datetime import datetime, timedelta
from vnstock import Vnstock
import pandas as pd
import traceback
import re

def parse_time_from_query(query: str):
    """Phân tích giờ hoặc buổi trong câu hỏi."""
    query = query.lower()
    match = re.search(r'(\d{1,2})\s*h', query)
    if match:
        hour = int(match.group(1))
    else:
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
    if "chiều" in query and hour < 12:
        hour += 12
    return hour


def get_stock_price(symbol: str, when: str = "latest", hour: int = None):
    try:
        vnstock = Vnstock()
        today = datetime.today().strftime("%Y-%m-%d")
        start_date = (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d")

        print(f"🔍 symbol nhận được: [{symbol}]")


        df = None
        for source in ["TCBS", "VCI"]:
            try:
                stock_obj = vnstock.stock(symbol=symbol, source=source)
                if hour is not None:
                    df = stock_obj.quote.intraday(start=today, end=today, interval="1m")
                else:
                    df = stock_obj.quote.history(start=start_date, end=today, interval="1D")
                if df is not None and not df.empty:
                    print(f" Dữ liệu lấy thành công từ nguồn {source}")
                    break
            except Exception as e:
                print(f"Lỗi khi lấy dữ liệu từ {source}: {e}")
                continue

        if df is None or df.empty:
            return f"⚠️ Không tìm thấy dữ liệu cho mã {symbol}. Có thể thị trường chưa mở hoặc API tạm lỗi."

        if hour is not None:
            df["time"] = pd.to_datetime(df["time"], errors="coerce")
            df = df.dropna(subset=["time"])
            target_time = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
            df["diff"] = abs(df["time"] - target_time)
            row = df.loc[df["diff"].idxmin()]
            return f"Giá {symbol} gần {hour}h là {row['close']:,} VND (thời gian: {row['time']})"

        date_col = "time" if "time" in df.columns else (
            "date" if "date" in df.columns else df.columns[0]
        )

        if when == "yesterday" and len(df) >= 2:
            row = df.iloc[-2]
        else:
            row = df.iloc[-1]

        return f"💰 Giá đóng cửa của {symbol} vào ngày {row[date_col]} là {row['close']:,} VND"

    except Exception as e:
        print("❌ Lỗi chi tiết:\n", traceback.format_exc())
        return f"❌ Lỗi khi truy vấn dữ liệu cho {symbol}: {e}"
