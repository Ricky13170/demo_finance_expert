"""
Stock Agent - Agent tra cứu giá cổ phiếu

Nhiệm vụ:
- Trích xuất mã cổ phiếu từ câu hỏi người dùng
- Lấy giá cổ phiếu từ vnstock API
- Trả về thông tin giá cổ phiếu theo định dạng dễ đọc
"""
import re
from vnstock import Listing, Vnstock
from datetime import datetime, timedelta


class StockAgent:
    """
    Agent chuyên tra cứu giá cổ phiếu Việt Nam
    
    Chức năng:
    - Tìm mã cổ phiếu trong câu hỏi người dùng
    - Lấy giá cổ phiếu từ vnstock API
    - Hiển thị thông tin giá theo định dạng dễ đọc
    """
    
    def __init__(self):
        """Khởi tạo StockAgent"""
        # Load danh sách mã cổ phiếu hợp lệ từ VN exchange
        self.valid_symbols = self._load_symbols()
    
    def _load_symbols(self) -> list:
        """Load danh sách mã cổ phiếu hợp lệ từ VN exchange"""
        try:
            listing = Listing()
            df = listing.all_symbols()
            tickers = df["symbol"].dropna().unique().tolist()
            print(f"[StockAgent] Đã load {len(tickers)} mã cổ phiếu hợp lệ")
            return tickers
        except Exception as e:
            print(f"[WARN] Không thể load danh sách mã cổ phiếu: {e}")
            return []
    
    def extract_symbol(self, query: str) -> str:
        """
        Tìm mã cổ phiếu trong câu hỏi người dùng
        
        Ví dụ: "Giá cổ phiếu FPT hôm nay" → "FPT"
        """
        query_upper = query.upper()
        # Tìm các chuỗi chữ hoa có 3-5 ký tự (mã cổ phiếu)
        candidates = re.findall(r"\b[A-Z]{3,5}\b", query_upper)
        
        # Lọc các mã hợp lệ
        valid = [c for c in candidates if c in self.valid_symbols] if self.valid_symbols else candidates
        
        if not valid:
            return None
        
        # Ưu tiên mã xuất hiện sau từ khóa như "của", "mã", "cổ phiếu"
        keywords = ["VE", "CUA", "MA", "CO PHIEU", "ABOUT", "OF", "SYMBOL", "STOCK"]
        for kw in keywords:
            for v in valid:
                pattern = rf"{kw}\s+{v}\b"
                if re.search(pattern, query_upper):
                    return v
        
        # Nếu không tìm thấy theo context, trả về mã cuối cùng (thường là mã thực)
        return valid[-1]
    
    def handle_request(self, query: str) -> str:
        """
        Xử lý yêu cầu tra cứu giá cổ phiếu
        
        Args:
            query: Câu hỏi người dùng (ví dụ: "Giá FPT hôm nay")
            
        Returns:
            Thông tin giá cổ phiếu hoặc thông báo lỗi
        """
        # Tìm mã cổ phiếu trong câu hỏi
        symbol = self.extract_symbol(query)
        if not symbol:
            return "Vui lòng cung cấp mã cổ phiếu hợp lệ (ví dụ: FPT, VNM, HPG, MWG, ...)."
        
        try:
            # Khởi tạo vnstock và lấy dữ liệu
            vnstock = Vnstock()
            stock_obj = vnstock.stock(symbol=symbol, source='VCI')
            
            # Lấy giá hiện tại
            quote = stock_obj.quote()
            if quote is None or quote.empty:
                return f"Không tìm thấy dữ liệu cho mã {symbol}."
            
            # Lấy thông tin từ quote
            current_price = float(quote.iloc[-1]['close']) if not quote.empty else 0
            change = float(quote.iloc[-1]['change']) if 'change' in quote.columns else 0
            change_percent = float(quote.iloc[-1]['pctChange']) if 'pctChange' in quote.columns else 0
            
            # Format kết quả
            result = f"📊 GIÁ CỔ PHIẾU {symbol}\n"
            result += f"{'='*40}\n"
            result += f"Giá hiện tại: {current_price:,.0f} VND\n"
            result += f"Thay đổi: {change:+,.0f} VND ({change_percent:+.2f}%)\n"
            
            # Thêm thông tin volume nếu có
            if 'volume' in quote.columns:
                volume = float(quote.iloc[-1]['volume'])
                result += f"Khối lượng: {volume:,.0f}\n"
            
            return result
            
        except Exception as e:
            print(f"[ERROR] Lỗi khi lấy giá cổ phiếu {symbol}: {e}")
            return f"Lỗi khi tra cứu giá cổ phiếu {symbol}. Vui lòng thử lại sau."

