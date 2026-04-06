"""
run_demo.py - Chay toan bo 5 test cases: Chatbot vs ReAct Agent
Group 28 - Day 3 Lab

Chay: python -X utf8 run_demo.py
Log luu tai: Day3_group28/log/
"""

import os
import sys
import time

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

from chatbot import call_chatbot
from agent import TravelReActAgent
from tools import TOOLS
from log_manager import log_query, log_session, LOG_DIR

# ─────────────────────────────────────────────────────────────────────────────
# 5 TEST CASES
# ─────────────────────────────────────────────────────────────────────────────

TEST_CASES = [
    {
        "id": "TC-01",
        "label": "Chatbot thang - Kien thuc chung",
        "question": "Toi so bi say tau xe, co meo gi de di du lich de chiu hon khong?",
    },
    {
        "id": "TC-02",
        "label": "Chatbot thang - Van hoa dia phuong",
        "question": "Lan dau di Nhat, toi can biet nhung phong tuc va quy tac lich su nao?",
    },
    {
        "id": "TC-03",
        "label": "Agent thang - Thoi tiet cu the",
        "question": "Toi muon di Hoi An tuan nay. Thoi tiet the nao? Nen mac gi?",
    },
    {
        "id": "TC-04",
        "label": "Agent thang - Multi-step planning",
        "question": (
            "Toi muon di Da Nang 4 ngay de tam bien va vui choi. "
            "Thoi tiet ra sao va nen di dau? "
            "Uoc tinh chi phi cho 2 nguoi di kieu binh dan?"
        ),
    },
    {
        "id": "TC-05",
        "label": "Edge Case - Dia diem khong ton tai",
        "question": "Toi muon di tham thanh pho Atlantis huyen thoai. Thoi tiet the nao va co gi vui choi khong?",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def run_all_tests(run_chatbot: bool = True, run_agent: bool = True):
    provider = os.getenv("DEFAULT_PROVIDER", "openai")
    model    = os.getenv("DEFAULT_MODEL", "gpt-4o")
    agent    = TravelReActAgent(tools=TOOLS) if run_agent else None

    print("=" * 70)
    print(f"  DEMO: Chatbot Baseline vs ReAct Agent - Group 28")
    print(f"  Provider: {provider} | Model: {model}")
    print(f"  Log dir: {LOG_DIR}")
    print("=" * 70)

    session_results = []

    for tc in TEST_CASES:
        print(f"\n\n{'#'*70}")
        print(f"  {tc['id']} | {tc['label']}")
        print(f"  Q: {tc['question'][:80]}{'...' if len(tc['question']) > 80 else ''}")
        print(f"{'#'*70}")

        chatbot_result = agent_result = None

        # ── Chatbot ──────────────────────────────────────────────────────────
        if run_chatbot:
            print(f"\n{'-'*35}")
            print("  [CHATBOT BASELINE]")
            print(f"{'-'*35}")
            chatbot_result = call_chatbot(tc["question"])
            print(chatbot_result["answer"])
            print(f"\n  [tokens={chatbot_result['tokens']['total']} | {chatbot_result['latency_ms']}ms | {chatbot_result['model']}]")

        # ── Agent ─────────────────────────────────────────────────────────────
        if run_agent:
            print(f"\n{'-'*35}")
            print("  [REACT AGENT]")
            print(f"{'-'*35}")
            agent_result = agent.run_with_meta(tc["question"])
            print(f"\n[Agent] Final Answer:\n{agent_result['answer']}")
            print(
                f"\n  [tokens={agent_result['tokens']['total']} | "
                f"wall={agent_result['latency_ms']}ms | "
                f"llm={agent_result['llm_latency_ms']}ms | "
                f"steps={agent_result['iterations']} | "
                f"tools={len(agent_result['tool_calls'])} | "
                f"model={agent_result['model']}]"
            )
            if agent_result["fallback_used"]:
                print("  [!] FALLBACK MODE was activated")
            agent.print_trace_summary()

        # ── Save query log ────────────────────────────────────────────────────
        log_file = log_query(
            question=tc["question"],
            chatbot_result=chatbot_result,
            agent_result=agent_result,
            source="run_demo",
            test_case_id=tc["id"],
        )

        session_results.append({
            "test_case_id": tc["id"],
            "label":        tc["label"],
            "question":     tc["question"],
            "chatbot":      {
                "answer":     chatbot_result.get("answer", "") if chatbot_result else None,
                "tokens":     chatbot_result.get("tokens", {}) if chatbot_result else {},
                "latency_ms": chatbot_result.get("latency_ms", 0) if chatbot_result else 0,
                "model":      chatbot_result.get("model", "") if chatbot_result else "",
            } if chatbot_result else None,
            "agent": {
                "answer":        agent_result.get("answer", "") if agent_result else None,
                "tokens":        agent_result.get("tokens", {}) if agent_result else {},
                "latency_ms":    agent_result.get("latency_ms", 0) if agent_result else 0,
                "llm_latency_ms": agent_result.get("llm_latency_ms", 0) if agent_result else 0,
                "iterations":    agent_result.get("iterations", 0) if agent_result else 0,
                "tool_calls":    agent_result.get("tool_calls", []) if agent_result else [],
                "fallback_used": agent_result.get("fallback_used", False) if agent_result else False,
                "model":         agent_result.get("model", "") if agent_result else "",
            } if agent_result else None,
        })

    # ── Session summary ───────────────────────────────────────────────────────
    session_file = log_session(session_results)

    print(f"\n\n{'='*70}")
    print("  KET QUA TONG KET")
    print(f"{'='*70}")
    print(f"  {'ID':<8} {'Label':<38} {'T-Chatbot':>10} {'T-Agent':>10}")
    print(f"  {'-'*8} {'-'*38} {'-'*10} {'-'*10}")
    for r in session_results:
        c_lat = r["chatbot"]["latency_ms"] if r["chatbot"] else 0
        a_lat = r["agent"]["latency_ms"]   if r["agent"]   else 0
        print(f"  {r['test_case_id']:<8} {r['label'][:38]:<38} {c_lat:>9}ms {a_lat:>9}ms")

    print(f"\n  Query log : {os.path.join(LOG_DIR, 'queries_*.jsonl')}")
    print(f"  Session   : {session_file}")
    print(f"\n  Chay web UI: python app.py  ->  http://localhost:5000\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    run_chatbot_flag = "agent-only"   not in args
    run_agent_flag   = "chatbot-only" not in args
    run_all_tests(run_chatbot=run_chatbot_flag, run_agent=run_agent_flag)
