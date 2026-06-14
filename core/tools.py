# core/tools.py
import json
from data.signal_knowledge_base import RANDOM_SIGNAL_KB

def _get_knowledge_node(node_id):
    node = RANDOM_SIGNAL_KB["knowledge_nodes"].get(node_id)
    if not node:
        return json.dumps({"error": f"未找到节点 {node_id}"}, ensure_ascii=False)
    result = {"title": node["title"], "chapter": node["chapter"], "core_concept": node["core_concept"],
              "engineering_meaning": node["engineering_meaning"]}
    kb = RANDOM_SIGNAL_KB
    for f_id in node.get("related_formulas", []):
        f = kb["formulas"].get(f_id)
        if f: result.setdefault("formulas", []).append(f)
    for e_id in node.get("related_errors", []):
        e = kb["error_warnings"].get(e_id)
        if e: result.setdefault("error_warnings", []).append(e)
    for c_id in node.get("related_cases", []):
        c = kb["problem_cases"].get(c_id)
        if c: result.setdefault("problem_cases", []).append(c)
    return json.dumps(result, ensure_ascii=False, indent=2)


def _get_glossary(term):
    matches = [g for g in RANDOM_SIGNAL_KB["glossary"] if
               term.lower() in g["symbol"].lower() or term.lower() in g["name"].lower()]
    return json.dumps(matches, ensure_ascii=False, indent=2) if matches else json.dumps(
        {"message": f"未找到术语 {term}"}, ensure_ascii=False)


def _get_problem_case(case_id):
    case = RANDOM_SIGNAL_KB["problem_cases"].get(case_id)
    if not case:
        for cid, c in RANDOM_SIGNAL_KB["problem_cases"].items():
            if case_id.lower() in c["type_name"].lower():
                case = c
                break
    return json.dumps(case, ensure_ascii=False, indent=2) if case else json.dumps({"message": f"未找到题型 {case_id}"},
                                                                                  ensure_ascii=False)


def _get_error_warning(err_id):
    err = RANDOM_SIGNAL_KB["error_warnings"].get(err_id)
    return json.dumps(err, ensure_ascii=False, indent=2) if err else json.dumps({"message": f"未找到错因 {err_id}"},
                                                                                ensure_ascii=False)


def _get_current_signal(signal_context):
    if not signal_context or (not signal_context.get("generated") and not signal_context.get("kalman_run")):
        return json.dumps({"message": "尚未生成信号或运行卡尔曼估计，请引导用户先设置参数运行。"}, ensure_ascii=False)
    
    result = {}
    if signal_context.get("generated"):
        feats = signal_context.get("features") or {}
        result.update({
            "signal_type": signal_context.get("signal_type"),
            "frequency_hz": signal_context.get("freq"),
            "snr_db": signal_context.get("snr_db"),
            "sample_rate": signal_context.get("fs"),
            "bandwidth_hz": signal_context.get("bandwidth"),
            "freq_end_hz": signal_context.get("freq_end"),
            "markov_a": signal_context.get("markov_a"),
            "freq2_hz": signal_context.get("freq2"),
            "features": {
                "mean": feats.get("mean"),
                "variance": feats.get("variance"),
                "std": feats.get("std"),
                "rms": feats.get("rms")
            }
        })
        
    if signal_context.get("filter_run"):
        f_feats = signal_context.get("filter_features") or {}
        result.update({
            "filter_run": True,
            "filter_type": signal_context.get("filter_type"),
            "filter_window_size": signal_context.get("filter_window_size"),
            "filter_cutoff_freq": signal_context.get("filter_cutoff_freq"),
            "filter_features": {
                "mean": f_feats.get("mean"),
                "variance": f_feats.get("variance"),
                "std": f_feats.get("std"),
                "rms": f_feats.get("rms")
            }
        })
        
    if signal_context.get("kalman_run"):
        result.update({
            "kalman_run": True,
            "kalman_q": signal_context.get("kalman_q"),
            "kalman_r": signal_context.get("kalman_r"),
            "kalman_v0": signal_context.get("kalman_v0"),
            "kalman_p_final": signal_context.get("kalman_p_final"),
            "kalman_k1_final": signal_context.get("kalman_k1_final"),
            "kalman_k2_final": signal_context.get("kalman_k2_final")
        })
        
    return json.dumps(result, ensure_ascii=False)


_TOOL_DISPATCH = {
    "get_knowledge_node": lambda args, ctx: _get_knowledge_node(args.get("node_id", "")),
    "get_glossary": lambda args, ctx: _get_glossary(args.get("term", "")),
    "get_problem_case": lambda args, ctx: _get_problem_case(args.get("case_id", "")),
    "get_error_warning": lambda args, ctx: _get_error_warning(args.get("err_id", "")),
    "get_current_signal": lambda args, ctx: _get_current_signal(ctx),
}


def _execute_tool(name, args, signal_context):
    handler = _TOOL_DISPATCH.get(name)
    return handler(args, signal_context) if handler else json.dumps({"error": f"未知工具: {name}"},
                                                                    ensure_ascii=False)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_knowledge_node",
            "description": "获取指定知识节点的完整内容（核心概念、工程意义、关联公式、常见误区）。解释概念时务必调用此工具确保内容准确。",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_id": {"type": "string", "description": "知识节点 ID: KP_CH1_01(广义平稳), KP_CH1_02(维纳-欣钦), KP_CH2_01(白噪声通过线性系统)"}
                },
                "required": ["node_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_glossary",
            "description": "查询术语符号表的定义，如 X(t)、m_X(t)、R_X(t1,t2)、G_X(ω)、WSS 等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "术语符号或名称"}
                },
                "required": ["term"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_problem_case",
            "description": "获取例题/题型卡片，包含题目、解题思路和数学推导步骤。当学生问例题或想练习时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_id": {"type": "string", "description": "题型ID(如 CASE_CH1_01)或题型名称关键词(如'自相关函数'、'功率谱密度')"}
                },
                "required": ["case_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_error_warning",
            "description": "获取常见误区/避坑指南。当学生可能犯错或需要提醒易混淆概念时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "err_id": {"type": "string", "description": "错因 ID，如 ERR_CH1_01(平稳混淆), ERR_CH2_01(积分破坏平稳)"}
                },
                "required": ["err_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_signal",
            "description": "获取当前已生成信号的参数和统计特征。当用户询问当前信号状态或要求分析信号时调用。",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]
