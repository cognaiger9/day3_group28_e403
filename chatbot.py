"""
chatbot.py - Travel Advisor Chatbot Baseline
Group 28 - Day 3 Lab

Chatbot TU VAN DU LICH don gian: chi dung LLM, KHONG co tool.
Muc dich: lam baseline de so sanh voi ReAct Agent.
"""

import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Ban la TravelBot - chuyen gia tu van du lich Viet Nam va quoc te voi 10 nam kinh nghiem.

VAI TRO:
- Tu van lich trinh du lich phu hop voi nhu cau va ngan sach.
- Chia se kinh nghiem, meo du lich va van hoa dia phuong.
- Goi y am thuc, dia diem tham quan va hoat dong hap dan.
- Giai dap thac mac ve thu tuc, giay to, an toan khi du lich.

PHONG CACH TRA LOI:
- Than thien, nhiet tinh nhu mot nguoi ban am hieu ve du lich.
- Cau tra loi co cau truc ro rang, dung gach dau dong khi liet ke.
- Luon hoi lai neu thong tin chua du (thoi gian, ngan sach, so thich).

GIOI HAN QUAN TRONG:
- Ban KHONG co quyen truy cap thong tin thoi tiet thuc te.
- Ban KHONG co quyen tra cuu gia ve, lich bay thoi gian thuc.
- Ban KHONG the book khach san hay dat tour.
- Khi duoc hoi thong tin thoi gian thuc, hay noi ro gioi han nay va
  goi y nguoi dung kiem tra truc tiep qua cac app/website uy tin.

NGON NGU: Tra loi bang tieng Viet tru khi khach hang dung tieng Anh.
"""

# ─────────────────────────────────────────────────────────────────────────────
# LLM CALLER — trả về dict đầy đủ
# ─────────────────────────────────────────────────────────────────────────────

def call_chatbot(question: str) -> Dict[str, Any]:
    """
    Gọi LLM với system prompt tư vấn du lịch (không có tool).
    Returns:
        {
          "answer":     str,
          "tokens":     {"prompt": int, "completion": int, "total": int},
          "latency_ms": int,
          "model":      str,
          "provider":   str,
          "timestamp":  str,
          "error":      str | None,
        }
    """
    provider  = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        if provider == "openai":
            return _call_openai(question, timestamp)
        elif provider == "google":
            return _call_gemini(question, timestamp)
        else:
            raise ValueError(f"Provider khong ho tro: {provider}")
    except Exception as e:
        return {
            "answer":    f"[LOI] {e}",
            "tokens":    {"prompt": 0, "completion": 0, "total": 0},
            "latency_ms": 0,
            "model":     os.getenv("DEFAULT_MODEL", "gpt-4o"),
            "provider":  provider,
            "timestamp": timestamp,
            "error":     str(e),
        }


def _call_openai(question: str, timestamp: str) -> Dict[str, Any]:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model  = os.getenv("DEFAULT_MODEL", "gpt-4o")
    t0 = time.time()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": question},
        ],
        temperature=0.7,
    )
    latency_ms = int((time.time() - t0) * 1000)
    usage = response.usage
    return {
        "answer":    response.choices[0].message.content,
        "tokens": {
            "prompt":     usage.prompt_tokens,
            "completion": usage.completion_tokens,
            "total":      usage.total_tokens,
        },
        "latency_ms": latency_ms,
        "model":      model,
        "provider":   "openai",
        "timestamp":  timestamp,
        "error":      None,
    }


def _call_gemini(question: str, timestamp: str) -> Dict[str, Any]:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model_name = os.getenv("DEFAULT_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(model_name, system_instruction=SYSTEM_PROMPT)
    t0 = time.time()
    response = model.generate_content(question)
    latency_ms = int((time.time() - t0) * 1000)
    usage_meta = getattr(response, "usage_metadata", None)
    return {
        "answer":    response.text,
        "tokens": {
            "prompt":     getattr(usage_meta, "prompt_token_count", 0),
            "completion": getattr(usage_meta, "candidates_token_count", 0),
            "total":      getattr(usage_meta, "total_token_count", 0),
        },
        "latency_ms": latency_ms,
        "model":      model_name,
        "provider":   "google",
        "timestamp":  timestamp,
        "error":      None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# BACKWARD COMPAT — dùng bởi run_demo.py cũ
# ─────────────────────────────────────────────────────────────────────────────

def run_single(question: str) -> str:
    return call_chatbot(question)["answer"]


# ─────────────────────────────────────────────────────────────────────────────
# INTERACTIVE
# ─────────────────────────────────────────────────────────────────────────────

def run_chat():
    provider = os.getenv("DEFAULT_PROVIDER", "openai")
    model    = os.getenv("DEFAULT_MODEL", "gpt-4o")
    print("=" * 60)
    print(f"   TravelBot - Baseline (khong co tool)")
    print(f"   Provider: {provider} | Model: {model}")
    print("   (Go 'exit' de thoat)")
    print("=" * 60)

    while True:
        try:
            user_input = input("\nBan: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input: continue
        if user_input.lower() in ("exit", "quit"): break
        r = call_chatbot(user_input)
        print(f"\nTravelBot: {r['answer']}")
        print(f"[tokens={r['tokens']['total']} | {r['latency_ms']}ms | {r['model']}]")


if __name__ == "__main__":
    run_chat()
