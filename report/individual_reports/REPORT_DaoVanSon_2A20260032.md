# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Đào Văn Sơn
- **Student ID**: 2A202600032
- **Role in Group**: Người C — ReAct Agent Developer
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

### Modules Implemented

| File | Vai trò |
| :--- | :--- |
| `agent.py` | Toàn bộ — ReAct loop, system prompt, fallback, token tracking |

### Code Highlights

**1. Vòng lặp ReAct chính** (`agent.py` — method `_run_internal`):

```python
for iteration in range(1, MAX_ITERATIONS + 1):
    llm_result = call_llm(running_prompt, self.system_prompt)
    llm_output = llm_result["content"]

    # Kiểm tra Final Answer
    fa_match = re.search(r"Final Answer:\s*(.+)", llm_output, re.DOTALL)
    if fa_match:
        final_answer = fa_match.group(1).strip()
        break

    # Parse và thực thi Action
    action_match = re.search(r"Action:\s*(\w+)\(([^)]*)\)", llm_output)
    if action_match:
        tool_name = action_match.group(1).strip()
        observation = self._execute_tool(tool_name, tool_args)
        running_prompt += clean_output + f"\nObservation: {observation}\n"
```

**2. Fallback sau 3 lần tool thất bại:**

```python
if failed_attempts >= FALLBACK_THRESHOLD:
    final_answer = fallback_static_knowledge(user_input, self.system_prompt)
    # Thông báo người dùng: "[Chế độ dự phòng - không có dữ liệu thực]"
```

**3. Token tracking tích lũy qua nhiều LLM calls:**

```python
def _accumulate_tokens(self, llm_result):
    self.total_tokens["prompt"]     += llm_result["usage"]["prompt_tokens"]
    self.total_tokens["completion"] += llm_result["usage"]["completion_tokens"]
    self.total_latency_ms           += llm_result["latency_ms"]
```

**4. `run_with_meta()` cho Web UI và logging:**

Trả về dict đầy đủ: `answer`, `trace`, `iterations`, `tool_calls`, `tokens`, `latency_ms`, `llm_latency_ms`, `fallback_used` — dùng bởi `app.py` và `log_manager.py`.

### Documentation

`agent.py` hoạt động như sau trong toàn hệ thống:
- Nhận câu hỏi từ `app.py` (web) hoặc `run_demo.py` (batch)
- Gọi `tools.py` để thực thi từng Action
- Ghi trace vào `self.trace_log` để `log_manager.py` lưu xuống `log/`
- Trả kết quả về cho `templates/index.html` hiển thị từng bước

---

## II. Debugging Case Study (10 Points)

### Problem: Agent trả lời sai ngày tháng — "24/10/2023"

**Mô tả:** Khi hỏi *"thời tiết hà nội bây giờ, hôm nay là ngày bao nhiêu"*, Agent trả lời đúng thời tiết (35.4°C từ API) nhưng sai ngày: "Hôm nay là ngày 24 tháng 10 năm 2023" — lệch gần 2.5 năm so với thực tế.

**Log thực tế:**

```json
{
  "event": "FINAL_ANSWER",
  "answer": "Thời tiết hiện tại ở Hà Nội là 35.4°C... Hôm nay là ngày 24 tháng 10 năm 2023."
}
```

**Diagnosis:**

Nguyên nhân 3 lớp:
1. **Không có tool ngày/giờ** → LLM không có nguồn dữ liệu nào để tra cứu
2. **LLM dùng kiến thức tĩnh** → GPT-4o training cutoff ~2023, tự điền ngày từ memory
3. **System prompt không có rule** → Không cấm LLM tự đoán ngày tháng

Đây là dạng lỗi nguy hiểm vì **không gây crash, output trông có vẻ đúng** nhưng thông tin sai. Người dùng dễ tin mà không kiểm tra lại.

**Solution:**

*Bước 1* — Thêm tool `get_current_datetime(location)` vào `tools.py`:
```python
# Open-Meteo Geocoding → timezone string → Python zoneinfo → giờ thực tế
tz = ZoneInfo(tz_str)
now = datetime.now(tz)
```

*Bước 2* — Thêm rule bắt buộc vào system prompt của `agent.py`:
```
QUY TAC BAT BUOC VE NGAY/GIO:
- TUYET DOI KHONG tu doan ngay thang nam hien tai.
- Khi cau hoi co "hom nay", "bay gio", "ngay bao nhieu"...
  -> PHAI goi get_current_datetime() TRUOC TIEN.
```

*Kết quả sau fix:* Agent gọi `get_current_datetime("Ha Noi")` → nhận `06/04/2026, 14:33` → trả lời đúng hoàn toàn.

**Bài học:** LLM luôn có xu hướng điền thông tin từ training data khi không có tool. Với bất kỳ dữ liệu time-sensitive nào (ngày, giờ, thời tiết, giá), phải có tool AND phải có rule trong system prompt buộc dùng tool đó.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

**1. Reasoning — Thought block giúp ích như thế nào?**

Block `Thought` buộc LLM phải *lập kế hoạch* trước khi hành động. Với câu hỏi phức tạp như *"4 ngày Đà Nẵng, thời tiết + địa điểm + ngân sách?"*, Chatbot trả lời ngay một lần nhưng thiếu dữ liệu thực. Agent lại suy nghĩ: *"Cần 3 loại thông tin khác nhau → gọi 3 tool theo thứ tự"* rồi mới tổng hợp. Đây chính là khả năng **decompose bài toán phức tạp** mà Chatbot không có.

**2. Reliability — Khi nào Agent tệ hơn Chatbot?**

Agent tệ hơn ở 2 trường hợp:
- **Câu hỏi kiến thức chung** (mẹo du lịch, phong tục văn hóa): Agent vẫn đúng nhưng mất thêm 3-4 giây và ~3,000 token chỉ để... không gọi tool nào. Chatbot trả lời nhanh hơn 2x với token ít hơn 10x.
- **Câu hỏi quá đơn giản** (1+1=?): Có rủi ro Agent hallucinate Observation thay vì thực sự gọi tool (Case Study 1 trong Group Report).

**3. Observation — Feedback vòng lặp ảnh hưởng thế nào?**

Observation là "mắt" của Agent. Trong TC-04, sau khi nhận `Observation: Không có dữ liệu 'biển' cho Đà Nẵng. Khả dụng: thiên nhiên, vui chơi`, Agent tự điều chỉnh sang `search_attractions("Đà Nẵng", "vui chơi")` — hành vi này **không thể xảy ra với Chatbot** vì không có feedback loop. Đây là điểm khác biệt cốt lõi: Agent *học từ môi trường trong runtime*, Chatbot thì không.

---

## IV. Future Improvements (5 Points)

**Scalability:**
Hiện tại tool được gọi tuần tự. Với câu hỏi cần 3 tool song song (thời tiết + địa điểm + ngân sách), có thể dùng async/threading để gọi đồng thời — giảm latency từ ~10s xuống ~4s.

```python
# Thay vì sequential:
obs1 = get_weather(city)
obs2 = search_attractions(city, interest)

# Dùng concurrent.futures:
with ThreadPoolExecutor() as ex:
    f1 = ex.submit(get_weather, city)
    f2 = ex.submit(search_attractions, city, interest)
```

**Safety:**
Thêm một *Supervisor LLM* nhỏ (Haiku/Flash) kiểm tra Action trước khi thực thi — phát hiện prompt injection, tham số bất thường, hoặc tool call vòng lặp giống nhau.

**Performance:**
Khi số tool tăng lên (>10), LLM khó chọn đúng tool chỉ qua text description. Giải pháp: dùng **vector embedding** để retrieve top-3 tools liên quan nhất theo câu hỏi, chỉ inject 3 tool đó vào system prompt — giảm token và tăng precision.
