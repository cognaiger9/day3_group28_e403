"""
tools.py - Travel Advisory Tools
Use case: Tư vấn du lịch thông minh - Group 28

get_weather: dùng Open-Meteo API (miễn phí, không cần API key, dữ liệu thực tế)
search_attractions / estimate_budget: dùng database nội bộ
"""

import requests

# ─────────────────────────────────────────────────────────────────────────────
# WMO WEATHER CODE → mô tả tiếng Việt
# ─────────────────────────────────────────────────────────────────────────────

_WMO_CODE = {
    0:  "Trời quang, nắng đẹp",
    1:  "Ít mây",
    2:  "Có mây rải rác",
    3:  "Trời âm u, nhiều mây",
    45: "Sương mù",
    48: "Sương mù có băng tuyết",
    51: "Mưa phùn nhẹ",
    53: "Mưa phùn vừa",
    55: "Mưa phùn dày",
    61: "Mưa nhẹ",
    63: "Mưa vừa",
    65: "Mưa to",
    71: "Tuyết nhẹ",
    73: "Tuyết vừa",
    75: "Tuyết dày",
    80: "Mưa rào nhẹ",
    81: "Mưa rào vừa",
    82: "Mưa rào lớn",
    85: "Mưa tuyết nhẹ",
    86: "Mưa tuyết nặng",
    95: "Có giông bão",
    96: "Giông kèm mưa đá nhỏ",
    99: "Giông kèm mưa đá lớn",
}

# ─────────────────────────────────────────────────────────────────────────────
# WIND DIRECTION
# ─────────────────────────────────────────────────────────────────────────────

def _wind_dir(deg: float) -> str:
    dirs = ["Bắc","ĐB","Đông","ĐN","Nam","TN","Tây","TB"]
    return dirs[round(deg / 45) % 8]

_ATTRACTIONS_DB = {
    # ── Hà Nội ──
    ("hà nội", "lịch sử"):      ["Văn Miếu – Quốc Tử Giám (08:00-17:00, 30k)", "Hoàng Thành Thăng Long (08:00-17:00, 30k)", "Nhà tù Hỏa Lò (08:00-17:00, 30k)", "Bảo tàng Hồ Chí Minh (08:00-11:30 & 14:00-16:00, miễn phí)"],
    ("hà nội", "ẩm thực"):      ["Phố cổ Hàng Ngang - Hàng Đào (phở, bún chả, bánh mì)", "Chợ đêm Đồng Xuân (18:00-23:00)", "Bún bò Nam Bộ phố Hàng Điếu", "Cà phê trứng Giảng - 39 Nguyễn Hữu Huân"],
    ("hà nội", "thiên nhiên"):  ["Hồ Tây (đạp vịt, cà phê hồ)", "Vườn thú Thủ Lệ (07:30-17:00, 40k)", "Công viên Thống Nhất", "Hồ Hoàn Kiếm & Tháp Rùa"],
    ("hà nội", "mua sắm"):      ["Vincom Bà Triệu", "AEON Mall Long Biên", "Chợ Đồng Xuân", "Phố Hàng Ngang – hàng thủ công"],
    # ── Hội An ──
    ("hội an", "lịch sử"):      ["Phố cổ Hội An (vé 120k/5 điểm)", "Chùa Cầu Nhật Bản (thế kỷ 17)", "Bảo tàng Gốm sứ Mậu dịch", "Nhà cổ Tấn Ký (1 Nguyễn Thái Học)"],
    ("hội an", "ẩm thực"):      ["Cao Lầu - đặc sản số 1 Hội An", "Bánh mì Phượng - 2B Phan Châu Trinh", "Mì Quảng bà Mua", "Chợ đêm Hội An (18:00-22:00)"],
    ("hội an", "biển"):         ["Biển Cửa Đại (cách 4km)", "Biển An Bàng (ít đông hơn)", "Đảo Cù Lao Chàm (lặn biển, cần đặt tour)"],
    # ── Đà Nẵng ──
    ("đà nẵng", "thiên nhiên"): ["Bán đảo Sơn Trà & Chùa Linh Ứng", "Bãi biển Mỹ Khê (top 6 đẹp nhất châu Á)", "Núi Ngũ Hành Sơn (40k)", "Suối Hoa (cách 15km)"],
    ("đà nẵng", "vui chơi"):    ["Bà Nà Hills & Cầu Vàng (750k, cáp treo)", "Sun World Đà Nẵng Wonders", "Asia Park (260k)", "Golden Bridge (Cầu Vàng)"],
    ("đà nẵng", "ẩm thực"):     ["Bánh tráng cuốn thịt heo - đặc sản ĐN", "Bún mắm nêm", "Mì Quảng Ếch", "Hải sản tươi sống Mân Thái"],
    # ── Phú Quốc ──
    ("phú quốc", "biển"):       ["Bãi Sao (đẹp nhất đảo)", "Bãi Dài (hoang sơ)", "Hòn Thơm (cáp treo vượt biển dài nhất TG)", "Lặn ngắm san hô Rạch Vẹm"],
    ("phú quốc", "vui chơi"):   ["VinWonders Phú Quốc (750k)", "Safari Phú Quốc (600k)", "Bến Tàu Dương Đông (chợ đêm)"],
    ("phú quốc", "ẩm thực"):    ["Bún quậy - đặc sản đảo", "Gỏi cá trích", "Nhum biển nướng", "Chợ đêm Dương Đông"],
    # ── Sa Pa ──
    ("sa pa", "thiên nhiên"):   ["Đỉnh Fansipan (600k cáp treo hoặc leo bộ)", "Thung lũng Mường Hoa", "Rừng đỗ quyên Fansipan", "Hồ Tả Van"],
    ("sa pa", "văn hóa"):       ["Làng bản H'Mông Cát Cát (50k)", "Chợ phiên Sa Pa (thứ 7 - chủ nhật)", "Bản Lao Chải - Tả Van (trek 1 ngày)"],
    # ── Nha Trang ──
    ("nha trang", "biển"):      ["Bãi biển Trần Phú (dài 7km)", "Đảo Hòn Mun (lặn biển, san hô)", "Vịnh Nha Trang (tour 4 đảo 350k)", "Bãi Dài Cam Ranh"],
    ("nha trang", "vui chơi"):  ["VinWonders Nha Trang (700k)", "Tháp Bà Ponagar (thế kỷ 8)", "Suối nước nóng Trăm Trứng (135k)"],
    # ── Quốc tế ──
    ("bangkok", "vui chơi"):    ["Cung điện Hoàng gia Grand Palace", "Chùa Wat Pho (tượng Phật nằm)", "Khao San Road (phố tây)", "Chợ nổi Damnoen Saduak"],
    ("tokyo", "lịch sử"):       ["Đền Senso-ji Asakusa", "Cung điện Hoàng gia", "Shibuya Crossing", "Khu phố Yanaka cổ"],
    ("paris", "lịch sử"):       ["Tháp Eiffel (26€)", "Bảo tàng Louvre (22€)", "Cung điện Versailles (20€)", "Nhà thờ Đức Bà Notre-Dame"],
    ("bali", "thiên nhiên"):    ["Ruộng bậc thang Tegalalang", "Núi lửa Batur (trekking 04:00 sáng)", "Đền Uluwatu (100k IDR)", "Ubud Monkey Forest"],
    ("singapore", "vui chơi"):  ["Gardens by the Bay (32 SGD)", "Universal Studios (88 SGD)", "Marina Bay Sands SkyPark (26 SGD)", "Sentosa Island"],
}

# ─────────────────────────────────────────────────────────────────────────────
# TOOL FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def get_weather(city: str) -> str:
    """
    [TOOL: get_weather]

    MỤC ĐÍCH: Lấy thông tin thời tiết hiện tại của một thành phố / điểm đến.

    INPUT:
      - city (str): Tên thành phố hoặc điểm đến bằng tiếng Việt hoặc tiếng Anh.
        Ví dụ hợp lệ: "Hà Nội", "Da Nang", "Hội An", "Bangkok", "Tokyo", "Paris".
        Không cần accent cũng được (ví dụ "Ha Noi" hoặc "Hà Nội" đều nhận).

    OUTPUT (str): Chuỗi mô tả thời tiết gồm:
      - Nhiệt độ (°C)
      - Tình trạng thời tiết (nắng / mưa / nhiều mây / sương mù...)
      - Độ ẩm (%)
      - Hướng và tốc độ gió
      - Chỉ số UV (1-11, càng cao càng cần chống nắng)
      - Lời khuyên trang phục ngắn gọn

    KHI NÀO NÊN DÙNG:
      - Người dùng hỏi "Thời tiết ở X thế nào?"
      - Người dùng hỏi nên mặc gì / mang theo gì khi đi X
      - Cần xác nhận điều kiện thời tiết trước khi gợi ý hoạt động ngoài trời
      - Người dùng đang lên kế hoạch đi du lịch và cần biết thời tiết hiện tại

    KHÔNG NÊN DÙNG:
      - Khi câu hỏi chỉ liên quan đến văn hóa, lịch sử, ẩm thực (dùng search_attractions)
      - Khi không có tên địa danh cụ thể
    """
    city = city.strip().strip('"\'')

    # ── Bước 1: Geocoding → tọa độ ──────────────────────────────────────────
    try:
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_r   = requests.get(geo_url,
                               params={"name": city, "count": 1, "language": "vi", "format": "json"},
                               timeout=8)
        geo_r.raise_for_status()
        results = geo_r.json().get("results")
        if not results:
            return (f"Không tìm thấy địa điểm '{city}'. "
                    f"Thử lại với tên tiếng Anh hoặc kiểm tra chính tả.")

        loc      = results[0]
        lat      = loc["latitude"]
        lon      = loc["longitude"]
        loc_name = loc.get("name", city)
        country  = loc.get("country", "")
        tz       = loc.get("timezone", "auto")

    except requests.RequestException as e:
        return f"Lỗi kết nối Geocoding API: {e}. Kiểm tra kết nối mạng."

    # ── Bước 2: Thời tiết hiện tại ───────────────────────────────────────────
    try:
        wx_url  = "https://api.open-meteo.com/v1/forecast"
        wx_r    = requests.get(wx_url, params={
            "latitude":  lat,
            "longitude": lon,
            "current":   "temperature_2m,apparent_temperature,relative_humidity_2m,"
                         "wind_speed_10m,wind_direction_10m,uv_index,weather_code,precipitation",
            "wind_speed_unit": "kmh",
            "timezone":        tz,
        }, timeout=8)
        wx_r.raise_for_status()
        cur = wx_r.json().get("current", {})

    except requests.RequestException as e:
        return f"Lỗi kết nối Weather API: {e}. Kiểm tra kết nối mạng."

    # ── Bước 3: Format kết quả ───────────────────────────────────────────────
    temp        = round(cur.get("temperature_2m", 0), 1)
    feels_like  = round(cur.get("apparent_temperature", 0), 1)
    humidity    = cur.get("relative_humidity_2m", 0)
    wind_speed  = round(cur.get("wind_speed_10m", 0), 1)
    wind_dir    = _wind_dir(cur.get("wind_direction_10m", 0))
    uv          = round(cur.get("uv_index", 0), 1)
    wx_code     = cur.get("weather_code", 0)
    precip      = round(cur.get("precipitation", 0), 1)
    condition   = _WMO_CODE.get(wx_code, f"Mã thời tiết {wx_code}")

    uv_label = ("Thấp" if uv <= 2 else "Trung bình" if uv <= 5
                else "Cao" if uv <= 7 else "Rất cao" if uv <= 10 else "Cực cao")

    if temp >= 37:
        advice = "Nắng cực gắt! Hạn chế ra ngoài 11h-16h, bôi kem SPF50+, uống nhiều nước."
    elif temp >= 35:
        advice = "Rất nóng. Mặc đồ nhẹ thoáng, bôi kem chống nắng SPF50+, mang nước."
    elif temp >= 28:
        advice = "Nóng. Trang phục mỏng nhẹ, mang theo ô hoặc áo mưa mỏng."
    elif temp >= 20:
        advice = "Dễ chịu. Áo nhẹ kết hợp một lớp ngoài mỏng."
    elif temp >= 12:
        advice = "Mát. Áo khoác nhẹ hoặc áo len, quần dài."
    else:
        advice = "Lạnh. Áo khoác ấm, khăn quàng cổ, mũ len."

    precip_str = f" | Lượng mưa: {precip}mm" if precip > 0 else ""
    location_str = f"{loc_name}, {country}" if country else loc_name

    return (
        f"[Du lieu thoi gian thuc - Open-Meteo API]\n"
        f"Thoi tiet tai {location_str}: {temp}C (cam giac nhu {feels_like}C), {condition}.\n"
        f"Do am: {humidity}% | Gio: {wind_dir} {wind_speed}km/h | UV: {uv} ({uv_label}){precip_str}.\n"
        f"Goi y trang phuc: {advice}"
    )


def search_attractions(location: str, interest: str) -> str:
    """
    [TOOL: search_attractions]

    MỤC ĐÍCH: Tìm kiếm và gợi ý địa điểm tham quan, hoạt động tại một địa điểm
    dựa trên sở thích / nhu cầu cụ thể của người dùng.

    INPUT:
      - location (str): Tên thành phố / điểm đến.
        Ví dụ: "Hội An", "Đà Nẵng", "Phú Quốc", "Bangkok", "Bali".

      - interest (str): Loại sở thích hoặc nhu cầu. Các giá trị được hỗ trợ:
          * "lịch sử"    - Di tích, đền chùa, bảo tàng, kiến trúc cổ
          * "ẩm thực"    - Món ăn đặc sản, quán nổi tiếng, chợ ăn đêm
          * "thiên nhiên"- Núi, thác, rừng, công viên, cảnh đẹp ngoài trời
          * "biển"       - Bãi tắm, lặn biển, đảo, thể thao nước
          * "vui chơi"   - Theme park, giải trí, hoạt động gia đình, trẻ em
          * "mua sắm"    - Trung tâm thương mại, chợ, đặc sản mua về
          * "văn hóa"    - Lễ hội, làng nghề, phong tục địa phương

    OUTPUT (str): Danh sách 3-5 địa điểm kèm thông tin thực tiễn:
      - Tên địa điểm
      - Giờ mở cửa (nếu có)
      - Giá vé / chi phí tham khảo
      - Ghi chú ngắn về điểm nổi bật

    KHI NÀO NÊN DÙNG:
      - "Ở X có gì hay không?" / "Nên đi đâu ở X?"
      - "Tôi thích [sở thích], ở X nên đến đâu?"
      - Khi cần gợi ý itinerary chi tiết
      - Người dùng hỏi về ăn gì, chơi gì, mua gì ở một địa điểm

    KHÔNG NÊN DÙNG:
      - Khi chỉ hỏi về thời tiết (dùng get_weather)
      - Khi câu hỏi quá chung chung không có địa danh

    LƯU Ý: Nếu không tìm thấy kết hợp location+interest, tool sẽ trả về gợi ý
    các interest khả dụng cho địa điểm đó để Agent có thể thử lại.
    """
    loc_key = location.strip().lower()
    int_key = interest.strip().lower()

    # Tìm chính xác
    result = _ATTRACTIONS_DB.get((loc_key, int_key))

    if result:
        header = f"Địa điểm '{interest}' nổi bật tại {location.title()}:"
        items = "\n".join([f"  {i+1}. {item}" for i, item in enumerate(result)])
        return f"{header}\n{items}"

    # Tìm partial match (location có nhưng interest không có)
    available = [k[1] for k in _ATTRACTIONS_DB if k[0] == loc_key]
    if available:
        return (
            f"Không có dữ liệu '{interest}' cho {location.title()}. "
            f"Sở thích khả dụng tại đây: {', '.join(available)}. "
            f"Hãy thử lại với một trong các loại trên."
        )

    # Không có location
    supported_locs = sorted(set(k[0] for k in _ATTRACTIONS_DB))
    return (
        f"Không có dữ liệu cho '{location}'. "
        f"Địa điểm được hỗ trợ: {', '.join(supported_locs)}."
    )


def estimate_budget(destination: str, days: int, travel_style: str = "trung bình") -> str:
    """
    [TOOL: estimate_budget]

    MỤC ĐÍCH: Ước tính ngân sách chuyến đi dựa trên điểm đến, số ngày và
    phong cách du lịch.

    INPUT:
      - destination (str): Tên điểm đến (ví dụ: "Đà Nẵng", "Bangkok")
      - days (int): Số ngày lưu trú (1-30)
      - travel_style (str): Phong cách du lịch:
          * "tiết kiệm"  - Hostel, xe buýt, ăn local
          * "trung bình" - Khách sạn 3 sao, taxi, nhà hàng bình dân
          * "cao cấp"    - Resort 4-5 sao, xe riêng, nhà hàng sang

    OUTPUT (str): Bảng ước tính chi phí theo hạng mục (VNĐ/ngày và tổng).

    KHI NÀO NÊN DÙNG:
      - Người dùng hỏi "đi X mấy ngày tốn bao nhiêu?"
      - Cần lên ngân sách trước chuyến đi
      - So sánh chi phí giữa các điểm đến
    """
    budgets = {
        "tiết kiệm":  {"vn": (300_000, 500_000),   "intl": (800_000,  1_200_000)},
        "trung bình": {"vn": (800_000, 1_500_000),  "intl": (2_000_000, 3_500_000)},
        "cao cấp":    {"vn": (2_000_000, 5_000_000),"intl": (5_000_000, 12_000_000)},
    }

    intl_cities = {"bangkok", "tokyo", "paris", "singapore", "seoul",
                   "bali", "london", "new york", "sydney", "dubai", "rome"}

    dest_key = destination.strip().lower()
    is_intl = dest_key in intl_cities
    style_key = travel_style.strip().lower()
    budget_range = budgets.get(style_key, budgets["trung bình"])
    daily = budget_range["intl"] if is_intl else budget_range["vn"]

    total_low  = daily[0] * days
    total_high = daily[1] * days

    currency = "VNĐ" if not is_intl else "VNĐ (đã quy đổi)"
    category = "Quốc tế" if is_intl else "Trong nước"

    return (
        f"Ước tính ngân sách cho {days} ngày tại {destination.title()} "
        f"[{category} - {travel_style}]:\n"
        f"  • Chi phí/ngày: {daily[0]:,} - {daily[1]:,} {currency}\n"
        f"  • Tổng {days} ngày: {total_low:,} - {total_high:,} {currency}\n"
        f"  • Bao gồm: khách sạn, ăn uống, di chuyển nội địa, vé tham quan\n"
        f"  • Chưa bao gồm: vé máy bay, visa, mua sắm cá nhân"
    )


def get_current_datetime(location: str = "") -> str:
    """
    [TOOL: get_current_datetime]

    MUC DICH: Lay ngay gio hien tai chinh xac theo mui gio cua mot dia diem.
    Du lieu thoi gian thuc tu dong ho he thong ket hop voi mui gio chinh xac.

    INPUT:
      - location (str): Ten thanh pho / quoc gia de xac dinh mui gio.
        Vi du: "Ha Noi", "Tokyo", "Paris", "New York", "Sydney".
        Co the de trong ("") de lay gio Viet Nam mac dinh (Asia/Ho_Chi_Minh).

    OUTPUT (str): Thong tin ngay gio hien tai gom:
      - Ngay (dd/mm/yyyy) va thu trong tuan
      - Gio hien tai (HH:MM:SS)
      - Mui gio (vi du: Asia/Ho_Chi_Minh, UTC+7)

    KHI NAO NEN DUNG:
      - Nguoi dung hoi "Hom nay la ngay may?" / "Bay gio la may gio?"
      - Cau hoi co chua tu "hom nay", "bay gio", "ngay nay", "thang nay", "nam nay"
      - Can biet ngay/gio de tinh toan lich trinh hoac thoi han
      - LUON LUON dung tool nay khi co bat ky cau hoi nao lien quan den ngay thang nam
        hoac gio hien tai - KHONG DUOC TU DOAN hoac dung kien thuc tinh!

    KHONG NEN DUNG:
      - Khi chi hoi ve thoi tiet (dung get_weather)
      - Khi chi hoi ve dia diem tham quan (dung search_attractions)
    """
    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        import pytz as _pytz
        ZoneInfo = _pytz.timezone  # fallback

    location = location.strip().strip('"\'')

    # Lay timezone tu geocoding API
    tz_str = "Asia/Ho_Chi_Minh"  # mac dinh Viet Nam
    loc_display = location or "Viet Nam"

    if location:
        try:
            geo_r = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": location, "count": 1, "language": "vi", "format": "json"},
                timeout=6,
            )
            geo_r.raise_for_status()
            results = geo_r.json().get("results", [])
            if results:
                tz_str      = results[0].get("timezone", "Asia/Ho_Chi_Minh")
                loc_display = results[0].get("name", location)
                country     = results[0].get("country", "")
                if country:
                    loc_display = f"{loc_display}, {country}"
        except Exception:
            pass  # Fallback to Asia/Ho_Chi_Minh

    # Lay thoi gian hien tai theo mui gio
    try:
        tz  = ZoneInfo(tz_str)
        now = datetime.now(tz)
    except Exception:
        now = datetime.now()
        tz_str = "local"

    # Thu tieng Viet
    weekdays_vi = ["Thu Hai", "Thu Ba", "Thu Tu", "Thu Nam",
                   "Thu Sau", "Thu Bay", "Chu Nhat"]
    weekday_vi  = weekdays_vi[now.weekday()]

    months_vi = ["thang 1","thang 2","thang 3","thang 4","thang 5","thang 6",
                 "thang 7","thang 8","thang 9","thang 10","thang 11","thang 12"]
    month_vi  = months_vi[now.month - 1]

    utc_offset = now.strftime("%z")
    if len(utc_offset) == 5:
        utc_offset = f"UTC{utc_offset[:3]}:{utc_offset[3:]}"

    return (
        f"[Du lieu thoi gian thuc]\n"
        f"Dia diem: {loc_display}\n"
        f"Ngay    : {weekday_vi}, ngay {now.day:02d}/{now.month:02d}/{now.year} "
        f"({now.day} {month_vi} nam {now.year})\n"
        f"Gio     : {now.strftime('%H:%M:%S')}\n"
        f"Mui gio : {tz_str} ({utc_offset})"
    )


# ─────────────────────────────────────────────────────────────────────────────
# TOOL REGISTRY - dùng bởi agent.py
# ─────────────────────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "get_current_datetime",
        "description": get_current_datetime.__doc__,
        "func": lambda args: get_current_datetime(args),
        "signature": "get_current_datetime(location)",
    },
    {
        "name": "get_weather",
        "description": get_weather.__doc__,
        "func": lambda args: get_weather(args),
        "signature": "get_weather(city)",
    },
    {
        "name": "search_attractions",
        "description": search_attractions.__doc__,
        "func": lambda args: _parse_and_call_search(args),
        "signature": "search_attractions(location, interest)",
    },
    {
        "name": "estimate_budget",
        "description": estimate_budget.__doc__,
        "func": lambda args: _parse_and_call_budget(args),
        "signature": "estimate_budget(destination, days, travel_style)",
    },
]


def _parse_and_call_search(args: str) -> str:
    """Parse 'location, interest' string and call search_attractions."""
    parts = [p.strip().strip('"\'') for p in args.split(",")]
    if len(parts) >= 2:
        return search_attractions(parts[0], parts[1])
    return search_attractions(args.strip().strip('"\''), "lịch sử")


def _parse_and_call_budget(args: str) -> str:
    """Parse 'destination, days, style' string and call estimate_budget."""
    parts = [p.strip().strip('"\'') for p in args.split(",")]
    try:
        destination = parts[0] if len(parts) > 0 else "Hà Nội"
        days = int(parts[1]) if len(parts) > 1 else 3
        style = parts[2] if len(parts) > 2 else "trung bình"
        return estimate_budget(destination, days, style)
    except Exception as e:
        return f"Lỗi parse tham số budget: {e}. Format: 'destination, days, travel_style'"


if __name__ == "__main__":
    # Quick test
    print(get_weather("Hội An"))
    print()
    print(search_attractions("Hội An", "ẩm thực"))
    print()
    print(estimate_budget("Đà Nẵng", 4, "trung bình"))
