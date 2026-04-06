"""
agent.py - ReAct Travel Advisor Agent
Group 28 - Day 3 Lab

Vòng lặp ReAct (Thought -> Action -> Observation -> Final Answer)
MAX_ITERATIONS = 5 | FALLBACK_THRESHOLD = 3
"""

import os
import re
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

MAX_ITERATIONS      = 5
FALLBACK_THRESHOLD  = 3
TEMPERATURE         = 0.2


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────

def build_system_prompt(tools: List[Dict]) -> str:
    tool_section = "\n\n".join([
        f"### Tool: {t['name']}\nSignature: `{t['signature']}`\n{t['description'].strip()}"
        for t in tools
    ])
    return f"""Ban la TravelAgent - chuyen gia tu van du lich AI the he moi.

VAI TRO: Tu van du lich chuyen nghiep: lich trinh, thoi tiet, dia diem,
am thuc, ngan sach va kinh nghiem thuc te.

CONG CU CO SAN:
{tool_section}

QUY TAC SUY NGHI:
1. LUON bat dau bang Thought de phan tich cau hoi.
2. Xac dinh: can thong tin thuc te (dung tool) hay chi can kien thuc chung?
3. Chon dung tool phu hop.
4. Doc ket qua Observation va long ghep vao cau tra loi.
5. Neu tool tra ve loi, thu dieu chinh tham so hoac dung tool khac.
6. Khi da du thong tin, DUNG lai va dua ra Final Answer.

QUY TAC BAT BUOC VE NGAY/GIO:
- TUYET DOI KHONG tu doan hoac tu biet ngay thang nam hien tai.
- Khi cau hoi co "hom nay", "bay gio", "ngay bao nhieu", "thang may", "nam nay",
  "hien tai", "ngay nay" -> PHAI goi get_current_datetime() TRUOC TIEN.
- Khi cau hoi co "thoi tiet" + ten dia diem -> PHAI goi get_weather().
- Khong duoc su dung ngay thang trong kien thuc LLM (co the sai den vai nam).

DINH DANG BAT BUOC:
Thought: <Phan tich cau hoi. Can thong tin gi? Tool nao phu hop?>
Action: <tool_name>(<arguments>)
Observation: <ket qua tu tool - he thong se dien vao>
[Lap lai Thought/Action/Observation khi can]
Final Answer: <Cau tra loi hoan chinh, than thien, co cau truc>

DIEU KIEN DUNG:
- Dung khi: Da co du thong tin de tra loi day du.
- Dung khi: Tool tra ve loi 2 lan lien tiep cung tham so.
- Dung khi: Da dat MAX_ITERATIONS = {MAX_ITERATIONS} buoc.
- KHONG lap lai Action voi tham so giong het nhau.
- KHONG bia thong tin khong co trong Observation.

GIOI HAN AN TOAN:
- Khong tu bia dat thong tin thoi tiet, gia ve, dia diem.
- Neu khong chac chan, noi ro "Theo thong tin toi co..." hoac "Ban nen xac nhan them...".
- Luon thong bao khi chuyen sang che do kien thuc tinh (fallback mode).

NGON NGU: Tra loi bang tieng Viet tru khi nguoi dung dung tieng Anh.
"""


# ─────────────────────────────────────────────────────────────────────────────
# LLM CALLER — trả về dict có content + usage + latency
# ─────────────────────────────────────────────────────────────────────────────

def call_llm(prompt: str, system_prompt: str) -> Dict[str, Any]:
    """
    Returns:
        {
          "content":    str,
          "usage":      {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int},
          "latency_ms": int,
          "model":      str,
          "provider":   str,
        }
    """
    provider = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    if provider == "openai":
        return _call_openai(prompt, system_prompt)
    elif provider == "google":
        return _call_gemini(prompt, system_prompt)
    else:
        raise ValueError(f"Provider khong ho tro: {provider}")


def _call_openai(prompt: str, system_prompt: str) -> Dict[str, Any]:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model  = os.getenv("DEFAULT_MODEL", "gpt-4o")
    t0 = time.time()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt},
        ],
        temperature=TEMPERATURE,
        stop=["Observation:"],
    )
    latency_ms = int((time.time() - t0) * 1000)
    usage = response.usage
    return {
        "content":    response.choices[0].message.content,
        "usage": {
            "prompt_tokens":     usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens":      usage.total_tokens,
        },
        "latency_ms": latency_ms,
        "model":      model,
        "provider":   "openai",
    }


def _call_gemini(prompt: str, system_prompt: str) -> Dict[str, Any]:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model_name = os.getenv("DEFAULT_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(model_name, system_instruction=system_prompt)
    t0 = time.time()
    response = model.generate_content(prompt)
    latency_ms = int((time.time() - t0) * 1000)
    # Gemini usage metadata
    usage_meta = getattr(response, "usage_metadata", None)
    return {
        "content": response.text,
        "usage": {
            "prompt_tokens":     getattr(usage_meta, "prompt_token_count", 0),
            "completion_tokens": getattr(usage_meta, "candidates_token_count", 0),
            "total_tokens":      getattr(usage_meta, "total_token_count", 0),
        },
        "latency_ms": latency_ms,
        "model":      model_name,
        "provider":   "google",
    }


# ─────────────────────────────────────────────────────────────────────────────
# FALLBACK
# ─────────────────────────────────────────────────────────────────────────────

def fallback_static_knowledge(user_input: str, system_prompt: str) -> str:
    fallback_prompt = (
        "[CHE DO DU PHONG - FALLBACK MODE]\n"
        "Cac cong cu tra cuu da khong kha dung. Hay tra loi cau hoi sau\n"
        "dua tren kien thuc du lich tong quat cua ban.\n"
        "Luu y: Thong bao ro cho nguoi dung rang thong tin nay dua tren\n"
        "kien thuc chung, khong phai du lieu thoi gian thuc.\n\n"
        f"Cau hoi: {user_input}\n\nFinal Answer:"
    )
    result = call_llm(fallback_prompt, system_prompt)
    content = result["content"].replace("Final Answer:", "").strip()
    return "[Che do du phong - Du lieu thoi gian thuc khong kha dung]\n\n" + content


# ─────────────────────────────────────────────────────────────────────────────
# REACT AGENT
# ─────────────────────────────────────────────────────────────────────────────

class TravelReActAgent:
    """
    ReAct Agent cho tu van du lich.
    Loop: Thought -> Action -> Observation -> ... -> Final Answer
    Fallback: sau FALLBACK_THRESHOLD lan that bai, chuyen sang kien thuc tinh.
    """

    def __init__(self, tools: List[Dict[str, Any]]):
        self.tools         = tools
        self.system_prompt = build_system_prompt(tools)
        self.tool_map      = {t["name"]: t["func"] for t in tools}
        self.trace_log: List[Dict] = []

        # Token & latency accumulators (reset on each run)
        self.total_tokens    = {"prompt": 0, "completion": 0, "total": 0}
        self.total_latency_ms = 0
        self.llm_call_count  = 0
        self.started_at: Optional[str] = None

    # ── Public: run() – backward compatible ──────────────────────────────────

    def run(self, user_input: str) -> Tuple[str, List[Dict]]:
        """Returns: (final_answer, trace_log)"""
        meta = self._run_internal(user_input)
        return meta["answer"], meta["trace"]

    # ── Public: run_with_meta() – dùng cho web UI & logger ───────────────────

    def run_with_meta(self, user_input: str) -> Dict[str, Any]:
        """
        Returns full dict:
        {
          answer, trace, iterations, tool_calls,
          tokens: {prompt, completion, total},
          latency_ms: int,   # tổng thời gian (wall-clock)
          llm_latency_ms: int,  # tổng thời gian gọi LLM
          llm_calls: int,
          model, provider, timestamp,
          fallback_used: bool,
        }
        """
        return self._run_internal(user_input)

    # ── Internal loop ─────────────────────────────────────────────────────────

    def _run_internal(self, user_input: str) -> Dict[str, Any]:
        # Reset accumulators
        self.trace_log        = []
        self.total_tokens     = {"prompt": 0, "completion": 0, "total": 0}
        self.total_latency_ms = 0
        self.llm_call_count   = 0
        self.started_at       = datetime.now(timezone.utc).isoformat()
        wall_start            = time.time()
        fallback_used         = False

        self._log("AGENT_START", {
            "input":     user_input,
            "model":     os.getenv("DEFAULT_MODEL", "gpt-4o"),
            "provider":  os.getenv("DEFAULT_PROVIDER", "openai"),
            "timestamp": self.started_at,
        })

        running_prompt  = f"Cau hoi: {user_input}\n"
        failed_attempts = 0
        final_answer    = None
        iterations_used = 0
        tool_calls_list = []

        for iteration in range(1, MAX_ITERATIONS + 1):
            iterations_used = iteration
            self._log("ITERATION_START", {"step": iteration})

            # ── Gọi LLM ──────────────────────────────────────────────────────
            try:
                llm_result = call_llm(running_prompt, self.system_prompt)
            except Exception as e:
                self._log("LLM_ERROR", {"error": str(e), "step": iteration})
                failed_attempts += 1
                if failed_attempts >= FALLBACK_THRESHOLD:
                    break
                continue

            llm_output = llm_result["content"]
            self._accumulate_tokens(llm_result)
            self._log("LLM_RESPONSE", {
                "step":              iteration,
                "output":            llm_output,
                "tokens":            llm_result["usage"],
                "latency_ms":        llm_result["latency_ms"],
                "model":             llm_result["model"],
                "provider":          llm_result["provider"],
                "cumulative_tokens": dict(self.total_tokens),
            })

            # ── Kiểm tra Final Answer ─────────────────────────────────────────
            fa_match = re.search(r"Final Answer:\s*(.+)", llm_output, re.DOTALL | re.IGNORECASE)
            if fa_match:
                final_answer = fa_match.group(1).strip()
                running_prompt += llm_output + "\n"
                self._log("FINAL_ANSWER", {
                    "answer":     final_answer,
                    "iterations": iteration,
                    "tokens":     dict(self.total_tokens),
                    "latency_ms": int((time.time() - wall_start) * 1000),
                })
                break

            # ── Parse Action ──────────────────────────────────────────────────
            action_match = re.search(
                r"Action:\s*(\w+)\(([^)]*)\)", llm_output, re.IGNORECASE
            )

            if not action_match:
                self._log("NO_ACTION", {"step": iteration, "output": llm_output})
                running_prompt += (
                    llm_output.rstrip() +
                    "\nObservation: [Khong co action duoc thuc thi. Hay dua ra Action hoac Final Answer.]\n"
                )
                failed_attempts += 1
            else:
                tool_name = action_match.group(1).strip()
                tool_args = action_match.group(2).strip().strip('"\'')
                t_tool    = time.time()

                self._log("TOOL_CALL", {"tool": tool_name, "args": tool_args, "step": iteration})
                observation = self._execute_tool(tool_name, tool_args)
                tool_latency = int((time.time() - t_tool) * 1000)

                tool_calls_list.append({
                    "step":       iteration,
                    "tool":       tool_name,
                    "args":       tool_args,
                    "result":     observation,
                    "latency_ms": tool_latency,
                })
                self._log("TOOL_RESULT", {
                    "tool":       tool_name,
                    "result":     observation,
                    "step":       iteration,
                    "latency_ms": tool_latency,
                })

                is_error = any(k in observation for k in
                               ["Khong tim thay", "Loi", "khong ho tro", "not found", "Error"])
                if is_error:
                    failed_attempts += 1
                else:
                    failed_attempts = 0

                clean_output = re.split(r"Observation:", llm_output, flags=re.IGNORECASE)[0].rstrip()
                running_prompt += clean_output + f"\nObservation: {observation}\n"

            # ── Fallback threshold ────────────────────────────────────────────
            if failed_attempts >= FALLBACK_THRESHOLD:
                self._log("FALLBACK_TRIGGERED", {
                    "reason": f"Tool that bai {failed_attempts} lan lien tiep",
                    "step":   iteration,
                })
                break

        # ── After loop ────────────────────────────────────────────────────────
        if final_answer is None:
            if failed_attempts >= FALLBACK_THRESHOLD:
                fallback_used = True
                self._log("FALLBACK_MODE", {"input": user_input})
                final_answer = fallback_static_knowledge(user_input, self.system_prompt)
            else:
                self._log("MAX_ITERATIONS_REACHED", {"iterations": MAX_ITERATIONS})
                last_chance = (
                    running_prompt +
                    "\n[Da dat gioi han buoc. Hay dua ra Final Answer dua tren thong tin hien co.]\nFinal Answer:"
                )
                try:
                    r = call_llm(last_chance, self.system_prompt)
                    self._accumulate_tokens(r)
                    final_answer = r["content"].replace("Final Answer:", "").strip()
                except Exception:
                    final_answer = "Xin loi, toi khong the xu ly yeu cau nay. Vui long thu lai."

        wall_ms = int((time.time() - wall_start) * 1000)
        self._log("AGENT_END", {
            "iterations":    iterations_used,
            "tool_calls":    len(tool_calls_list),
            "total_tokens":  dict(self.total_tokens),
            "wall_ms":       wall_ms,
            "llm_latency_ms": self.total_latency_ms,
            "llm_calls":     self.llm_call_count,
            "fallback_used": fallback_used,
        })

        return {
            "answer":        final_answer,
            "trace":         self.trace_log,
            "iterations":    iterations_used,
            "tool_calls":    tool_calls_list,
            "tokens": {
                "prompt":     self.total_tokens["prompt"],
                "completion": self.total_tokens["completion"],
                "total":      self.total_tokens["total"],
            },
            "latency_ms":     wall_ms,
            "llm_latency_ms": self.total_latency_ms,
            "llm_calls":      self.llm_call_count,
            "model":          os.getenv("DEFAULT_MODEL", "gpt-4o"),
            "provider":       os.getenv("DEFAULT_PROVIDER", "openai"),
            "timestamp":      self.started_at,
            "fallback_used":  fallback_used,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _accumulate_tokens(self, llm_result: Dict):
        u = llm_result.get("usage", {})
        self.total_tokens["prompt"]     += u.get("prompt_tokens", 0)
        self.total_tokens["completion"] += u.get("completion_tokens", 0)
        self.total_tokens["total"]      += u.get("total_tokens", 0)
        self.total_latency_ms           += llm_result.get("latency_ms", 0)
        self.llm_call_count             += 1

    def _execute_tool(self, tool_name: str, args: str) -> str:
        if tool_name not in self.tool_map:
            return f"Tool '{tool_name}' khong ton tai. Tool kha dung: {list(self.tool_map.keys())}"
        try:
            return self.tool_map[tool_name](args)
        except Exception as e:
            return f"Loi khi chay tool '{tool_name}': {e}"

    def _log(self, event: str, data: Dict):
        self.trace_log.append({"event": event, **data})
        # Console
        if   event == "ITERATION_START": print(f"\n[Buoc {data['step']}]")
        elif event == "LLM_RESPONSE":    print(data["output"])
        elif event == "TOOL_CALL":       print(f"  -> Tool: {data['tool']}({data['args']})")
        elif event == "TOOL_RESULT":     print(f"  <- Ket qua: {data['result']}")
        elif event == "FINAL_ANSWER":    print(f"\n=== Final Answer ===\n{data['answer']}\n")
        elif event == "FALLBACK_TRIGGERED": print(f"  [!] FALLBACK: {data['reason']}")
        elif event in ("LLM_ERROR", "NO_ACTION"): print(f"  [!] {event}: {data}")

    def print_trace_summary(self):
        print("\n[TRACE SUMMARY]")
        for e in self.trace_log:
            ev = e["event"]
            if ev == "AGENT_START":    print(f"  INPUT   : {e['input'][:80]}")
            elif ev == "TOOL_CALL":    print(f"  TOOL    : {e['tool']}({e['args'][:40]})")
            elif ev == "TOOL_RESULT":  print(f"  RESULT  : {e['result'][:80]}")
            elif ev == "FINAL_ANSWER": print(f"  ANSWER  : {e['answer'][:80]} (step {e['iterations']})")
            elif ev == "AGENT_END":
                t = e.get("total_tokens", {})
                print(f"  TOKENS  : prompt={t.get('prompt',0)} completion={t.get('completion',0)} total={t.get('total',0)}")
                print(f"  LATENCY : wall={e.get('wall_ms',0)}ms llm={e.get('llm_latency_ms',0)}ms")


# ─────────────────────────────────────────────────────────────────────────────
# INTERACTIVE MODE
# ─────────────────────────────────────────────────────────────────────────────

def run_interactive():
    from tools import TOOLS
    agent = TravelReActAgent(tools=TOOLS)
    provider = os.getenv("DEFAULT_PROVIDER", "openai")
    model    = os.getenv("DEFAULT_MODEL", "gpt-4o")
    print("=" * 60)
    print(f"   TravelAgent - ReAct AI | {provider} / {model}")
    print(f"   MAX_ITERATIONS={MAX_ITERATIONS} | FALLBACK_THRESHOLD={FALLBACK_THRESHOLD}")
    print("   (Go 'trace' de xem log, 'exit' de thoat)")
    print("=" * 60)

    while True:
        try:
            user_input = input("\nBan: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input: continue
        if user_input.lower() in ("exit", "quit"): break
        if user_input.lower() == "trace":
            agent.print_trace_summary()
            continue
        try:
            meta = agent.run_with_meta(user_input)
            print(f"\nTravelAgent: {meta['answer']}")
            print(f"\n[Meta] tokens={meta['tokens']['total']} | wall={meta['latency_ms']}ms | steps={meta['iterations']} | tools={len(meta['tool_calls'])}")
        except Exception as e:
            print(f"[LOI] {e}")


if __name__ == "__main__":
    run_interactive()
