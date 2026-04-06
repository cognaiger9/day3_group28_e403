"""
app.py - Flask Web UI for Travel Advisor AI
Group 28 - Day 3 Lab

Chay: python app.py
Truy cap: http://localhost:5000
"""

import os
import threading
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

from chatbot import call_chatbot
from agent import TravelReActAgent
from tools import TOOLS
from log_manager import log_query, read_recent_queries

app = Flask(__name__)

# Shared agent instance (thread-safe per request via new instance)
_TOOLS = TOOLS


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html",
                           provider=os.getenv("DEFAULT_PROVIDER", "openai"),
                           model=os.getenv("DEFAULT_MODEL", "gpt-4o"))


@app.route("/api/chatbot", methods=["POST"])
def api_chatbot():
    data     = request.get_json(force=True)
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "question is required"}), 400
    result = call_chatbot(question)
    # Log partial (agent side will be None for now)
    return jsonify(result)


@app.route("/api/agent", methods=["POST"])
def api_agent():
    data     = request.get_json(force=True)
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "question is required"}), 400
    agent  = TravelReActAgent(tools=_TOOLS)
    result = agent.run_with_meta(question)
    # Build a clean trace for the frontend (structured steps)
    result["frontend_trace"] = _build_frontend_trace(result["trace"])
    return jsonify(result)


@app.route("/api/ask", methods=["POST"])
def api_ask():
    """
    Gọi cả 2 hệ thống song song bằng threading.
    Returns combined result + saves to log.
    """
    data     = request.get_json(force=True)
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "question is required"}), 400

    chatbot_result = {}
    agent_result   = {}
    errors         = {}

    def run_chatbot():
        try:
            chatbot_result.update(call_chatbot(question))
        except Exception as e:
            errors["chatbot"] = str(e)

    def run_agent():
        try:
            ag = TravelReActAgent(tools=_TOOLS)
            r  = ag.run_with_meta(question)
            r["frontend_trace"] = _build_frontend_trace(r["trace"])
            agent_result.update(r)
        except Exception as e:
            errors["agent"] = str(e)

    t1 = threading.Thread(target=run_chatbot)
    t2 = threading.Thread(target=run_agent)
    t1.start(); t2.start()
    t1.join();  t2.join()

    # Save to log
    try:
        log_query(
            question=question,
            chatbot_result=chatbot_result or None,
            agent_result=agent_result or None,
            source="web",
        )
    except Exception:
        pass

    return jsonify({
        "question": question,
        "chatbot":  chatbot_result,
        "agent":    agent_result,
        "errors":   errors,
    })


@app.route("/api/history", methods=["GET"])
def api_history():
    """Trả về N câu hỏi gần nhất."""
    limit = int(request.args.get("limit", 10))
    return jsonify(read_recent_queries(limit))


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _build_frontend_trace(trace_log: list) -> list:
    """
    Chuyển trace_log thành danh sách steps dễ render trên UI.
    Mỗi step = { step_num, thought, action, observation, tokens, latency_ms }
    """
    steps  = []
    current_step = {}
    step_num = 0

    for entry in trace_log:
        ev = entry.get("event")

        if ev == "ITERATION_START":
            if current_step:
                steps.append(current_step)
            step_num = entry.get("step", step_num + 1)
            current_step = {"step": step_num, "thought": "", "action": None, "observation": None,
                            "tokens": None, "latency_ms": None}

        elif ev == "LLM_RESPONSE":
            output = entry.get("output", "")
            # Extract Thought
            thought_m = __import__("re").search(r"Thought:\s*(.+?)(?=Action:|Final Answer:|$)",
                                                 output, __import__("re").DOTALL | __import__("re").IGNORECASE)
            if thought_m:
                current_step["thought"] = thought_m.group(1).strip()
            # Extract Action line
            action_m = __import__("re").search(r"Action:\s*(.+)", output, __import__("re").IGNORECASE)
            if action_m:
                current_step["action_text"] = action_m.group(1).strip()
            current_step["tokens"]     = entry.get("tokens")
            current_step["latency_ms"] = entry.get("latency_ms")

        elif ev == "TOOL_CALL":
            current_step["action"] = {
                "tool": entry.get("tool"),
                "args": entry.get("args"),
            }
        elif ev == "TOOL_RESULT":
            current_step["observation"] = entry.get("result")
            current_step["tool_latency_ms"] = entry.get("latency_ms")

        elif ev == "FINAL_ANSWER":
            if current_step:
                # Extract Final Answer from last LLM_RESPONSE
                current_step["final_answer"] = entry.get("answer")
                steps.append(current_step)
                current_step = {}

        elif ev == "FALLBACK_TRIGGERED":
            if current_step:
                current_step["fallback_reason"] = entry.get("reason")
                steps.append(current_step)
                current_step = {}
            steps.append({"step": "FALLBACK", "reason": entry.get("reason")})

    if current_step:
        steps.append(current_step)

    return steps


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    provider = os.getenv("DEFAULT_PROVIDER", "openai")
    model    = os.getenv("DEFAULT_MODEL", "gpt-4o")
    print(f"Travel Advisor AI - Web UI")
    print(f"Provider: {provider} | Model: {model}")
    print(f"URL: http://localhost:5000")
    app.run(debug=True, port=5000, threaded=True)
