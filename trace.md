# Agent Trace Log - Mẫu Câu Hỏi Khó
## Group 28 | Use Case: Tư vấn Du lịch Thông minh

---

## Câu hỏi được trace

> **"Tôi có 5 ngày nghỉ, muốn đi du lịch biển nhưng không muốn quá nóng. Hiện tại Đà Nẵng và Phú Quốc thời tiết thế nào? Ở đâu phù hợp hơn? Nếu chọn Phú Quốc thì có gì để chơi không? Ước tính chi phí đi 2 người kiểu trung bình?"`**

**Tại sao chọn câu hỏi này?**
- Multi-step: 4 yêu cầu khác nhau trong 1 câu
- So sánh 2 địa điểm → cần gọi tool 2 lần
- Cần ra quyết định dựa trên kết quả tool
- Cần tính ngân sách dựa trên điểm đến được chọn

---

## Full Trace Log

```
════════════════════════════════════════════════════════
[INPUT]  "Tôi có 5 ngày nghỉ, muốn đi du lịch biển nhưng không
         muốn quá nóng. Hiện tại Đà Nẵng và Phú Quốc thời tiết
         thế nào? Ở đâu phù hợp hơn? Nếu chọn Phú Quốc thì có
         gì để chơi không? Ước tính chi phí đi 2 người kiểu
         trung bình?"
════════════════════════════════════════════════════════

──────────────────────────────────────────────────────
[Bước 1 / MAX_ITERATIONS=5]
──────────────────────────────────────────────────────

Thought: Người dùng muốn so sánh thời tiết Đà Nẵng và Phú Quốc
         để chọn điểm đi. Ưu tiên: không quá nóng. Tôi cần lấy
         thời tiết của cả 2 nơi. Bắt đầu với Đà Nẵng.

Action: get_weather(Đà Nẵng)

→ Gọi tool: get_weather(Đà Nẵng)
← Observation: Thời tiết tại Đà Nẵng: 31°C, Nắng đẹp. Độ ẩm:
   70% | Gió: SE 12km/h | UV: 8 (Rất cao). Gợi ý trang phục:
   Trang phục mỏng nhẹ, mang theo ô hoặc áo mưa mỏng.

──────────────────────────────────────────────────────
[Bước 2 / MAX_ITERATIONS=5]
──────────────────────────────────────────────────────

Thought: Đà Nẵng 31°C, nắng đẹp - khá nóng nhưng chấp nhận được.
         Bây giờ cần so sánh với Phú Quốc. Gọi get_weather tiếp.

Action: get_weather(Phú Quốc)

→ Gọi tool: get_weather(Phú Quốc)
← Observation: Thời tiết tại Phú Quốc: 32°C, Nắng, ít mây. Độ
   ẩm: 60% | Gió: SW 6km/h | UV: 8 (Rất cao). Gợi ý trang phục:
   Trang phục mỏng nhẹ, mang theo ô hoặc áo mưa mỏng.

──────────────────────────────────────────────────────
[Bước 3 / MAX_ITERATIONS=5]
──────────────────────────────────────────────────────

Thought: So sánh:
         - Đà Nẵng: 31°C, nắng đẹp, độ ẩm 70% (hơi ẩm)
         - Phú Quốc: 32°C, nắng ít mây, độ ẩm 60% (khô hơn, dễ
           chịu hơn dù nhỉnh hơn 1°C)
         Người dùng không muốn "quá nóng" → cả 2 đều nóng nhưng
         Phú Quốc khô hơn nên cảm giác dễ chịu hơn.
         Người dùng hỏi Phú Quốc có gì chơi → cần search_attractions.
         Sở thích: "biển" → thử interest="biển".

Action: search_attractions(Phú Quốc, biển)

→ Gọi tool: search_attractions(Phú Quốc, biển)
← Observation: Địa điểm 'biển' nổi bật tại Phú Quốc:
   1. Bãi Sao (đẹp nhất đảo)
   2. Bãi Dài (hoang sơ)
   3. Hòn Thơm (cáp treo vượt biển dài nhất TG)
   4. Lặn ngắm san hô Rạch Vẹm

──────────────────────────────────────────────────────
[Bước 4 / MAX_ITERATIONS=5]
──────────────────────────────────────────────────────

Thought: Có địa điểm biển rồi. Người dùng hỏi "có gì để chơi"
         → nên bổ sung thêm "vui chơi" để có nhiều lựa chọn hơn.

Action: search_attractions(Phú Quốc, vui chơi)

→ Gọi tool: search_attractions(Phú Quốc, vui chơi)
← Observation: Địa điểm 'vui chơi' nổi bật tại Phú Quốc:
   1. VinWonders Phú Quốc (750k)
   2. Safari Phú Quốc (600k)
   3. Bến Tàu Dương Đông (chợ đêm)

──────────────────────────────────────────────────────
[Bước 5 / MAX_ITERATIONS=5]
──────────────────────────────────────────────────────

Thought: Đã có thời tiết 2 nơi, địa điểm Phú Quốc. Còn thiếu
         ước tính chi phí. Dùng estimate_budget: 2 người x 5 ngày,
         kiểu trung bình. (Lưu ý: tool tính per person → nhân 2).

Action: estimate_budget(Phú Quốc, 5, trung bình)

→ Gọi tool: estimate_budget(Phú Quốc, 5, trung bình)
← Observation: Ước tính ngân sách cho 5 ngày tại Phú Quốc
   [Trong nước - trung bình]:
   • Chi phí/ngày: 800,000 - 1,500,000 VNĐ
   • Tổng 5 ngày: 4,000,000 - 7,500,000 VNĐ
   • Bao gồm: khách sạn, ăn uống, di chuyển nội địa, vé tham quan
   • Chưa bao gồm: vé máy bay, visa, mua sắm cá nhân

════════════════════════════════════════════════════════
Final Answer (bước 5):

🏝️ So sánh thời tiết hiện tại:
• Đà Nẵng: 31°C, nắng đẹp, độ ẩm 70%
• Phú Quốc: 32°C, nắng nhẹ, độ ẩm 60%

👉 Gợi ý: Phú Quốc phù hợp hơn — dù nóng hơn 1°C nhưng độ ẩm
   thấp hơn đáng kể (60% vs 70%), cảm giác dễ chịu và thoáng hơn
   khi đi biển.

🌊 Địa điểm nên đến tại Phú Quốc (5 ngày):
• Biển Bãi Sao (đẹp nhất đảo)
• Bãi Dài (hoang sơ, yên tĩnh)
• Hòn Thơm – Cáp treo vượt biển dài nhất thế giới
• Lặn ngắm san hô Rạch Vẹm
• VinWonders Phú Quốc (750k/người)
• Safari Phú Quốc (600k/người)
• Chợ đêm Dương Đông

💰 Ước tính chi phí 2 người (5 ngày, kiểu trung bình):
• Mỗi người: 4,000,000 – 7,500,000 VNĐ
• Cả 2 người: 8,000,000 – 15,000,000 VNĐ
• Chưa bao gồm: vé máy bay (thêm ~2-4 triệu/người từ HN/HCM)

💡 Mẹo: Đặt phòng trước ít nhất 2 tuần và mua vé máy bay sớm
   để được giá tốt nhất!
════════════════════════════════════════════════════════
```

---

## Phân tích từng bước Thought (Justified)

| Bước | Thought | Lý do / Justification |
|------|---------|----------------------|
| **1** | Cần lấy thời tiết Đà Nẵng trước | Câu hỏi yêu cầu so sánh 2 địa điểm → phải lấy đủ cả 2 trước khi kết luận. Bắt đầu theo thứ tự câu hỏi. |
| **2** | Lấy thời tiết Phú Quốc | Không thể so sánh với chỉ 1 điểm. Cần cả 2 để đưa ra khuyến nghị. |
| **3** | Phân tích: Phú Quốc phù hợp hơn (độ ẩm thấp hơn) | Agent không chỉ relay data mà phân tích thêm. 32°C với 60% ẩm dễ chịu hơn 31°C với 70% ẩm. Quyết định dựa trên yêu cầu "không quá nóng". |
| **4** | Bổ sung thêm category "vui chơi" | Người dùng hỏi "có gì để chơi" — biển là một phần nhưng cần thêm activities khác để câu trả lời đầy đủ. |
| **5** | Tính ngân sách cho 1 người, sẽ nhân 2 | Câu hỏi nói "2 người" nhưng tool tính per-person. Agent nhận thức được cần điều chỉnh khi trình bày. |

---

## Số liệu đo lường

| Metric | Giá trị |
|--------|---------|
| Tổng số bước (iterations) | 5 / 5 (max) |
| Tool calls thành công | 5 / 5 (100%) |
| Tool calls thất bại | 0 |
| Fallback kích hoạt | Không |
| Tổng tokens (ước tính) | ~1,800 tokens |
| Thời gian phản hồi (ước tính) | ~8-12 giây |
| Câu hỏi được trả lời đầy đủ | ✅ Có (4/4 phần) |

---

## So sánh với Chatbot Baseline

| Phần câu hỏi | Chatbot | Agent |
|-------------|---------|-------|
| Thời tiết Đà Nẵng thực tế | ❌ Chỉ ước đoán theo mùa | ✅ 31°C chính xác |
| Thời tiết Phú Quốc thực tế | ❌ Chỉ ước đoán | ✅ 32°C chính xác |
| So sánh → Đề xuất chọn nơi nào | ⚠️ Có nhưng không dựa trên data | ✅ Dựa trên data thực tế |
| Địa điểm tham quan Phú Quốc | ✅ Biết nhưng có thể thiếu | ✅ Đầy đủ từ database |
| Ước tính chi phí | ⚠️ Rất chung chung | ✅ Có dải cụ thể |

---

## Flowchart Mô tả (dùng để vẽ sơ đồ)

```
[START]
   │
   ▼
[Nhận câu hỏi của người dùng]
   │
   ▼
[Phân tích: Cần bao nhiêu loại thông tin?]
   │
   ├─► [Thông tin thời tiết?] ──► get_weather(city)
   │                                    │
   │                               [Observation]
   │                                    │
   ├─► [Địa điểm tham quan?] ──► search_attractions(loc, interest)
   │                                    │
   │                               [Observation]
   │                                    │
   ├─► [Ngân sách?] ──────────► estimate_budget(dest, days, style)
   │                                    │
   │                               [Observation]
   │
   ▼
[Có đủ thông tin để trả lời?]
   │
   ├─► [Có] ──► Final Answer ──► [END]
   │
   ├─► [Chưa, cần thêm] ──► [Tiếp tục vòng lặp, iteration + 1]
   │                              │
   │                    [iterations < MAX_ITERATIONS?]
   │                              │
   │                    ├─► [Có] ──► Quay lại Thought
   │                    │
   │                    └─► [Không] ──► Buộc Final Answer với thông tin hiện có
   │
   └─► [Tool thất bại liên tiếp ≥ 3 lần]
              │
              ▼
        [FALLBACK MODE]
              │
        [Trả lời bằng kiến thức tĩnh + ⚠️ thông báo]
              │
              ▼
            [END]
```

**Các node quan trọng:**
1. **Thought** — LLM suy nghĩ, quyết định tool nào cần gọi tiếp theo
2. **Action** — Gọi tool với tham số
3. **Observation** — Kết quả thực tế từ tool
4. **Điều kiện dừng** — Final Answer tìm thấy OR MAX_ITERATIONS OR FALLBACK
5. **Fallback** — Kích hoạt khi failed_attempts ≥ FALLBACK_THRESHOLD (3)
