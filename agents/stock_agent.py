import re
from tools.vnstock_tool import get_stock_price, parse_time_from_query

class StockAgent:
    def __init__(self, name="StockAgent"):
        self.name = name

    def extract_symbol(self, query: str):
        """Trích xuất mã cổ phiếu từ câu hỏi"""
        matches = re.findall(r"\b[A-Z]{3,4}\b", query.upper())
        return matches[0] if matches else None

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
            return "Vui lòng cung cấp mã cổ phiếu (ví dụ: FPT, VNM, HPG, ...)"

        return get_stock_price(symbol, when, hour)