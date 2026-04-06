# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: Group 28
- **Team Members**: Trương Gia Ngọc (Tools), Nguyễn Trọng Tín (Chatbot), Đào Văn Sơn (Agent), Phạm Minh Quang (Web UI), Đinh Công Tài(QA)
- **Use Case**: Tư vấn Du lịch Thông minh
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

Nhóm xây dựng hệ thống **TravelAgent** so sánh hai kiến trúc AI cho bài toán tư vấn du lịch:
- **Chatbot Baseline**: GPT-4o trả lời trực tiếp từ kiến thức tĩnh, không có công cụ
- **ReAct Agent**: GPT-4o + 4 tools thời gian thực, vòng lặp Thought → Action → Observation

Kết quả trên 5 test cases:

- **Agent Success Rate**: 3/5 tasks rõ ràng vượt trội (thời tiết, multi-step planning, edge case)
- **Chatbot Success Rate**: 2/5 tasks phù hợp hơn (kiến thức chung, văn hóa)
- **Key Outcome**: Agent giải quyết được 100% câu hỏi cần dữ liệu thực tế (thời tiết, ngày giờ, ngân sách), trong khi Chatbot chỉ đoán mò hoặc từ chối trả lời.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

```
User Input
    │
    ▼
[Thought] ─ LLM phân tích câu hỏi, quyết định dùng tool nào
    │
    ▼
[Action] ─ Gọi tool: get_weather(city) / get_current_datetime(loc) / ...
    │
    ▼
[Observation] ─ Nhận kết quả thực tế từ API
    │
    ├─► Chưa đủ thông tin? → Quay lại Thought (tối đa 5 vòng)
    │
    └─► Đủ thông tin? → Final Answer
                              │
              Tool thất bại ≥ 3 lần → FALLBACK (kiến thức tĩnh + cảnh báo)
```

**Tham số điều khiển:**
- `MAX_ITERATIONS = 5` — giới hạn vòng lặp, tránh chi phí vô tận
- `FALLBACK_THRESHOLD = 3` — chuyển sang kiến thức tĩnh sau 3 lần tool thất bại
- `TEMPERATURE = 0.2` — giảm ngẫu nhiên, tăng độ ổn định khi parse output

### 2.2 Tool Definitions

| Tool Name | Input Format | Nguồn dữ liệu | Use Case |
| :--- | :--- | :--- | :--- |
| `get_current_datetime` | `location: str` | Open-Meteo Geocoding + `zoneinfo` | Ngày giờ thực tế theo múi giờ địa phương |
| `get_weather` | `city: str` | Open-Meteo Weather API | Nhiệt độ, độ ẩm, UV, gió — dữ liệu thực |
| `search_attractions` | `location, interest: str` | Database nội bộ | Địa điểm tham quan theo sở thích |
| `estimate_budget` | `destination, days, style: str` | Database nội bộ | Ước tính chi phí chuyến đi |

**Lý do dùng Open-Meteo:** Miễn phí, không cần API key thêm, độ chính xác cao, hỗ trợ toàn cầu.

### 2.3 LLM Providers Used

- **Primary**: GPT-4o (OpenAI) — độ chính xác cao, tuân thủ format tốt
- **Secondary (Backup)**: Gemini 1.5 Flash (Google) — nhanh hơn, chi phí thấp hơn

---

## 3. Telemetry & Performance Dashboard

Dữ liệu từ session log `log/session_2026-04-06_*.json` — 5 test cases:

### Agent

| Metric | Giá trị |
| :--- | :--- |
| Average Latency (P50) | ~6,200ms |
| Max Latency (P99 — TC-04 multi-step) | ~10,600ms |
| Average Tokens per Task | ~3,807 tokens |
| Total Tokens (5 test cases) | 19,037 tokens |
| Total Tool Calls | 5 calls |
| Fallback Activated | 0 lần |
| LLM Calls Total | ~12 calls |

### Chatbot

| Metric | Giá trị |
| :--- | :--- |
| Average Latency (P50) | ~3,000ms |
| Average Tokens per Task | ~350 tokens |
| Tool Calls | 0 |

### So sánh

| | Chatbot | Agent | Nhận xét |
| :--- | :--- | :--- | :--- |
| Token/task | ~350 | ~3,807 | Agent dùng nhiều hơn ~10x do multi-turn |
| Latency/task | ~3,000ms | ~6,200ms | Agent chậm hơn ~2x do tool I/O |
| Accuracy (real-time) | ❌ Không có | ✅ Chính xác | Agent vượt trội hoàn toàn |
| Accuracy (general) | ✅ Tốt | ✅ Tốt | Tương đương |

---

## 4. Root Cause Analysis (RCA) — Failure Traces

### Case Study 1: Hallucinated Observation (TC-01)

- **Input**: "15% of 240 là bao nhiêu?"
- **Quan sát**: Agent gọi `calculator(240 * 0.15)` nhưng GPT-4o tự điền `Observation: 36.0` mà **không thực sự gọi tool**. Kết quả đúng nhưng tool không được thực thi.
- **Root Cause**: Model đủ tự tin để trả lời toán đơn giản → tự sinh cả Observation trong cùng 1 lần generate thay vì dừng lại chờ hệ thống điền.
- **Solution**: Thêm `stop=["Observation:"]` trong OpenAI API call — buộc model dừng trước Observation để hệ thống điền giá trị thực.

### Case Study 2: Sai ngày tháng (phát hiện trong demo)

- **Input**: "Hôm nay là ngày bao nhiêu?"
- **Quan sát**: Agent trả lời "24 tháng 10 năm 2023" — sai hoàn toàn so với thực tế 06/04/2026.
- **Root Cause**: Không có tool `get_current_datetime` → LLM dùng kiến thức tĩnh từ training data (cutoff 2023).
- **Solution**: Thêm tool `get_current_datetime(location)` dùng Open-Meteo API lấy timezone + `zoneinfo` tính giờ thực. Thêm rule bắt buộc vào system prompt: *"TUYET DOI KHONG tu doan ngay thang nam"*.

---

## 5. Ablation Studies & Experiments

### Experiment 1: System Prompt v1 vs v2

| | Prompt v1 | Prompt v2 |
| :--- | :--- | :--- |
| **Thay đổi** | Không có rule ngày/giờ | Thêm "PHAI goi get_current_datetime() khi hoi ngay/gio" |
| **Kết quả** | Hallucinate ngày 2023 | Gọi đúng tool, ngày chính xác |
| **Cải thiện** | — | Sửa 100% lỗi ngày/giờ |

### Experiment 2: Chatbot vs Agent — 5 Test Cases

| Test Case | Câu hỏi | Chatbot | Agent | Winner |
| :--- | :--- | :--- | :--- | :--- |
| TC-01 | Mẹo chống say xe | ✅ Đầy đủ | ✅ Đầy đủ | **Chatbot** (nhanh hơn) |
| TC-02 | Phong tục Nhật Bản | ✅ Chi tiết | ✅ Chi tiết | **Chatbot** (nhanh hơn) |
| TC-03 | Thời tiết Hội An | ❌ "Không biết thực tế" | ✅ 30°C, nắng đẹp (từ API) | **Agent** |
| TC-04 | 4 ngày Đà Nẵng + ngân sách | ⚠️ Chung chung | ✅ 31°C + địa điểm + 8-15M VNĐ | **Agent** |
| TC-05 | Atlantis huyền thoại | ✅ Giải thích hợp lý | ✅ Trả lời ngay, không gọi tool | **Draw** |

### Experiment 3: Tool Description Detail Level

Khi `search_attractions` có docstring ngắn → Agent thường chọn sai interest keyword.
Sau khi viết docstring chi tiết với danh sách interest khả dụng → Agent chọn đúng 100%.

---

## 6. Production Readiness Review

- **Security**: Sanitize tham số trước khi truyền vào tool (strip quotes, kiểm tra ký tự đặc biệt). Không expose API key trong log.
- **Guardrails**: `MAX_ITERATIONS = 5` ngăn vòng lặp vô tận. `FALLBACK_THRESHOLD = 3` đảm bảo luôn có câu trả lời. Tool timeout 8 giây tránh treo.
- **Cost Control**: Agent dùng ~10x token hơn Chatbot. Trong production, nên route câu hỏi đơn giản sang Chatbot, phức tạp mới dùng Agent.
- **Scaling**: Có thể thêm tool mới vào `TOOLS` list mà không cần sửa Agent. Chuyển sang async tool calls để giảm latency multi-step.
- **Monitoring**: Mọi query được log vào `log/queries_YYYY-MM-DD.jsonl` với đầy đủ tokens, latency, trace — sẵn sàng tích hợp Grafana/DataDog.
