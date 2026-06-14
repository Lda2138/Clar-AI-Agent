# backend/knowledge_routes.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.config import agent, KP_KEYWORD_RULES
from data.signal_knowledge_base import RANDOM_SIGNAL_KB

router = APIRouter()

@router.get("/api/knowledge/node/{node_id}")
def api_get_node(node_id: str):
    nodes = RANDOM_SIGNAL_KB.get("knowledge_nodes", {})
    node = nodes.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"未找到节点 {node_id}")

    result = {
        "title": node["title"],
        "chapter": node["chapter"],
        "core_concept": node["core_concept"],
        "engineering_meaning": node["engineering_meaning"],
        "formulas": [],
        "errors": [],
    }
    for f_id in node.get("related_formulas", []):
        f = RANDOM_SIGNAL_KB.get("formulas", {}).get(f_id)
        if f:
            result["formulas"].append(f)
    for e_id in node.get("related_errors", []):
        e = RANDOM_SIGNAL_KB.get("error_warnings", {}).get(e_id)
        if e:
            result["errors"].append(e)
    return result


@router.get("/api/knowledge/graph")
def api_get_graph():
    syllabus = RANDOM_SIGNAL_KB.get("course_syllabus", {})
    nodes = []
    links = []

    def resolve_kp(topic_name, section_name):
        combined = topic_name + " " + section_name
        for keywords, kp_id in KP_KEYWORD_RULES:
            if any(kw in combined for kw in keywords):
                return kp_id
        return None

    chapter_idx = 0
    for chapter_name, sections in syllabus.items():
        chapter_short = chapter_name.split("_")[1] if "_" in chapter_name else chapter_name
        chapter_id = f"ch_{chapter_idx}"
        nodes.append({
            "id": chapter_id, "name": chapter_short,
            "symbolSize": 38, "category": 0,
            "itemStyle": {"color": "#4c85cc"},
            "node_type": "chapter",
            "chapter": chapter_short,
        })
        for section_name, topics in sections.items():
            section_id = f"{chapter_id}_{section_name}"
            nodes.append({
                "id": section_id, "name": section_name,
                "symbolSize": 26, "category": 1,
                "itemStyle": {"color": "#356099"},
                "node_type": "section",
                "chapter": chapter_short,
                "section": section_name,
                "topics": topics,
            })
            links.append({"source": chapter_id, "target": section_id})
            for topic in topics:
                topic_id = f"{section_id}_{topic}"
                color = "#C95C16" if any(kw in topic for kw in ["平稳", "维纳", "白噪声", "正态"]) else "#E47732"
                node_data = {
                    "id": topic_id, "name": topic,
                    "symbolSize": 18, "category": 2,
                    "itemStyle": {"color": color},
                    "node_type": "topic",
                    "chapter": chapter_short,
                    "section": section_name,
                }
                kp_id = resolve_kp(topic, section_name)
                if kp_id:
                    node_data["kp_node_id"] = kp_id
                nodes.append(node_data)
                links.append({"source": section_id, "target": topic_id})
        chapter_idx += 1

    return {"nodes": nodes, "links": links}


@router.get("/api/knowledge/quick-questions/{node_id}")
def api_quick_questions(node_id: str, count: int = 3):
    nodes = RANDOM_SIGNAL_KB.get("knowledge_nodes", {})
    node = nodes.get(node_id)

    fallback = [
        f"请详细解释「{node['title'] if node else '该知识点'}」的核心概念是什么？",
        "这个概念在工程实践中有哪些典型应用场景？",
        "能否用 Python 代码演示该概念的仿真验证过程？",
    ]

    if not node:
        return JSONResponse(
            {"code": 404, "questions": fallback},
            headers={"Cache-Control": "no-store"},
        )

    if agent is None:
        return JSONResponse(
            {"code": 503, "questions": fallback},
            headers={"Cache-Control": "no-store"},
        )

    try:
        questions = agent.get_smart_follow_ups(node["title"], node["core_concept"], node.get("engineering_meaning", ""), count)
        if questions:
            return JSONResponse(
                {"code": 200, "questions": questions},
                headers={"Cache-Control": "no-store"},
            )
    except Exception:
        pass

    return JSONResponse(
        {"code": 200, "questions": fallback},
        headers={"Cache-Control": "no-store"},
    )
