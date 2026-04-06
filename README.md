# Day 3 Lab — Chatbot vs ReAct Agent
## Use Case: Tư vấn Du lịch Thông minh 🌏
**Group 28** | VinAI Training Program

---

## Mục tiêu

So sánh hai kiến trúc AI:

| | Chatbot Baseline | ReAct Agent |
|---|---|---|
| **Cách hoạt động** | LLM trả lời trực tiếp | Thought → Action → Observation → lặp |
| **Công cụ** | Không có | `get_weather`, `get_current_datetime`, `search_attractions`, `estimate_budget` |
| **Dữ liệu** | Kiến thức tĩnh (training data) | API thời gian thực |
| **Phù hợp** | Câu hỏi kinh nghiệm, văn hóa | Câu hỏi cần dữ liệu thực tế, multi-step |

---



---

## Cài đặt

### 1. Clone và vào thư mục
```bash
git clone <repo-url>
cd Day3_group28
```

### 2. Cài Python packages
```bash
pip install -r requirements.txt
```

### 3. Tạo file `.env`
```bash
cp .env.example .env   # hoặc tạo thủ công
```

Điền API key vào `.env`:
```env
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=...

# Chọn provider: openai | google
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
```

> **Lưu ý:** `get_weather` và `get_current_datetime` dùng **Open-Meteo API** — miễn phí, **không cần thêm API key**.

---

## Chạy

### Web UI (khuyến nghị)
```bash
python app.py
```
Mở trình duyệt: **http://localhost:5000**

Giao diện gồm:
- Ô nhập câu hỏi ở trên
- **Panel trái**: ReAct Agent — hiển thị từng bước Thought / Action / Observation
- **Panel phải**: Chatbot Baseline — trả lời trực tiếp
- Footer mỗi panel: tokens, latency, model, số bước, tool calls

### Chạy 5 test cases tự động
```bash
python -X utf8 run_demo.py
```

Kết quả lưu tại `log/`:
- `log/queries_YYYY-MM-DD.jsonl` — mỗi câu hỏi 1 dòng JSON
- `log/session_YYYY-MM-DD_HHMMSS.json` — tổng kết session (tokens, latency, tool calls)

### Chạy từng hệ thống riêng
```bash
# Chỉ Agent
python -X utf8 run_demo.py agent-only

# Chỉ Chatbot
python -X utf8 run_demo.py chatbot-only

# Interactive Agent
python agent.py

# Interactive Chatbot
python chatbot.py
```

---

## Công cụ (Tools)

| Tool | API | Mô tả |
|------|-----|-------|
| `get_current_datetime(location)` | Open-Meteo Geocoding + `zoneinfo` | Ngày giờ thực tế theo múi giờ địa phương |
| `get_weather(city)` | Open-Meteo Weather API | Nhiệt độ, độ ẩm, UV, gió — dữ liệu thực tế |
| `search_attractions(location, interest)` | Database nội bộ | Địa điểm tham quan theo sở thích |
| `estimate_budget(destination, days, style)` | Database nội bộ | Ước tính chi phí chuyến đi |

---

## Cấu hình Agent

| Tham số | Giá trị | Ý nghĩa |
|---------|---------|---------|
| `MAX_ITERATIONS` | 5 | Tối đa 5 bước Thought/Action/Observation |
| `FALLBACK_THRESHOLD` | 3 | Sau 3 lần tool thất bại → chuyển sang kiến thức tĩnh |
| `TEMPERATURE` | 0.2 | Ít ngẫu nhiên, ổn định hơn |

---

## Log Format

Mỗi query được lưu với đầy đủ thông tin:

```json
{
  "timestamp": "2026-04-06T14:33:37Z",
  "source": "web",
  "question": "Thời tiết Hà Nội hôm nay?",
  "chatbot": {
    "answer": "...",
    "tokens": { "prompt": 120, "completion": 80, "total": 200 },
    "latency_ms": 1800,
    "model": "gpt-4o"
  },
  "agent": {
    "answer": "...",
    "iterations": 2,
    "tool_calls": [{ "tool": "get_current_datetime", "args": "Ha Noi" }, ...],
    "tokens": { "prompt": 400, "completion": 150, "total": 550 },
    "latency_ms": 4200,
    "llm_latency_ms": 3800,
    "llm_calls": 2,
    "fallback_used": false
  },
  "comparison": {
    "token_delta": 350,
    "token_ratio": 2.75,
    "latency_delta_ms": 2400,
    "agent_tool_calls": 2
  }
}
```

---

## 5 Test Cases

| ID | Câu hỏi | Ai thắng |
|----|---------|---------|
| TC-01 | Mẹo chống say tàu xe | Chatbot (kiến thức chung) |
| TC-02 | Phong tục khi đi Nhật | Chatbot (văn hóa ổn định) |
| TC-03 | Thời tiết Hội An tuần này | Agent (cần dữ liệu thực) |
| TC-04 | Kế hoạch 4 ngày Đà Nẵng + ngân sách | Agent (multi-step, 3 tools) |
| TC-05 | Thành phố Atlantis | Edge case (fallback) |

Chi tiết xem [`test_cases.md`](test_cases.md)

---

## Phân công nhóm

| Thành viên | Files phụ trách |
|-----------|----------------|
| **Người A** | `tools.py` |
| **Người B** | `chatbot.py` |
| **Người C** | `agent.py` |
| **Người D** | `app.py`, `templates/index.html`, `log_manager.py` |
| **Người E** | `run_demo.py`, `test_cases.md`, `trace.md`, `requirements.txt` |

---

## Yêu cầu hệ thống

- Python **3.9+** (cần `zoneinfo` stdlib)
- Kết nối internet (Open-Meteo API cho thời tiết và ngày giờ)
- OpenAI API key **hoặc** Google Gemini API key

---

## Tài liệu thêm

- [`test_cases.md`](test_cases.md) — 5 test cases chi tiết với Expected vs Actual
- [`trace.md`](trace.md) — Trace log mẫu giải thích từng bước Thought
- [`SCORING.md`](../Day-3-Lab-Chatbot-vs-react-agent/SCORING.md) — Rubric chấm điểm
