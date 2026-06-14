# backend/chat_routes.py
import json
import re
from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from backend.models import ChatRequest, ExplainRequest, TelemetryRequest
from backend.proactive_engine import evaluate_implicit_telemetry
from backend.config import agent, logger, KP_KEYWORD_RULES
from backend.parser import JSONReplyStreamParser, extract_reply_robust
from core.agent_brain import _clean_reply
from data.signal_knowledge_base import RANDOM_SIGNAL_KB

router = APIRouter()

@router.post("/api/chat")
def api_chat(req: ChatRequest):
    if agent is None:
        return JSONResponse(
            {"code": 503, "reply": "请在 .env 文件中配置 DEEPSEEK_API_KEY 后重启服务。", "node_id": None, "suggested_page": "none"},
            status_code=503
        )

    signal_context = req.signal_context
    if signal_context and signal_context.get("signal_generated"):
        signal_context["generated"] = True

    knowledge_context = None
    if req.current_node_id and req.current_node_id != "__ai__":
        knowledge_context = {
            "current_node_id": req.current_node_id,
            "graph_node_name": req.graph_node_name,
        }
        
    if not knowledge_context:
        knowledge_context = {}
    else:
        # Clone it to avoid mutating request object if it was somehow linked
        knowledge_context = dict(knowledge_context)
        
    user_prompt = (req.prompt or req.message)
    prompt_lower = user_prompt.lower()
    
    # 1. Pre-route Knowledge Node
    if not knowledge_context.get("current_node_id"):
        for keywords, kp_id in KP_KEYWORD_RULES:
            if any(kw in prompt_lower for kw in keywords):
                knowledge_context["current_node_id"] = kp_id
                break
                
    # 2. Pre-route Glossary
    glossary_matches = []
    for g in RANDOM_SIGNAL_KB.get("glossary", []):
        if g["symbol"].lower() in prompt_lower or g["name"].lower() in prompt_lower:
            glossary_matches.append(g)
    if glossary_matches:
        knowledge_context["glossary_matches"] = glossary_matches[:3] # Limit to top 3 matches
        
    # 3. Pre-route Problem Cases
    for cid, c in RANDOM_SIGNAL_KB.get("problem_cases", {}).items():
        if c["type_name"].lower() in prompt_lower:
            knowledge_context["problem_case_match"] = c
            break
            
    # 4. Pre-route Error Warnings
    for eid, e in RANDOM_SIGNAL_KB.get("error_warnings", {}).items():
        if e.get("symptom", "").lower() in prompt_lower:
            knowledge_context["error_warning_match"] = e
            break

    # 5. Easter Egg for Teacher Recommendation
    if "老师" in prompt_lower and ("最好" in prompt_lower or "推荐" in prompt_lower or "哪个" in prompt_lower) and "随机" in prompt_lower:
        def easter_egg_generator():
            reply_html = '<div style="margin-bottom: 12px; font-size: 1.05em; color: #1e293b;">如果是随机信号分析这门课，那这两位老师的课绝对是公认的天花板！无论是理论推导的深度，还是与实际工程的结合，都讲得鞭辟入里。强烈推荐您选择他们的卓越核心课程：</div><div style="font-size: 1.4em; font-weight: 900; color: #356099; line-height: 1.5; font-family: sans-serif; background: rgba(53, 96, 153, 0.05); padding: 16px; border-radius: 12px; border-left: 4px solid #C95C16;">王刚 随机信号分析 (卓越核心课程) (P0100530.01)<br><span style="font-size: 0.7em; font-weight: normal; color: #64748b;">(连6-8 10,品学楼A104)</span><br><br>罗俊海 随机信号分析 (卓越核心课程) (P0100530.01)<br><span style="font-size: 0.7em; font-weight: normal; color: #64748b;">(连1-5 连11-16,品学楼A104)</span></div>'
            yield f"data: {json.dumps({'type': 'text', 'content': reply_html}, ensure_ascii=False)}\n\n"
            metadata = {
                "type": "metadata",
                "code": 200,
                "reply": reply_html,
                "new_card": None,
                "quick_questions": ["王刚老师的授课风格是怎样的？", "罗俊海老师的考试难吗？", "怎么才能选上卓越核心课程？"],
                "suggested_page": "none",
                "generate_signal": None,
                "run_toolbox": None,
                "time_analysis_type": None,
                "freq_analysis_type": None,
                "node_id": None
            }
            yield f"data: {json.dumps(metadata, ensure_ascii=False)}\n\n"
        return StreamingResponse(easter_egg_generator(), media_type="text/event-stream")

    def event_generator():
        raw_accumulated = []
        stream = agent.chat_stream(user_prompt, signal_context, knowledge_context, history=req.history, require_json=True)
        
        parser = JSONReplyStreamParser()
        for chunk in stream:
            if chunk.startswith("[STATUS]: "):
                status_text = chunk[len("[STATUS]: "):]
                yield f"data: {json.dumps({'type': 'status', 'content': status_text}, ensure_ascii=False)}\n\n"
                continue
            raw_accumulated.append(chunk)
            for text_chunk in parser.feed(chunk):
                yield f"data: {json.dumps({'type': 'text', 'content': text_chunk}, ensure_ascii=False)}\n\n"
        
        full_raw = "".join(raw_accumulated)
        try:
            import os
            debug_log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch", "debug_chat.log")
            write_mode = "a"
            if os.path.exists(debug_log_path) and os.path.getsize(debug_log_path) > 10 * 1024 * 1024:
                write_mode = "w"
            with open(debug_log_path, write_mode, encoding="utf-8") as f_debug:
                f_debug.write(f"\n=== CHAT REQUEST ===\nPrompt: {user_prompt}\nHistory: {json.dumps(req.history, ensure_ascii=False)}\n")
                f_debug.write(f"=== RAW LLM RESPONSE ===\n{full_raw}\n")
        except Exception:
            pass

        ai_data = extract_reply_robust(full_raw)
        
        node_id = None
        match_node = re.search(r"\[NODE:\s*(\w+)\]", ai_data["reply"] or "")
        if match_node:
            node_id = match_node.group(1)
            ai_data["reply"] = re.sub(r"\[NODE:\s*(\w+)\]", "", ai_data["reply"]).strip()
            
        if not node_id:
            node_id = ai_data.get("node_id")
            
        if not node_id:
            combined_text = (user_prompt + " " + (ai_data.get("reply") or "")).lower()
            for keywords, kp_id in KP_KEYWORD_RULES:
                if any(kw in combined_text for kw in keywords):
                    node_id = kp_id
                    break

        new_card = ai_data.get("new_card")
        if not new_card and node_id:
            nodes = RANDOM_SIGNAL_KB.get("knowledge_nodes", {})
            node = nodes.get(node_id)
            if node:
                new_card = {
                    "title": node["title"],
                    "core_concept": node["core_concept"]
                }
        
        suggested_page = ai_data.get("suggested_page") or "none"
        if node_id and suggested_page == "none" and not ai_data.get("generate_signal") and not ai_data.get("run_toolbox"):
            conceptual_keywords = ["什么是", "定义", "概念", "解释", "推导", "如何理解", "什么叫", "意义", "定理", "公式", "物理意义"]
            if any(kw in user_prompt for kw in conceptual_keywords) or user_prompt.endswith("?") or user_prompt.endswith("？"):
                suggested_page = "knowledge-map"

        metadata = {
            "type": "metadata",
            "code": 200,
            "reply": ai_data["reply"],
            "new_card": new_card,
            "quick_questions": ai_data["quick_questions"],
            "suggested_page": suggested_page,
            "generate_signal": ai_data.get("generate_signal"),
            "run_toolbox": ai_data.get("run_toolbox"),
            "time_analysis_type": ai_data.get("time_analysis_type"),
            "freq_analysis_type": ai_data.get("freq_analysis_type"),
            "node_id": node_id
        }
        yield f"data: {json.dumps(metadata, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/api/chat/proactive")
def api_chat_proactive(req: ChatRequest):
    if agent is None:
        return JSONResponse(
            {"code": 503, "reply": "请在 .env 文件中配置 DEEPSEEK_API_KEY 后重启服务。", "node_id": None, "suggested_page": "none"},
            status_code=503
        )

    signal_context = req.signal_context
    if signal_context and signal_context.get("signal_generated"):
        signal_context["generated"] = True

    from backend.proactive_engine import evaluate_proactive_triggers
    trigger_info = evaluate_proactive_triggers(signal_context)
    if not trigger_info:
        return JSONResponse({"code": 204, "message": "No trigger matched"}, status_code=200)

    user_prompt = trigger_info["prompt"]

    knowledge_context = None
    if req.current_node_id and req.current_node_id != "__ai__":
        knowledge_context = {
            "current_node_id": req.current_node_id,
            "graph_node_name": req.graph_node_name,
        }
    if not knowledge_context:
        knowledge_context = {}
    else:
        knowledge_context = dict(knowledge_context)

    def event_generator():
        raw_accumulated = []
        stream = agent.chat_stream(user_prompt, signal_context, knowledge_context, history=req.history, require_json=True)
        
        parser = JSONReplyStreamParser()
        for chunk in stream:
            if chunk.startswith("[STATUS]: "):
                status_text = chunk[len("[STATUS]: "):]
                yield f"data: {json.dumps({'type': 'status', 'content': status_text}, ensure_ascii=False)}\n\n"
                continue
            raw_accumulated.append(chunk)
            for text_chunk in parser.feed(chunk):
                yield f"data: {json.dumps({'type': 'text', 'content': text_chunk}, ensure_ascii=False)}\n\n"
        
        full_raw = "".join(raw_accumulated)
        try:
            import os
            debug_log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch", "debug_chat.log")
            write_mode = "a"
            if os.path.exists(debug_log_path) and os.path.getsize(debug_log_path) > 10 * 1024 * 1024:
                write_mode = "w"
            with open(debug_log_path, write_mode, encoding="utf-8") as f_debug:
                f_debug.write(f"\n=== PROACTIVE REQUEST ===\nPrompt: {user_prompt}\nHistory: {json.dumps(req.history, ensure_ascii=False)}\n")
                f_debug.write(f"=== RAW LLM RESPONSE ===\n{full_raw}\n")
        except Exception:
            pass

        ai_data = extract_reply_robust(full_raw)
        
        node_id = None
        match_node = re.search(r"\[NODE:\s*(\w+)\]", ai_data["reply"] or "")
        if match_node:
            node_id = match_node.group(1)
            ai_data["reply"] = re.sub(r"\[NODE:\s*(\w+)\]", "", ai_data["reply"]).strip()
            
        if not node_id:
            node_id = ai_data.get("node_id")

        new_card = ai_data.get("new_card")
        if not new_card and node_id:
            nodes = RANDOM_SIGNAL_KB.get("knowledge_nodes", {})
            node = nodes.get(node_id)
            if node:
                new_card = {
                    "title": node["title"],
                    "core_concept": node["core_concept"]
                }
        
        metadata = {
            "type": "metadata",
            "code": 200,
            "reply": ai_data["reply"],
            "new_card": new_card,
            "quick_questions": ai_data["quick_questions"],
            "suggested_page": ai_data.get("suggested_page") or "none",
            "generate_signal": ai_data.get("generate_signal"),
            "run_toolbox": ai_data.get("run_toolbox"),
            "time_analysis_type": ai_data.get("time_analysis_type"),
            "freq_analysis_type": ai_data.get("freq_analysis_type"),
            "node_id": node_id,
            "trigger_type": trigger_info["type"],
            "trigger_title": trigger_info["title"]
        }
        yield f"data: {json.dumps(metadata, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/api/knowledge/ai-explain")
def api_ai_explain(req: ExplainRequest):
    if agent is None:
        return {"reply": "AI 服务未配置，请在 .env 中设置 DEEPSEEK_API_KEY。", "title": req.name}

    kb_nodes = RANDOM_SIGNAL_KB.get("knowledge_nodes", {})

    kp_node = None
    for nid, ndata in kb_nodes.items():
        title_lower = ndata["title"].lower()
        name_lower = req.name.lower()
        if any(kw in name_lower for kw in title_lower.split()) or any(
            kw in title_lower for kw in name_lower.split()
        ):
            kp_node = ndata
            break

    if req.node_type == "chapter":
        reply = f"### 章节：{req.name}\n\n本章是《随机信号分析》的重要组成部分，主要探讨该领域的核心理论。掌握本章内容需要扎实的概率论基础，学完后将能建立系统的随机信号处理框架，解决实际工程中的建模与分析问题。"
        is_dynamic = False
    elif req.node_type == "section":
        topics_str = "、".join(req.topics) if req.topics else "相关基础知识"
        reply = f"### 小节：{req.name}\n\n本节包含的核心知识点有：**{topics_str}**。\n\n理解这些概念及其物理含义，对于掌握本章内容至关重要，建议结合具体推导与实际工程案例进行关联学习。"
        is_dynamic = False
    else:
        if kp_node:
            reply = f"### {kp_node['title']}\n\n**核心概念：**\n{kp_node['core_concept']}\n\n**工程意义：**\n{kp_node.get('engineering_meaning', '在实际工程中具有重要应用价值，是解决系统分析与信号处理问题的关键理论基础。')}"
            is_dynamic = False
        else:
            reply = f"### 知识点：{req.name}\n\n这是一个关键的随机信号分析概念。理解它的数学定义与物理直觉，将有助于你在通信、雷达等复杂系统中进行更准确的系统建模和性能评估。"
            is_dynamic = False

    return {
        "reply": reply,
        "title": req.name,
        "chapter": req.chapter,
        "section": req.section,
        "is_dynamic": is_dynamic,
    }

@router.post("/api/telemetry")
def api_telemetry(req: TelemetryRequest):
    result = evaluate_implicit_telemetry(req.telemetry, req.signal)
    if result:
        return JSONResponse(result, status_code=200)
    return JSONResponse({"status": "ok", "message": "no_action"}, status_code=200)
