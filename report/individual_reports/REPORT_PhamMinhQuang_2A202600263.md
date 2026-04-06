# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Phạm Minh Quang
- **Student ID**: 2A20260263
- **Role in Group**: Web UI + Logging Developer
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

### Modules Implemented

| File | Vai trò |
| :--- | :--- |
| `app.py` | Flask server — 4 API endpoints, parallel execution |
| `templates/index.html` | Web UI — 2 panel so sánh, trace visualization |
| `log_manager.py` | Structured logging — JSONL query log + session summary |

### Code Highlights

**1. Parallel execution — Chatbot và Agent chạy đồng thời:**

```python
# app.py — /api/ask endpoint
def run_chatbot():
    chatbot_result.update(call_chatbot(question))

def run_agent():
    ag = TravelReActAgent(tools=_TOOLS)
    agent_result.update(ag.run_with_meta(question))

t1 = threading.Thread(target=run_chatbot)
t2 = threading.Thread(target=run_agent)
t1.start(); t2.start()
t1.join();  t2.join()
```

Chatbot hiển thị kết quả ngay khi xong (~2s), Agent tiếp tục xử lý (~6s) — UX mượt mà hơn so với chờ cả hai.

**2. Frontend trace rendering — phân màu từng loại block:**

```javascript
// index.html
// Thought  → màu xanh dương (#60a5fa)
// Action   → màu vàng (#f59e0b) + action pill hiển thị tool name
// Obs      → màu xanh lá (#34d399)
// Final    → màu tím (#a78bfa)

const stepEl = `
  <div class="trace-block block-thought">Thought: ${thought}</div>
  <div class="action-pill"><span class="tool-name">${tool}</span>(${args})</div>
  <div class="trace-block block-obs">Observation: ${obs}</div>
`;
```

**3. Structured logging với comparison metrics:**

```python
# log_manager.py
def _build_comparison(chatbot, agent):
    return {
        "token_delta":      agent_tokens - chatbot_tokens,
        "token_ratio":      agent_tokens / chatbot_tokens,
        "latency_delta_ms": agent_latency - chatbot_latency,
        "agent_tool_calls": len(agent["tool_calls"]),
    }
```

### Documentation

`app.py` là điểm kết nối toàn hệ thống: nhận câu hỏi từ web UI → phân phối cho `chatbot.py` và `agent.py` song song → tổng hợp kết quả → lưu log qua `log_manager.py` → trả JSON về frontend. `index.html` render trace thành visual steps có thể expand/collapse để dễ debug.

---

## II. Debugging Case Study (10 Points)

### Problem: Web UI bị lỗi encoding — tiếng Việt hiển thị thành ký tự lạ

**Mô tả:** Khi chạy trên Windows, Flask response chứa tiếng Việt bị encode sai — browser hiển thị `ThÃ¡ng` thay vì `Tháng`. Đặc biệt nặng ở phần Observation trong trace.

**Diagnosis:**

Python trên Windows mặc định dùng `cp932` (Japanese encoding) thay vì UTF-8. Flask trả response nhưng không set header `charset=utf-8` đúng cách, browser đọc sai encoding.

**Solution (3 bước):**

```python
# app.py — đảm bảo Flask response luôn UTF-8
app.config['JSON_AS_ASCII'] = False

# Thêm header vào mọi response
@app.after_request
def add_charset(response):
    if response.content_type.startswith('application/json'):
        response.content_type = 'application/json; charset=utf-8'
    return response
```

```html
<!-- index.html — khai báo charset -->
<meta charset="UTF-8">
```

Sau fix: toàn bộ tiếng Việt hiển thị đúng trên cả Chrome, Edge, Firefox.

**Bài học:** Web encoding là vấn đề cổ điển nhưng hay bị bỏ qua. Trên Windows, phải luôn explicit set UTF-8 — không được assume default.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

**1. Reasoning — Trace giúp tôi hiểu Agent "nghĩ" như thế nào:**

Khi implement UI hiển thị trace, tôi phải parse từng bước Thought/Action/Observation. Điều này buộc tôi đọc kỹ output của Agent — và tôi nhận ra Thought block thực sự thú vị: Agent không chỉ gọi tool mù quáng, nó giải thích lý do *tại sao* chọn tool đó. Chatbot hoàn toàn black-box — chỉ có input/output.

**2. Reliability — Latency là điểm yếu rõ nhất của Agent:**

Từ metrics dashboard, Agent TC-04 mất 10.6s — người dùng thực tế sẽ thấy lâu. Chatbot luôn dưới 5s. Với use case tư vấn du lịch, người dùng chấp nhận chờ 6-10s nếu câu trả lời rõ ràng chính xác hơn. Nhưng nếu câu trả lời tương đương, latency là yếu tố quyết định.

**3. Observation — Logging là "xương sống" để so sánh:**

Không có `log_manager.py`, việc so sánh Agent vs Chatbot sẽ chỉ là cảm quan. Nhờ có `comparison.token_ratio` và `comparison.latency_delta_ms` trong mỗi log entry, nhóm có thể đưa ra kết luận định lượng: Agent dùng nhiều hơn ~10x token nhưng đổi lại được dữ liệu thực tế.

---

## IV. Future Improvements (5 Points)

**Scalability:** Thêm streaming cho Agent trace — thay vì chờ Agent xong rồi render, dùng Server-Sent Events (SSE) để push từng bước Thought/Action/Observation ngay khi có. Latency cảm nhận giảm đáng kể dù tổng thời gian không đổi.

**Safety:** Thêm rate limiting trên `/api/ask` — tránh người dùng spam request gây tốn API cost. Giới hạn 10 requests/minute/IP.

**Performance:** Lưu log vào SQLite thay vì JSONL thuần — dễ query, filter, và vẽ biểu đồ latency/token trend theo thời gian. Tích hợp một dashboard đơn giản ngay trong web UI để xem lịch sử queries.
