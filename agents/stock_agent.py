import re
from tools.vnstock_tool import get_stock_price, parse_time_from_query
from vnstock import Listing

class StockAgent:
    def __init__(self, name="StockAgent"):
        self.name = name
        self.valid_symbols = self._load_symbols()

    def _load_symbols(self):
        """Tải danh sách mã cổ phiếu hợp lệ từ VCI (vnstock 3.2.x)."""
        try:
            listing = Listing()
            df = listing.all_symbols()
            tickers = df["symbol"].dropna().unique().tolist() 
            print(f"✅ Đã tải {len(tickers)} mã cổ phiếu hợp lệ từ sàn VN")
            return tickers
        except Exception as e:
            print(f"⚠️ Không thể tải danh sách mã cổ phiếu: {e}")
            return []

    def extract_symbol(self, query: str):
        """Trích xuất mã cổ phiếu từ câu hỏi — tránh bắt nhầm chữ 'TIN' trong 'tin tức'."""
        query_up = query.upper()
        candidates = re.findall(r"\b[A-Z]{3,5}\b", query_up)

        # Lọc theo danh sách hợp lệ
        valid = [c for c in candidates if c in self.valid_symbols]

        if not valid:
            return None

        # Ưu tiên mã xuất hiện SAU các từ khóa “về”, “của”, “mã”, “cổ phiếu”
        keywords = ["VỀ", "CỦA", "MÃ", "CỔ PHIẾU"]
        for kw in keywords:
            for v in valid:
                pattern = rf"{kw}\s+{v}\b"
                if re.search(pattern, query_up):
                    return v

        # Nếu không match theo ngữ cảnh → chọn mã cuối cùng (thường là mã thật)
        return valid[-1]

    def extract_time(self, query: str):
        q = query.lower()
        if "hôm qua" in q:
            return "yesterday"
        elif "hôm nay" in q:
            return "today"
        else:
            return "latest"

    def handle_request(self, query: str):
        symbol = self.extract_symbol(query)
        when = self.extract_time(query)
        hour = parse_time_from_query(query)

        if not symbol:
            return "Vui lòng cung cấp mã cổ phiếu hợp lệ (ví dụ: FPT, VNM, HPG, MWG, ...)."

        return get_stock_price(symbol, when, hour)
