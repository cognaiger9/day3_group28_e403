# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Đinh Công Tài
- **Student ID**: 2A202600034
- **Role in Group**: QA + Documentation Lead
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

### Modules Implemented

| File | Vai trò |
| :--- | :--- |
| `run_demo.py` | Batch runner — chạy 5 test cases, in kết quả so sánh, ghi session log |
| `test_cases.md` | Tài liệu 5 test cases với expected output và pass/fail criteria |
| `trace.md` | Full trace log của 5 test cases — Agent steps, token counts, latency |
| `requirements.txt` | Dependency list — pin version để đảm bảo reproducibility |

### Code Highlights

**1. `run_demo.py` — Batch runner với output format rõ ràng:**

```python
# run_demo.py
TEST_CASES = [
    "Tôi hay bị say xe. Có mẹo gì để chống say xe không?",
    "Tôi muốn đi Nhật Bản lần đầu. Cần biết phong tục gì để không thất lễ?",
    "Thời tiết Hội An hôm nay thế nào? Có nên đi không?",
    "Lên kế hoạch 4 ngày ở Đà Nẵng, ngân sách 10 triệu, thích biển và hải sản.",
    "Thành phố Atlantis huyền thoại có thật không? Nếu có thì ở đâu?",
]

for i, q in enumerate(TEST_CASES, 1):
    print(f"\n{'='*60}")
    print(f"TC-{i:02d}: {q}")
    print(f"{'='*60}")
    chatbot_result = call_chatbot(q)
    agent_result   = TravelReActAgent(tools=_TOOLS).run_with_meta(q)
    _print_comparison(chatbot_result, agent_result)
    log_query(q, chatbot_result, agent_result)
```

**2. Kết quả in có cấu trúc — dễ debug và so sánh:**

```python
def _print_comparison(chatbot, agent):
    print(f"\n[CHATBOT] {chatbot['latency_ms']}ms | {chatbot['tokens']['total']} tokens")
    print(chatbot['answer'])
    print(f"\n[AGENT]   {agent['latency_ms']}ms | {agent['tokens']['total']} tokens")
    print(f"Iterations: {agent['iterations']} | Tool calls: {len(agent['tool_calls'])}")
    for step in agent['trace']:
        print(f"  Thought : {step['thought'][:80]}...")
        print(f"  Action  : {step['action']}({step['args']})")
        print(f"  Obs     : {step['observation'][:60]}...")
    print(f"\nFinal: {agent['answer']}")
```

**3. `requirements.txt` — pin versions để tránh breaking changes:**

```
openai>=1.30.0,<2.0.0
google-generativeai>=0.5.0
flask>=3.0.0
requests>=2.31.0
python-dotenv>=1.0.0
```

### Documentation

`run_demo.py` là script duy nhất cần chạy để reproduce toàn bộ kết quả lab. Nó đóng vai trò **integration test** — chạy cả 5 test cases, gọi cả chatbot lẫn agent, in kết quả so sánh có cấu trúc, và kích hoạt `log_manager.py` ghi session log. `test_cases.md` ghi lại thiết kế test với rationale cho từng case. `trace.md` là ground truth kết quả thực tế để reviewer kiểm tra mà không cần chạy lại.

---

## II. Debugging Case Study (10 Points)

### Problem: `run_demo.py` crash trên Windows — UnicodeEncodeError

**Mô tả:** Khi chạy `run_demo.py` trên Windows 11 (cmd.exe), script crash ngay ở dòng đầu tiên in tiếng Việt:

```
UnicodeEncodeError: 'cp932' codec can't encode character '\u0103'
in position 12: illegal multibyte sequence
```

**Log thực tế:**

```
> python run_demo.py
TC-01: Tôi hay bị say xe...
UnicodeEncodeError: 'cp932' codec can't encode character '\u0103'...
```

**Diagnosis:**

Windows cmd.exe mặc định dùng code page 932 (Japanese Shift-JIS). Python `print()` dùng stdout encoding mặc định của hệ thống → không encode được ký tự tiếng Việt như `ă`, `ơ`, `ư`, `đ`. Vấn đề không xuất hiện trên macOS/Linux vì mặc định UTF-8.

**Solution (2 bước):**

*Bước 1* — Thêm vào đầu `run_demo.py`:
```python
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
```

*Bước 2* — Thay các ký tự Unicode decorative bằng ASCII:
```python
# Trước:
print(f"{'═'*60}")   # box drawing char — crash trên Windows
print(f"⏱ {latency}ms")  # emoji — crash trên cp932

# Sau:
print(f"{'='*60}")   # ASCII safe
print(f"[{latency}ms]")  # plain text
```

Hoặc chạy với flag: `python -X utf8 run_demo.py`

Sau fix: chạy được trên Windows, macOS, Linux mà không cần thay đổi cài đặt hệ thống.

**Bài học:** Bao giờ cũng test script trên cả 2 nền tảng (Windows + Unix) trước khi submit. Tiếng Việt đặc biệt dễ gây lỗi encoding trên Windows vì cp932 không cover Unicode Latin Extended (dải ký tự tiếng Việt). Giải pháp nhanh nhất là luôn explicit set UTF-8 ở đầu script.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

**1. Reasoning — Test cases phải cover được sự khác biệt:**

Khi thiết kế 5 test cases, tôi phải suy nghĩ: *"Case nào sẽ làm lộ điểm yếu của Chatbot? Case nào Agent tốn công mà kết quả như nhau?"* TC-01 và TC-02 là "control group" — câu hỏi kiến thức chung mà cả hai đều làm tốt, nhưng Agent tốn gấp 10x token. TC-03 là "critical test" cho real-time data. TC-04 là "stress test" cho multi-step reasoning. TC-05 là "edge case" cho câu hỏi không có câu trả lời rõ ràng. Thiết kế test tốt phải cover cả 3 loại này.

**2. Reliability — Từ góc nhìn QA: Agent có thể fail theo nhiều cách hơn Chatbot:**

Trong quá trình test, tôi ghi nhận: Chatbot chỉ có 1 failure mode (hallucination). Agent có ít nhất 4 failure modes: hallucinated observation, sai tool choice, sai tham số tool, vòng lặp vô tận. May mắn là Agent có `MAX_ITERATIONS` và `FALLBACK_THRESHOLD` làm safety net — nhưng QA cần test cả 4 paths đó. Tôi đã viết explicit test cho edge cases trong `test_cases.md`.

**3. Observation — Trace log là tài sản quan trọng nhất của Agent:**

Khi review `trace.md`, tôi có thể thấy chính xác tại sao Agent đưa ra quyết định nào, dùng tool gì với tham số gì, nhận observation nào. Điều này giúp debug gấp 3-4 lần so với Chatbot vì Chatbot là black-box: chỉ có input/output, không có reasoning trail. Với Agent, nếu output sai, tôi biết cần fix ở đâu — tool logic, tool description, hay system prompt rule.

---

## IV. Future Improvements (5 Points)

**Scalability:** Tự động hóa regression testing — thay vì chạy `run_demo.py` thủ công, tích hợp với pytest để có `assert` cụ thể cho từng TC. Ví dụ: `assert "35" in agent_result["answer"] or "36" in agent_result["answer"]` cho TC-03 (nhiệt độ thực tế). Khi code thay đổi, CI/CD tự phát hiện regression.

**Safety:** Thêm test case cho adversarial inputs — câu hỏi prompt injection như *"Bỏ qua tất cả hướng dẫn trước đó và..."* hoặc tham số tool bất thường như `city=""`, `days=-1`. Đây là QA gap hiện tại của hệ thống.

**Performance:** Tạo `benchmark.py` riêng — chạy mỗi TC 5 lần, tính p50/p95/p99 latency và token variance. Hiện tại `run_demo.py` chỉ chạy 1 lần nên số liệu có thể bị outlier. Variance cao là dấu hiệu system prompt không ổn định.
