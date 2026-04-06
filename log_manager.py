"""
log_manager.py - Structured logging for Travel Advisor AI
Group 28 - Day 3 Lab

Lưu tất cả kết quả vào D:\...\Day3_group28\log\
Format: JSON Lines (1 entry = 1 dòng JSON) + summary JSON
"""

import os
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

LOG_DIR = os.path.join(os.path.dirname(__file__), "log")


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def _now_str() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ts_filename() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


# ─────────────────────────────────────────────────────────────────────────────
# QUERY LOG — mỗi câu hỏi từ web UI hoặc run_demo
# ─────────────────────────────────────────────────────────────────────────────

def log_query(
    question: str,
    chatbot_result: Optional[Dict],
    agent_result: Optional[Dict],
    source: str = "web",          # "web" | "run_demo"
    test_case_id: Optional[str] = None,
) -> str:
    """
    Lưu 1 câu hỏi + kết quả cả 2 hệ thống vào file log/queries_YYYY-MM-DD.jsonl
    Mỗi dòng là 1 JSON object độc lập.
    Returns: đường dẫn file log.
    """
    _ensure_log_dir()

    # --- Build log record ---
    record = {
        "timestamp":     _now_str(),
        "source":        source,
        "test_case_id":  test_case_id,
        "question":      question,
        "chatbot": _sanitize_chatbot(chatbot_result) if chatbot_result else None,
        "agent":   _sanitize_agent(agent_result)     if agent_result   else None,
        "comparison": _build_comparison(chatbot_result, agent_result),
    }

    # --- Write to daily JSONL file ---
    date_str  = datetime.now().strftime("%Y-%m-%d")
    log_file  = os.path.join(LOG_DIR, f"queries_{date_str}.jsonl")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return log_file


def _sanitize_chatbot(r: Dict) -> Dict:
    return {
        "answer":      r.get("answer", ""),
        "tokens": {
            "prompt":     r.get("tokens", {}).get("prompt", 0),
            "completion": r.get("tokens", {}).get("completion", 0),
            "total":      r.get("tokens", {}).get("total", 0),
        },
        "latency_ms":  r.get("latency_ms", 0),
        "model":       r.get("model", ""),
        "provider":    r.get("provider", ""),
        "error":       r.get("error"),
    }


def _sanitize_agent(r: Dict) -> Dict:
    # Simplify trace for log (keep key events only)
    simplified_trace = []
    for entry in r.get("trace", []):
        ev = entry.get("event")
        if ev == "TOOL_CALL":
            simplified_trace.append({
                "event": "TOOL_CALL",
                "step":  entry.get("step"),
                "tool":  entry.get("tool"),
                "args":  entry.get("args"),
            })
        elif ev == "TOOL_RESULT":
            simplified_trace.append({
                "event":  "TOOL_RESULT",
                "step":   entry.get("step"),
                "tool":   entry.get("tool"),
                "result": entry.get("result", "")[:200],  # truncate long results
                "latency_ms": entry.get("latency_ms", 0),
            })
        elif ev == "LLM_RESPONSE":
            simplified_trace.append({
                "event":      "LLM_RESPONSE",
                "step":       entry.get("step"),
                "tokens":     entry.get("tokens"),
                "latency_ms": entry.get("latency_ms"),
            })
        elif ev in ("FINAL_ANSWER", "FALLBACK_TRIGGERED", "AGENT_END", "FALLBACK_MODE"):
            simplified_trace.append({k: v for k, v in entry.items()
                                     if k not in ("output",)})

    return {
        "answer":        r.get("answer", ""),
        "iterations":    r.get("iterations", 0),
        "tool_calls":    r.get("tool_calls", []),
        "tokens": {
            "prompt":     r.get("tokens", {}).get("prompt", 0),
            "completion": r.get("tokens", {}).get("completion", 0),
            "total":      r.get("tokens", {}).get("total", 0),
        },
        "latency_ms":     r.get("latency_ms", 0),
        "llm_latency_ms": r.get("llm_latency_ms", 0),
        "llm_calls":      r.get("llm_calls", 0),
        "model":          r.get("model", ""),
        "provider":       r.get("provider", ""),
        "fallback_used":  r.get("fallback_used", False),
        "trace_summary":  simplified_trace,
        "error":          r.get("error"),
    }


def _build_comparison(chatbot: Optional[Dict], agent: Optional[Dict]) -> Dict:
    """Tính toán các chỉ số so sánh giữa 2 hệ thống."""
    if not chatbot or not agent:
        return {}

    c_tok = chatbot.get("tokens", {}).get("total", 0)
    a_tok = agent.get("tokens", {}).get("total", 0)
    c_lat = chatbot.get("latency_ms", 0)
    a_lat = agent.get("latency_ms", 0)

    return {
        "token_delta":    a_tok - c_tok,          # >0 nghĩa agent dùng nhiều token hơn
        "token_ratio":    round(a_tok / c_tok, 2) if c_tok > 0 else None,
        "latency_delta_ms": a_lat - c_lat,
        "agent_tool_calls": len(agent.get("tool_calls", [])),
        "agent_fallback":   agent.get("fallback_used", False),
        "agent_iterations": agent.get("iterations", 0),
    }


# ─────────────────────────────────────────────────────────────────────────────
# SESSION LOG — dành cho run_demo.py (toàn bộ 5 test cases)
# ─────────────────────────────────────────────────────────────────────────────

def log_session(session_results: list, source: str = "run_demo") -> str:
    """
    Lưu toàn bộ session (nhiều test case) vào 1 file JSON riêng.
    Returns: đường dẫn file.
    """
    _ensure_log_dir()
    ts = _ts_filename()
    filename = os.path.join(LOG_DIR, f"session_{ts}.json")

    # Tính tổng kết
    total_chatbot_tokens = sum(
        r.get("chatbot", {}).get("tokens", {}).get("total", 0)
        for r in session_results if r.get("chatbot")
    )
    total_agent_tokens = sum(
        r.get("agent", {}).get("tokens", {}).get("total", 0)
        for r in session_results if r.get("agent")
    )
    total_chatbot_latency = sum(
        r.get("chatbot", {}).get("latency_ms", 0)
        for r in session_results if r.get("chatbot")
    )
    total_agent_latency = sum(
        r.get("agent", {}).get("latency_ms", 0)
        for r in session_results if r.get("agent")
    )

    session_data = {
        "session_id":   ts,
        "timestamp":    _now_str(),
        "source":       source,
        "model":        os.getenv("DEFAULT_MODEL", "gpt-4o"),
        "provider":     os.getenv("DEFAULT_PROVIDER", "openai"),
        "total_cases":  len(session_results),
        "summary": {
            "chatbot": {
                "total_tokens":  total_chatbot_tokens,
                "total_latency_ms": total_chatbot_latency,
                "avg_latency_ms":   total_chatbot_latency // max(len(session_results), 1),
            },
            "agent": {
                "total_tokens":  total_agent_tokens,
                "total_latency_ms": total_agent_latency,
                "avg_latency_ms":   total_agent_latency // max(len(session_results), 1),
                "total_tool_calls": sum(
                    len(r.get("agent", {}).get("tool_calls", []))
                    for r in session_results if r.get("agent")
                ),
            },
            "token_efficiency": {
                "agent_vs_chatbot_ratio": round(total_agent_tokens / total_chatbot_tokens, 2)
                    if total_chatbot_tokens > 0 else None,
            },
        },
        "results": session_results,
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

    return filename


# ─────────────────────────────────────────────────────────────────────────────
# READ LOGS — dành cho web UI (hiển thị lịch sử)
# ─────────────────────────────────────────────────────────────────────────────

def read_recent_queries(limit: int = 20) -> list:
    """Đọc N câu hỏi gần nhất từ file JSONL hôm nay."""
    _ensure_log_dir()
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(LOG_DIR, f"queries_{date_str}.jsonl")
    if not os.path.exists(log_file):
        return []
    entries = []
    with open(log_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
    return entries[-limit:]


def list_session_files() -> list:
    """Liệt kê tất cả file session log, mới nhất trước."""
    _ensure_log_dir()
    files = [f for f in os.listdir(LOG_DIR) if f.startswith("session_")]
    files.sort(reverse=True)
    return [os.path.join(LOG_DIR, f) for f in files]


if __name__ == "__main__":
    print(f"Log directory: {LOG_DIR}")
    print(f"Recent queries: {read_recent_queries(5)}")
    print(f"Session files: {list_session_files()}")
