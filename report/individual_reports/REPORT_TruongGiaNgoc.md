# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Truong Gia Ngoc
- **Student ID**: 2A202600329
- **Date**: 6-4-2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implemented**: `tools.py`, `test_cases.md`

- **Code Highlights**:

  *Four tool functions in `tools.py`:*

  | Tool | Approach | Key detail |
  |------|----------|-----------|
  | `get_weather` | Open-Meteo free API (no key required) | Two-step: geocoding → current weather; returns temperature, humidity, UV index, wind, and clothing advice |
  | `search_attractions` | Internal `_ATTRACTIONS_DB` dict with `(location, interest)` composite key | Gracefully returns available interest categories when exact key is missing, letting the agent self-correct |
  | `estimate_budget` | Rule-based cost ranges (domestic vs. international) | Separates per-day range from total, and explicitly lists what is/isn't included |
  | `get_current_datetime` | `datetime.now()` + timezone from geocoding API | Annotated with `LUÔN LUÔN dùng tool này` to prevent the LLM from hallucinating a date from training data |

  *Argument parsers (`_parse_and_call_search`, `_parse_and_call_budget`) convert the raw LLM argument string (e.g., `"Phú Quốc, biển"`) into typed function calls, with safe defaults for missing parameters.*

  *`TOOLS` registry — the list of dicts that `agent.py` imports and injects verbatim into the system prompt:*

  ```python
  TOOLS = [
      {
          "name": "get_weather",
          "description": get_weather.__doc__,   # rich docstring injected as tool spec
          "func": lambda args: get_weather(args),
          "signature": "get_weather(city)",
      },
      ...
  ]
  ```

  *Five test cases in `test_cases.md` with expected agent traces, covering: chatbot-wins (TC-01 general tips, TC-02 cultural knowledge), agent-wins (TC-03 real-time weather, TC-04 multi-step 3-tool chain), and edge cases (TC-05 non-existent city → fallback mechanism).*

- **Documentation**: Each tool function contains a bilingual docstring with sections `MỤC ĐÍCH / INPUT / OUTPUT / KHI NÀO NÊN DÙNG / KHÔNG NÊN DÙNG`. Because the `description` field in `TOOLS` is set to `<function>.__doc__`, `agent.py` automatically injects these docstrings into the LLM's system prompt at runtime, giving the model precise grounding on when and how to call each tool without hard-coding tool specs in the agent itself.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: The agent entered a repeated-action loop when a user asked about beach activities in Đà Nẵng. The tool `search_attractions(Đà Nẵng, biển)` returned a graceful error (the key `("đà nẵng", "biển")` does not exist in `_ATTRACTIONS_DB` — only `"thiên nhiên"` and `"vui chơi"` are available there). The Observation message explicitly listed the available interests, yet the agent called the same action again on the very next step:

  ```
  [Bước 1] → Tool: search_attractions(Đà Nẵng, biển)
           ← Không có dữ liệu 'biển' cho Đà Nẵng.
             Sở thích khả dụng: thiên nhiên, vui chơi, ẩm thực.
  [Bước 2] → Tool: search_attractions(Đà Nẵng, biển)  ← lặp lại!
           ← Không có dữ liệu 'biển' cho Đà Nẵng...
  [Bước 3] → Tool: search_attractions(Đà Nẵng, biển)  ← lặp lại lần 2!
  [!] FALLBACK: Tool thất bại 3 lần liên tiếp → chuyển sang kiến thức tĩnh
  ```

- **Log Source**: Observed in the console `TOOL_RESULT` trace events during `python agent.py` interactive testing; the `trace_log` list in `TravelReActAgent` captures each `TOOL_CALL` and `TOOL_RESULT` event.

- **Diagnosis**: Two compounding causes:
  1. **Missing guard in the system prompt**: The original `ĐIỀU KIỆN DỪNG` section did not include an explicit rule against repeating an identical action. The LLM re-read the user's request ("muốn tắm biển") each Thought iteration and kept concluding it should try `biển` — effectively ignoring the Observation content.
  2. **Temperature too high**: The initial draft used `TEMPERATURE = 0.7`, adding stochasticity that made the model inconsistently act on the Observation data. With high temperature, the LLM sometimes "forgot" to read the hint in the previous Observation and regenerated the same Action.

- **Solution**:
  1. Added the rule `"KHÔNG lặp lại Action với tham số giống hệt nhau"` to the `ĐIỀU KIỆN DỪNG` section in `agent.py`'s system prompt (now visible at line 70).
  2. Lowered `TEMPERATURE` from `0.7` to `0.2` (`agent.py` line 24), making the Thought-Action generation more deterministic and observation-driven.

  After both fixes, the same query produced: `search_attractions(Đà Nẵng, thiên nhiên)` on step 2, then `search_attractions(Đà Nẵng, vui chơi)` on step 3 — matching the expected trace in `test_cases.md` TC-04.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1. **Reasoning**: The `Thought` block changes the model's mode from *recall* to *plan-then-verify*. Instead of immediately generating an answer from training data, the agent first articulates what information is missing and which tool can fill the gap. The most striking example from `trace.md` is step 3: after receiving weather data for both cities, the agent's Thought compared humidity values (70% vs 60%) and recommended Phú Quốc despite it being 1°C hotter — a nuanced, data-driven conclusion a chatbot would not reach because it has no real temperature or humidity data to compare. The Chatbot in the same comparison table was marked `⚠️ Có nhưng không dựa trên data` for the recommendation task.

2. **Reliability**: The Agent performed *worse* than the Chatbot in two distinct scenarios:
   - **Pure knowledge questions** (TC-01 motion-sickness tips, TC-02 Japanese customs): These are stable, factual topics the LLM already knows well. The Agent wasted 1–2 Thought/Action iterations trying to find a relevant tool before concluding none applied, adding latency with no accuracy gain. The Chatbot answered immediately in a more natural, conversational tone.
   - **Non-existent or unsupported destinations** (TC-05 "Atlantis"): The Agent's `FALLBACK_THRESHOLD = 3` meant it had to fail three times before giving a static-knowledge answer — the same answer the Chatbot would produce in under 2 seconds. For edge cases with no matching tool data, the Agent's loop overhead is pure cost with no benefit.

3. **Observation**: Observations acted as hard, injection-resistant facts in the agent's context window. Each Observation value anchored the next Thought: after step 1's Observation returned `31°C` for Đà Nẵng, the step-2 Thought correctly held `31°C` in working memory while fetching Phú Quốc data, and step 3 synthesized both. This chain is impossible in a single-turn chatbot where the model has to fabricate weather data from training priors. Conversely, when Observations contained error messages (the beach-category bug above), they were *supposed to* redirect the agent — demonstrating that the quality of Observation feedback directly determines whether the agent converges or loops.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: The current `_ATTRACTIONS_DB` is a hardcoded Python dict with ~20 location-interest pairs. For production, migrate to a **vector database** (e.g., Qdrant or Pinecone) where attraction records are embedded and retrieved by semantic similarity. This lets the agent find relevant results even when the user's phrasing doesn't exactly match an interest category (e.g., "chỗ để chụp ảnh đẹp" → maps to `"thiên nhiên"` semantically), and allows the database to scale to thousands of locations without any code change.

- **Safety**: Implement a **Supervisor LLM** pattern — a lightweight secondary model that audits each parsed `Action` before execution. It would check: (a) is the tool call coherent with the conversation so far? (b) does the argument look safe (no prompt injection via user input)? (c) is the same action about to be repeated? This prevents both adversarial inputs and the repeated-action loop described in Section II, acting as a circuit breaker earlier than `FALLBACK_THRESHOLD`.

- **Performance**: The sequential `Thought → Action → Observation` loop means multi-city comparisons (like the Đà Nẵng vs. Phú Quốc query) must call `get_weather` twice in series (~4–6 s each). Adding an **async parallel tool execution** layer — where the agent can dispatch a batch of independent tool calls in one step and receive all Observations before the next Thought — would reduce total latency from ~12 s to ~6 s for this common pattern, without any change to the ReAct logic itself.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
