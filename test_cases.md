# Test Cases - Chatbot vs ReAct Agent
## Use Case: Tư vấn Du lịch Thông minh | Group 28

---

## Phương pháp đánh giá

| Tiêu chí | Mô tả |
|----------|-------|
| **Accuracy** | Thông tin có chính xác không? |
| **Completeness** | Trả lời đầy đủ các phần của câu hỏi không? |
| **Grounding** | Có dựa trên dữ liệu thực tế (tool) hay chỉ đoán mò? |
| **Usefulness** | Người dùng có thể hành động ngay dựa trên câu trả lời không? |

---

## TC-01 | Chatbot thắng — Tư vấn kinh nghiệm chung

**Câu hỏi:** `"Tôi sợ bị say tàu/xe, có mẹo gì để đi du lịch dễ chịu hơn không?"`

**Loại:** Kiến thức tổng quát, không cần dữ liệu thực tế

### Expected

| Hệ thống | Kết quả kỳ vọng |
|----------|----------------|
| Chatbot  | ✅ Trả lời đầy đủ, thân thiện: các mẹo phòng say tàu xe (gừng, thuốc, chỗ ngồi...) |
| Agent    | Có thể lãng phí 1-2 bước thử gọi tool không cần thiết trước khi trả lời |

### Actual (điền sau khi chạy)

| Hệ thống | Kết quả thực tế | Điểm |
|----------|----------------|------|
| Chatbot  | | /10 |
| Agent    | | /10 |

### Phân tích
- **Chatbot thắng vì:** Câu hỏi thuần kiến thức — LLM đã được train đủ để trả lời mà không cần tool.
- **Agent bất lợi:** Có thể thử gọi tool không cần thiết, làm tăng latency.
- **Điểm rút ra:** ReAct Agent không phải lúc nào cũng tốt hơn. Với câu hỏi kiến thức tổng quát, chatbot đơn giản hơn và nhanh hơn.

---

## TC-02 | Chatbot thắng — Lời khuyên văn hóa

**Câu hỏi:** `"Lần đầu đi Nhật, tôi cần biết những phong tục, quy tắc lịch sự nào?"`

**Loại:** Kiến thức văn hóa, kinh nghiệm du lịch — LLM đã biết rõ

### Expected

| Hệ thống | Kết quả kỳ vọng |
|----------|----------------|
| Chatbot  | ✅ Liệt kê đầy đủ: cúi chào, bỏ giày, không bo tiền, xếp hàng, quy tắc trên tàu điện... |
| Agent    | Không có tool nào liên quan → có thể lãng phí bước hoặc trả lời không mượt |

### Actual (điền sau khi chạy)

| Hệ thống | Kết quả thực tế | Điểm |
|----------|----------------|------|
| Chatbot  | | /10 |
| Agent    | | /10 |

### Phân tích
- **Chatbot thắng vì:** Thông tin văn hóa là kiến thức tĩnh, ổn định — không cần cập nhật real-time.
- **Agent bất lợi:** System prompt agent hướng về tool-use, có thể làm Thought/Action dài dòng không cần thiết.

---

## TC-03 | Agent thắng — Thời tiết cụ thể

**Câu hỏi:** `"Tôi muốn đi Hội An tuần này. Thời tiết thế nào? Nên mặc gì?"`

**Loại:** Cần dữ liệu thực tế (thời tiết) → bắt buộc dùng tool

### Expected

| Hệ thống | Kết quả kỳ vọng |
|----------|----------------|
| Chatbot  | ❌ Không có dữ liệu thực tế → phải thừa nhận giới hạn hoặc đưa ra thông tin chung chung |
| Agent    | ✅ Gọi `get_weather("Hội An")` → nhận 30°C, nắng đẹp → tư vấn trang phục cụ thể |

### Expected Agent Trace
```
Thought: Người dùng hỏi thời tiết Hội An. Tôi cần dữ liệu thực tế → dùng get_weather.
Action: get_weather(Hội An)
Observation: Thời tiết tại Hội An: 30°C, Nắng đẹp. Độ ẩm: 72% | Gió: SE 10km/h | UV: 7 (Cao)...
Thought: Đã có đủ thông tin. Trả lời về thời tiết và tư vấn trang phục.
Final Answer: Thời tiết Hội An hiện tại 30°C, nắng đẹp...
```

### Actual (điền sau khi chạy)

| Hệ thống | Kết quả thực tế | Accuracy | Usefulness |
|----------|----------------|----------|-----------|
| Chatbot  | | /5 | /5 |
| Agent    | | /5 | /5 |

### Phân tích
- **Agent thắng vì:** Có dữ liệu thực tế từ tool, trả lời chính xác và có thể hành động ngay.
- **Chatbot thua vì:** Phải nói "tôi không biết thời tiết thực tế" hoặc đưa ra dự đoán có thể sai.

---

## TC-04 | Agent thắng — Multi-step: Kết hợp nhiều tool

**Câu hỏi:** `"Tôi muốn đi Đà Nẵng 4 ngày để tắm biển và chơi vui. Thời tiết ra sao và nên đi đâu? Ước tính chi phí cho 2 người đi kiểu bình dân?"`

**Loại:** Multi-step, cần 3 tool calls: thời tiết + địa điểm + ngân sách

### Expected Agent Trace
```
Thought: Câu hỏi phức tạp, cần: (1) thời tiết ĐN, (2) địa điểm biển/vui chơi, (3) ngân sách.
Action: get_weather(Đà Nẵng)
Observation: 31°C, Nắng đẹp...
Thought: Thời tiết OK. Giờ tìm địa điểm biển.
Action: search_attractions(Đà Nẵng, biển)
Observation: [Không có key (đà nẵng, biển) → trả về gợi ý] → thử thiên nhiên
Action: search_attractions(Đà Nẵng, vui chơi)
Observation: Bà Nà Hills, Sun World...
Action: estimate_budget(Đà Nẵng, 4, trung bình)
Observation: 800k-1.5M/ngày...
Final Answer: Tổng hợp đầy đủ 3 phần...
```

### Expected

| Hệ thống | Kết quả kỳ vọng |
|----------|----------------|
| Chatbot  | ❌ Thông tin chung chung, không có số liệu cụ thể, không ước tính ngân sách chính xác |
| Agent    | ✅ Thông tin cụ thể từ 3 tool calls, tổng hợp mạch lạc |

### Actual (điền sau khi chạy)

| Hệ thống | Accuracy | Completeness | Steps dùng | Kết quả |
|----------|----------|-------------|-----------|---------|
| Chatbot  | /5 | /5 | N/A | |
| Agent    | /5 | /5 | | |

### Phân tích
- **Agent thắng rõ ràng:** Câu hỏi đòi hỏi nhiều loại thông tin khác nhau. Agent chain tool calls một cách logic.
- **Chatbot thua:** Không thể cung cấp tất cả thông tin chính xác trong một lần.

---

## TC-05 | Edge Case — Địa điểm không tồn tại / Yêu cầu vô lý

**Câu hỏi:** `"Tôi muốn đi thăm thành phố Atlantis huyền thoại. Thời tiết thế nào và có gì vui chơi không?"`

**Loại:** Edge case — địa danh không tồn tại thực tế

### Expected

| Hệ thống | Kết quả kỳ vọng |
|----------|----------------|
| Chatbot  | Trả lời về Atlantis theo nghĩa thần thoại / giải thích đây là thành phố huyền thoại |
| Agent    | Tool trả về lỗi "không tìm thấy" → sau 3 lần thất bại → kích hoạt FALLBACK → thông báo rõ |

### Expected Agent Trace
```
Thought: Atlantis - cần kiểm tra thời tiết.
Action: get_weather(Atlantis)
Observation: Không tìm thấy dữ liệu thời tiết cho 'Atlantis'...
Thought: Thất bại lần 1. Thử search_attractions.
Action: search_attractions(Atlantis, vui chơi)
Observation: Không có dữ liệu cho 'Atlantis'...
[failed_attempts = 2]
Thought: Thất bại lần 2. Thử tên khác.
Action: get_weather(thành phố Atlantis)
Observation: Không tìm thấy...
[failed_attempts = 3 → FALLBACK kích hoạt]
⚠️ FALLBACK MODE
Final Answer: ⚠️ [Chế độ dự phòng] Atlantis là thành phố huyền thoại trong thần thoại Hy Lạp...
```

### Actual (điền sau khi chạy)

| Hệ thống | Xử lý lỗi | Thông báo rõ ràng? | Kết quả cuối |
|----------|-----------|-------------------|-------------|
| Chatbot  | | | |
| Agent    | | | |

### Phân tích
- **Điểm thú vị:** Agent không chỉ thất bại — nó thất bại một cách có kiểm soát và thông báo rõ.
- **Chatbot** có thể trả lời về Atlantis theo thần thoại ngay mà không cần vòng lặp.
- **Điểm rút ra:** Fallback mechanism quan trọng để agent không bị kẹt. Đây là minh chứng tốt cho Code Quality.

---

## Bảng Tổng Kết

| Test Case | Câu hỏi tóm tắt | Người thắng | Lý do chính |
|-----------|----------------|------------|-------------|
| TC-01 | Mẹo chống say tàu xe | Chatbot | Kiến thức tĩnh, không cần tool |
| TC-02 | Phong tục Nhật Bản | Chatbot | Văn hóa ổn định, LLM biết rõ |
| TC-03 | Thời tiết Hội An | Agent | Cần dữ liệu real-time |
| TC-04 | Kế hoạch 4 ngày Đà Nẵng | Agent | Multi-step, cần 3 tool calls |
| TC-05 | Atlantis huyền thoại | N/A (Edge) | Fallback mechanism test |

### Kết luận

**ReAct Agent vượt trội khi:**
- Câu hỏi cần dữ liệu thời gian thực (thời tiết, giá cả)
- Câu hỏi multi-step đòi hỏi kết hợp nhiều nguồn thông tin
- Cần độ chính xác cao, có thể kiểm chứng

**Chatbot Baseline vượt trội khi:**
- Câu hỏi kiến thức tổng quát, kinh nghiệm, tư vấn chung
- Không cần số liệu cụ thể
- Cần tốc độ phản hồi nhanh (không có overhead của tool calls)
