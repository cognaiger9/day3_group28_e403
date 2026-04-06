# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Trọng Tín
- **Student ID**: 2A202600229
- **Role in Group**: Chatbot Baseline Developer
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

### Modules Implemented

| File | Vai trò |
| :--- | :--- |
| `chatbot.py` | Toàn bộ — system prompt, LLM caller, token tracking, interactive mode |

### Code Highlights

**1. System Prompt — vai trò tư vấn viên với giới hạn rõ ràng:**

```python
SYSTEM_PROMPT = """Bạn là TravelBot - chuyên gia tư vấn du lịch với 10 năm kinh nghiệm.

GIỚI HẠN QUAN TRỌNG:
- Bạn KHÔNG có quyền truy cập thông tin thời tiết thực tế.
- Bạn KHÔNG có quyền tra cứu giá vé, lịch bay thời gian thực.
- Khi được hỏi thông tin thời gian thực, hãy nói rõ giới hạn này
  và gợi ý người dùng kiểm tra qua Weather.com, Booking.com...
"""
```

**2. `call_chatbot()` — trả về metadata đầy đủ để so sánh với Agent:**

```python
def call_chatbot(question: str) -> Dict[str, Any]:
    # Returns: answer, tokens {prompt, completion, total}, latency_ms, model, provider
    t0 = time.time()
    response = client.chat.completions.create(model=model, messages=[...])
    return {
        "answer":    response.choices[0].message.content,
        "tokens":    {"prompt": usage.prompt_tokens, ...},
        "latency_ms": int((time.time() - t0) * 1000),
    }
```

**3. Hỗ trợ cả OpenAI và Gemini qua cùng interface:**

```python
def call_chatbot(question):
    provider = os.getenv("DEFAULT_PROVIDER", "openai")
    if provider == "openai":
        return _call_openai(question, timestamp)
    elif provider == "google":
        return _call_gemini(question, timestamp)
```

### Documentation

`chatbot.py` đóng vai trò **baseline** — điểm chuẩn để đo cải thiện của Agent. Mọi metric (tokens, latency) được format đồng nhất với `agent.py` để `log_manager.py` có thể so sánh trực tiếp qua field `comparison.token_delta` và `comparison.latency_delta_ms`.

---

## II. Debugging Case Study (10 Points)

### Problem: System prompt quá ngắn — Chatbot trả lời sai phong cách

**Mô tả:** Phiên bản đầu system prompt chỉ có 2 dòng: *"Bạn là chuyên gia du lịch. Hãy tư vấn cho người dùng."* Kết quả: Chatbot trả lời về thời tiết Hà Nội bằng cách bịa ra số liệu cụ thể thay vì thừa nhận giới hạn. Điều này tệ hơn cả không trả lời.

**Log thực tế (prompt v1):**

```
Q: Thời tiết Hà Nội tuần này thế nào?
A: Tuần này Hà Nội có nhiệt độ khoảng 25-30°C, ít mưa, thích hợp...
   [hoàn toàn là hallucination, không có nguồn dữ liệu]
```

**Diagnosis:**

Không có câu lệnh rõ ràng về giới hạn → LLM mặc định tự tin trả lời mọi thứ. GPT-4o được train để hữu ích, nên khi không được nhắc "tôi không biết", nó sẽ đoán.

**Solution:**

Thêm section `GIỚI HẠN QUAN TRỌNG` vào system prompt với các bullet point cụ thể. Sau fix, Chatbot trả lời: *"Tôi không thể cung cấp thông tin thời tiết thực tế. Bạn nên kiểm tra Weather.com hoặc Google Weather."* — trung thực và hữu ích hơn.

**Bài học:** System prompt phải định nghĩa không chỉ **vai trò** mà còn **giới hạn** của LLM. Một chatbot biết mình không biết gì còn tốt hơn một chatbot bịa ra câu trả lời.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

**1. Reasoning — Chatbot không có bước "nghĩ":**

Chatbot trả lời trong một shot — không có cơ chế decompose câu hỏi phức tạp. Với TC-04 (4 ngày Đà Nẵng + ngân sách), Chatbot đưa ra câu trả lời chung chung vì không thể thực hiện 3 bước tra cứu độc lập. Agent lại tự hỏi: *"Tôi cần thứ gì? → thời tiết, địa điểm, ngân sách → gọi 3 tool"* rồi tổng hợp.

**2. Reliability — Chatbot ổn định hơn với câu hỏi văn hóa:**

TC-01 (mẹo chống say xe), TC-02 (phong tục Nhật): Chatbot trả lời nhanh, đầy đủ, không cần tool. Agent cũng đúng nhưng mất thêm 3-4 giây và gần 3,000 token để... ra cùng kết quả. Với use case này, Chatbot rõ ràng hiệu quả hơn về chi phí và tốc độ.

**3. Observation — Chatbot thiếu feedback loop:**

Điểm yếu lớn nhất của Chatbot: không có cơ chế kiểm tra lại. Nếu câu trả lời sai, người dùng phải tự phát hiện và hỏi lại. Agent có Observation để tự điều chỉnh — gặp lỗi tool → thay tham số → thử lại, tất cả trong một request.

---

## IV. Future Improvements (5 Points)

**Scalability:** Thêm conversation memory cho Chatbot (lưu 5-10 tin nhắn gần nhất) để hỗ trợ multi-turn hội thoại. Hiện tại mỗi câu hỏi là độc lập — người dùng phải nhắc lại context mỗi lần.

**Safety:** Thêm output filter kiểm tra câu trả lời không chứa thông tin hallucinated (số liệu thời tiết, giá vé cụ thể không có nguồn). Có thể dùng một LLM nhỏ hơn để verify.

**Performance:** Với câu hỏi đơn giản, thay GPT-4o bằng GPT-4o-mini — giảm latency ~50% và cost ~90% mà chất lượng không giảm đáng kể cho use case tư vấn chung.
