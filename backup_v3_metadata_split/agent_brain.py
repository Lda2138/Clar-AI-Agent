# core/agent_brain.py
import os
import re
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger("signal_agent")

_RE_THINKING = re.compile(
    r'(?:好的[，,]?\s*)?(?:现在\s*)?(?:让我们?|我来|咱们)\s*(?:再|先)?\s*(?:查|查看|调|搜|找|看|调用|了解)\s*一下[^。！？\n]*[。！？]?')
_RE_XML_TAGS = re.compile(
    r"<\s*[!/]?\s*(function_calls|function_call|invoke|parameter)[^>]*>.*?<\s*/\s*(function_calls|function_call|invoke)\s*>|<\s*(function_calls|function_call|invoke|parameter)[^>]*/?>",
    flags=re.DOTALL)
_RE_INVISIBLE = re.compile(r"[​-‍﻿­‎‏]")
_RE_EMOJI = re.compile(
    r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0000FE00-\U0000FE0F\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002300-\U000023FF\U00002B50\U00002764\U00002714\U00002705\U0000200D\U000020E3\U0001F004\U0001F0CF]",
    flags=re.UNICODE)
_RE_EMPTY_XML = re.compile(r'^\s*(<[^>]*>)?\s*$')
_RE_NODE = re.compile(r"\[NODE:\s*(\w+)\]")


def _load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    load_dotenv(env_path)


def _get_knowledge_node(node_id):
    from data.signal_knowledge_base import RANDOM_SIGNAL_KB
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
    from data.signal_knowledge_base import RANDOM_SIGNAL_KB
    matches = [g for g in RANDOM_SIGNAL_KB["glossary"] if
               term.lower() in g["symbol"].lower() or term.lower() in g["name"].lower()]
    return json.dumps(matches, ensure_ascii=False, indent=2) if matches else json.dumps(
        {"message": f"未找到术语 {term}"}, ensure_ascii=False)


def _get_problem_case(case_id):
    from data.signal_knowledge_base import RANDOM_SIGNAL_KB
    case = RANDOM_SIGNAL_KB["problem_cases"].get(case_id)
    if not case:
        for cid, c in RANDOM_SIGNAL_KB["problem_cases"].items():
            if case_id.lower() in c["type_name"].lower():
                case = c;
                break
    return json.dumps(case, ensure_ascii=False, indent=2) if case else json.dumps({"message": f"未找到题型 {case_id}"},
                                                                                  ensure_ascii=False)


def _get_error_warning(err_id):
    from data.signal_knowledge_base import RANDOM_SIGNAL_KB
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


def _clean_reply(text):
    if not text: return ""
    text = _RE_XML_TAGS.sub("", text)
    text = _RE_THINKING.sub("", text)
    text = _RE_INVISIBLE.sub("", text)
    text = _RE_EMOJI.sub("", text)
    return text.strip()


TOOLS = [
    {"type": "function", "function": {"name": "get_knowledge_node",
                                      "description": "获取指定知识节点的核心概念等。解释概念时务必调用此工具确保准确。",
                                      "parameters": {"type": "object", "properties": {"node_id": {"type": "string"}},
                                                     "required": ["node_id"]}}},
    {"type": "function", "function": {"name": "get_glossary", "description": "查询术语符号表的定义。",
                                      "parameters": {"type": "object", "properties": {"term": {"type": "string"}},
                                                     "required": ["term"]}}},
    {"type": "function", "function": {"name": "get_problem_case", "description": "获取例题/题型卡片。",
                                      "parameters": {"type": "object", "properties": {"case_id": {"type": "string"}},
                                                     "required": ["case_id"]}}},
    {"type": "function", "function": {"name": "get_error_warning", "description": "获取常见误区。",
                                      "parameters": {"type": "object", "properties": {"err_id": {"type": "string"}},
                                                     "required": ["err_id"]}}},
    {"type": "function", "function": {"name": "get_current_signal", "description": "获取当前已生成信号的参数和特征。",
                                      "parameters": {"type": "object", "properties": {}, "required": []}}}
]


def _build_system_prompt(signal_context, knowledge_context=None, require_json=False, ui_mode="classic"):
    from data.signal_knowledge_base import RANDOM_SIGNAL_KB
    kb = RANDOM_SIGNAL_KB
    nodes = kb["knowledge_nodes"]
    node_brief = "、".join(f"{nid}({info['title']})" for nid, info in nodes.items())

    signal_block = ""
    if signal_context and signal_context.get("generated"):
        feats = signal_context.get("features") or {}
        signal_block = (
            f"\n\n## 当前信号\n"
            f"类型: {signal_context.get('signal_type', '?')}, "
            f"频率: {signal_context.get('freq', '?')} Hz, "
            f"SNR: {signal_context.get('snr_db', '?')} dB, "
            f"采样率: {signal_context.get('fs', '?')} Hz\n"
            f"统计特征: 均值={feats.get('mean', '?')}, 方差={feats.get('variance', '?')}, RMS={feats.get('rms', '?')}"
        )

    filter_block = ""
    if signal_context and signal_context.get("filter_run"):
        filter_type_map = {
            "moving_average": "滑动平均滤波",
            "rc_lowpass": "RC一阶低通滤波",
            "wiener": "维纳滤波"
        }
        f_type = signal_context.get("filter_type")
        f_name = filter_type_map.get(f_type, f_type)
        
        param_desc = ""
        if f_type == "moving_average":
            param_desc = f"窗口大小 N={signal_context.get('filter_window_size', '?')}"
        elif f_type == "rc_lowpass":
            param_desc = f"截止频率 f_c={signal_context.get('filter_cutoff_freq', '?')} Hz"
        elif f_type == "wiener":
            param_desc = "自适应最佳线性估计 (MMSE)"
            
        f_feats = signal_context.get("filter_features") or {}
        filter_block = (
            f"\n\n## 滤波器处理状态\n"
            f"滤波器类型: {f_name} ({param_desc})\n"
            f"滤波后统计特征: 均值={f_feats.get('mean', '?')}, 方差={f_feats.get('variance', '?')}, RMS={f_feats.get('rms', '?')}"
        )

    kalman_block = ""
    if signal_context and signal_context.get("kalman_run"):
        kalman_block = (
            f"\n\n## 卡尔曼滤波跟踪仿真状态\n"
            f"过程噪声强度 q: {signal_context.get('kalman_q', '?')}\n"
            f"测量噪声标准差 σ_v (r): {signal_context.get('kalman_r', '?')}\n"
            f"状态初速度 v₀: {signal_context.get('kalman_v0', '?')}\n"
            f"收敛估计协方差 P₁₁: {signal_context.get('kalman_p_final', '?')}\n"
            f"收敛位置增益 K₁: {signal_context.get('kalman_k1_final', '?')}\n"
            f"收敛速度增益 K₂: {signal_context.get('kalman_k2_final', '?')}"
        )

    knowledge_block = ""
    if knowledge_context and knowledge_context.get("current_node_id"):
        node = nodes.get(knowledge_context["current_node_id"])
        if node:
            knowledge_block = (
                f"\n\n## 当前讨论的知识点\n"
                f"「{node['title']}」（{node['chapter']}）\n"
                f"核心概念: {node['core_concept']}\n"
                f"学生正在追问这个知识点的深层问题，请直接切入核心作答。"
            )

    prompt = (
        f"你是《随机信号分析》课程的 AI 助教 Clar，职责是帮助学生真正理解随机信号处理。\n"
        f"你的知识库覆盖以下节点: {node_brief}\n"
        f"此外还有术语符号表、公式库、例题集和常见误区可供查询。"
        f"{signal_block}{filter_block}{kalman_block}{knowledge_block}\n"
        f"\n## 行为准则\n"
        f"1. 遇到概念解释、公式推导、术语定义时，若上下文/历史中缺乏准确信息，可调用工具获取以确保准确；若已有相关信息或属于基础通用知识，建议直接在 \"reply\" 中回答，避免不必要的工具调用以提升响应速度。\n"
        f"2. 用中文回答。所有数学公式、符号、变量及数学式子必须且只能用 LaTeX 渲染，行内公式必须包裹在单美元符号 $...$ 中，独立块级公式必须包裹在双美元符号 $$...$$ 中且单独成行。公式保持在一行内。严禁使用 \\[...\\] 或 \\(...\\) 或 [...] 作为公式定界符。\n"
        f"3. 绝对禁止在 $ 或 $$ 的数学块外部输出任何带有反斜杠的 LaTeX 命令或裸露的数学符号（例如：绝对不能在普通文本中直接书写 \\tau、\\Delta 或 \\sin(\\omega t) 或 x(t)，必须写作 $\\tau$、$\\Delta$、$\\sin(\\omega t)$、$x(t)$）。\n"
        f"4. 结合工程实际举例说明，不要只堆砌公式和定义。\n"
        f"5. 语气像一位耐心的助教——用简洁清晰的语言把复杂概念讲透。\n"
        f"6. 回复末尾单独一行输出 [NODE:节点ID]，关联到与回答最相关的知识卡片。\n"
        f"7. 严禁在回复中出现工具调用痕迹（如\"让我查一下\"\"调用函数\"等）。\n"
        f"8. 不输出任何 Emoji 表情，用纯文字表达。\n"
        f"9. 绝对禁止使用 ~~（波浪号）和 ---（连续减号）。\n"
        f"10. 严格遵守 Markdown 语法：加粗文本必须紧贴定界符，即 **加粗内容** 之间绝不能有任何空格或多余字符（必须是 **加粗文本**，禁止写成 * *加粗* * 或 ** 加粗 **），斜体文本同理（必须是 *斜体文本*）。\n"
    )

    if ui_mode == "all":
        prompt += (
            "\n## 全屏沉浸模式 (Clar-all) 特别规则\n"
            "在 Clar-all 模式下，左侧主工作区和底栏是隐藏的。为了让本系统显得极度智能，你必须承担起「全自动信号生成 + 滤波处理 + 算法对比 + 深度特征分析」的全链条职责（即 AI-all 必须全自动闭环，用户只需给出模糊需求，你直接把活全干了）：\n"
            "1. **主动构建教学仿真实验**：如果用户讨论某个信号处理算法（如维纳滤波、马尔可夫、低通滤波、卡尔曼滤波）或信号特征（如自相关、功率谱、频谱），你必须在回答的同时，主动在 JSON 中配好 `generate_signal` 和 `run_toolbox` 执行实验，不需要等到用户明确发出生成指令！\n"
            "   * **维纳最优滤波 (wiener)**: 主动生成正弦+白噪声 (freq=200, fs=10000, snr_db=10) 并运行 wiener 滤波 (operation: 'wiener')。在 JSON 中设置 suggested_page 为 'toolbox'。同时在回答中嵌入自适应滤波对比图 `<div class=\"ai-chart\" data-type=\"filter\"></div>`。\n"
            "   * **卡尔曼滤波 (kalman)**: 卡尔曼滤波属于独立的二维状态空间仿真，无需生成前置观测序列。请将 generate_signal 设为 null，仅返回 run_toolbox (operation: 'kalman', q=0.1, r=1.0, v0=1.0)，在 JSON 中设置 suggested_page 为 'toolbox'。在回答中嵌入卡尔曼轨迹图 `<div class=\"ai-chart\" data-type=\"kalman\"></div>`。\n"
            "   * **高斯白噪声 (white noise)**: 主动生成高斯白噪声信号 (fs=10000, snr_db=10)。在 JSON 中设置 suggested_page 为 'signal-lab', freq_analysis_type 为 'psd' (以展示平坦功率谱)。在回答中嵌入 `<div class=\"ai-chart\" data-type=\"time-domain\" data-subtype=\"waveform\"></div>` 和 `<div class=\"ai-chart\" data-type=\"freq-domain\" data-subtype=\"psd\"></div>`。\n"
        )

    if require_json:
        prompt += (
            "\n\n## 最终输出格式规范 (CRITICAL)\n"
            "你的回复必须由两部分组成，中间用 `===METADATA===` 分隔。请严格按照以下格式输出，绝对不要使用 ```json 包裹整个回复，也不要把文本解答放进 JSON 字符串中：\n"
            "[第一部分：你对用户问题的详细文字解答]\n"
            "这里直接以 Markdown 格式编写你的学术解答，LaTeX 公式（行内公式必须用 $...$ 包裹，例如 $\\tau$ 和 $\\Delta$；独立块公式必须用 $$...$$ 包裹，且公式单独占据一行）。如果是 Clar-all 模式，可以直接在适当的段落中嵌入相应的 HTML 图表占位符（如 `<div class=\"ai-chart\" data-type=\"...\"></div>`）。\n"
            "\n"
            "===METADATA===\n"
            "{\n"
            '  "node_id": null | "KP_CH1_01" | "KP_CH1_02" | "KP_CH2_01" | "KP_CH2_02" | "KP_CH2_03" (关联与回答最相关的知识卡片ID，如涉及平稳过程填 KP_CH1_01，维纳-欣钦填 KP_CH1_02，高斯白噪声填 KP_CH2_01，维纳滤波填 KP_CH2_02，卡尔曼滤波填 KP_CH2_03。若无可填 null),\n'
            '  "new_card": null | {"title": "提炼的新知识点标题", "core_concept": "新知识点的核心概念"},\n'
            '  "quick_questions": ["追问问题1", "追问问题2", "追问问题3"],\n'
            '  "suggested_page": "signal-lab" | "knowledge-map" | "toolbox" | "none",\n'
            '  "time_analysis_type": null | "waveform" | "autocorr" | "crosscorr" | "pdf",\n'
            '  "freq_analysis_type": null | "amplitude" | "psd" | "phase",\n'
            '  "generate_signal": null | {\n'
            '     "signal_type": "正弦+白噪声" | "方波+白噪声" | "窄带" | "瑞利分布" | "线性调频(LFM)" | "高斯白噪声" | "一阶马尔可夫过程" | "三角波+白噪声" | "双频正弦+白噪声",\n'
            '     "freq": 信号频率/中心频率/起始频率(float，单位Hz，高斯白噪声和一阶马尔可夫不需要该参数填 null),\n'
            '     "fs": 采样率(int，单位Hz),\n'
            '     "snr_db": 信噪比(float，单位dB),\n'
            '     "bandwidth": 带宽(float，单位Hz，选填，针对窄带或瑞利分布),\n'
            '     "freq_end": 扫频终止频率(float，单位Hz，选填，针对线性调频),\n'
            '     "markov_a": 自回归系数(float，在0到0.99之间，选填，针对一阶马尔可夫过程，默认0.9),\n'
            '     "freq2": 第二频率(float，单位Hz，选填，针对双频正弦+白噪声，默认300.0)\n'
            '  },\n'
            '  "run_toolbox": null | {\n'
            '     "operation": "moving_average" | "rc_lowpass" | "wiener" | "kalman",\n'
            '     "params": {\n'
            '        "window_size": 窗口大小(int，针对滑动平均),\n'
            '        "cutoff_freq": 截止频率(float，单位Hz，针对RC低通),\n'
            '        "q": 过程噪声强度(float，针对卡尔曼),\n'
            '        "r": 测量噪声标准差(float，针对卡尔曼),\n'
            '        "v0": 状态初速度(float，针对卡尔曼)\n'
            '     }\n'
            '  }\n'
            "}\n"
            "※ suggested_page 说明：根据用户的意图判断是否需要帮用户切换工作区页面。如果用户想生成信号/看时频域波形/分析基底信号特征选 'signal-lab'，想看课程大纲/知识图谱拓扑选 'knowledge-map'，想做滤波实验（包括滑动平均、RC低通、维纳滤波、卡尔曼滤波仿真）选 'toolbox'。如果不涉及切换或仅对当前页面已有的实验/仿真结果进行分析，则填 'none'。\n"
            "※ time_analysis_type 说明：如果用户想要查看时域波形图、自相关函数图、互相关函数图或概率密度(PDF)图，或者用户的提问涉及并要求查看某一个特定的时域图表，则填入该字段对应的取值（waveform、autocorr、crosscorr、pdf）。此时 suggested_page 务必设为 'signal-lab'。如不需要切换时域图像，填 null。\n"
            "※ freq_analysis_type 说明：如果用户想要查看幅度谱、功率谱密度(PSD)或相位谱，或者用户的提问涉及并要求查看某一个特定的频域图表，则填入该字段对应的取值（amplitude、psd、phase）。此时 suggested_page 务必设为 'signal-lab'。如不需要切换频域图像，填 null。\n"
            "※ generate_signal 说明：当且仅当用户请求/指示生成某种信号时，填入该对象。此时 suggested_page 务必设为 'signal-lab'。\n"
            "※ run_toolbox 说明：当用户请求在工具箱运行滑动平均滤波、RC一阶低通滤波、维纳最优滤波或卡尔曼滤波仿真，或者你在解答中决定展示某种实验时，填入此对象，并将参数传回前端，前端会自动配置参数并立即执行。此时 suggested_page 务必设为 'toolbox'。如果不涉及工具箱运行，则填 null。\n"
            "【重要】如果用户的指令比较模糊（缺少部分或全部参数），必须按如下经典值直接填入（绝对不要向用户追问参数）：\n"
            "- 'generate_signal':\n"
            "  * '正弦+白噪声': freq=200.0, fs=10000, snr_db=10.0\n"
            "  * '方波+白噪声': freq=200.0, fs=10000, snr_db=10.0\n"
            "  * '窄带': freq=200.0, fs=10000, snr_db=10.0, bandwidth=50.0\n"
            "  * '瑞利分布': freq=200.0, fs=10000, snr_db=10.0, bandwidth=50.0\n"
            "  * '线性调频(LFM)': freq=100.0, freq_end=400.0, fs=10000, snr_db=10.0\n"
            "  * '高斯白噪声': fs=10000, snr_db=10.0\n"
            "  * '一阶马尔可夫过程': markov_a=0.9, fs=10000, snr_db=10.0\n"
            "  * '三角波+白噪声': freq=200.0, fs=10000, snr_db=10.0\n"
            "  * '双频正弦+白噪声': freq=200.0, freq2=300.0, fs=10000, snr_db=10.0\n"
            "  * 若只说'生成信号'但无指明类型，默认按 '正弦+白噪声' 经典值。\n"
            "- 'run_toolbox':\n"
            "  * 'moving_average': window_size=10\n"
            "  * 'rc_lowpass': cutoff_freq=500.0\n"
            "  * 'wiener': params留空/无\n"
            "  * 'kalman': q=0.1, r=1.0, v0=1.0\n"
            "如果用户不需要生成信号/运行工具，对应的字段必须返回 null。"
        )

    return prompt


class SignalAgent:
    def __init__(self):
        _load_dotenv()
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key or api_key == "your_deepseek_api_key_here":
            raise ValueError("请在 .env 文件中设置有效的 DEEPSEEK_API_KEY")
        
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        
        timeout_val = os.getenv("DEEPSEEK_TIMEOUT", "60.0")
        try:
            timeout = float(timeout_val)
        except ValueError:
            timeout = 60.0
            
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )

    def get_smart_follow_ups(self, node_title, core_concept, engineering_meaning="", count=3):
        """
        根据知识点生成智能追问问题列表。
        调用 DeepSeek API 生成与知识点相关的追问。
        如果 API 不可用则返回 None，由调用方回退到默认问题。
        """
        prompt = (
            f"你是一个《随机信号分析》课程的 AI 助教 Clar。\n"
            f"当前讨论的知识点：{node_title}\n"
            f"核心概念：{core_concept}\n"
            f"工程意义：{engineering_meaning or '暂无'}\n\n"
            f"请生成 {count} 个能够引导学生深入思考该知识点的追问问题，"
            f"问题应当具有启发性和工程关联性。\n"
            f"请严格按照 JSON 格式返回：{{\"questions\": [\"问题1\", \"问题2\", ...]}}"
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=512,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content
            data = json.loads(raw) if raw else {}
            questions = data.get("questions", [])
            if questions and len(questions) >= 1:
                return questions
            return None
        except Exception:
            logger.exception("智能追问生成失败")
            return None

    def _execute_tool(self, name, args, signal_context):
        handler = _TOOL_DISPATCH.get(name)
        return handler(args, signal_context) if handler else json.dumps({"error": f"未知工具: {name}"},
                                                                        ensure_ascii=False)

    def chat(self, user_message, signal_context=None, knowledge_context=None, temperature=0.5, require_json=False, ui_mode="classic", history=None):
        system_prompt = _build_system_prompt(signal_context, knowledge_context, require_json, ui_mode)
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for msg in history:
                if isinstance(msg, dict) and msg.get("role") in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})
        kwargs = {"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": 4096}
        # Disabled response_format json_object for split response structure

        try:
            response = self.client.chat.completions.create(tools=TOOLS, **kwargs)
            msg = response.choices[0].message
            if msg.tool_calls:
                clean_content = _clean_reply(msg.content or "")
                if _RE_EMPTY_XML.match(clean_content): clean_content = ""
                messages.append({"role": "assistant", "content": clean_content, "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in
                    msg.tool_calls]})
                for tc in msg.tool_calls:
                    try:
                        fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    except json.JSONDecodeError:
                        fn_args = {}
                    result = self._execute_tool(tc.function.name, fn_args, signal_context)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

                # Second turn: keep response_format if require_json is True
                kwargs["messages"] = messages
                if not require_json:
                    kwargs.pop("response_format", None)
                response2 = self.client.chat.completions.create(**kwargs)
                reply = response2.choices[0].message.content
            else:
                reply = msg.content
        except Exception as e:
            logger.exception("AI 服务调用失败")
            reply = f"抱歉，AI 服务暂时不可用：{e}"

        reply = _clean_reply(reply or "抱歉，我暂时无法回答这个问题。")

        node_id = None
        match = _RE_NODE.search(reply)
        if match:
            node_id = match.group(1)
            reply = _RE_NODE.sub("", reply).strip()

        return reply, node_id

    def chat_stream(self, user_message, signal_context=None, knowledge_context=None, temperature=0.5, require_json=False, ui_mode="classic", history=None):
        system_prompt = _build_system_prompt(signal_context, knowledge_context, require_json, ui_mode)
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for msg in history:
                if isinstance(msg, dict) and msg.get("role") in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})
        kwargs = {"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": 4096}
        # Disabled response_format json_object for split response structure

        try:
            client_to_use = self.client.client if hasattr(self.client, 'client') else self.client
            stream_response = client_to_use.chat.completions.create(tools=TOOLS, stream=True, **kwargs)
            
            has_tool_calls = False
            tool_calls_dict = {}
            assistant_content = ""
            
            for chunk in stream_response:
                choices = chunk.choices
                if not choices:
                    continue
                delta = choices[0].delta
                if not delta:
                    continue
                
                # Collect tool calls if any
                if delta.tool_calls:
                    has_tool_calls = True
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_dict:
                            tool_calls_dict[idx] = {
                                "id": "",
                                "name": "",
                                "arguments": ""
                            }
                        if tc.id:
                            tool_calls_dict[idx]["id"] += tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls_dict[idx]["name"] += tc.function.name
                            if tc.function.arguments:
                                tool_calls_dict[idx]["arguments"] += tc.function.arguments
                
                # Collect and yield normal content
                if delta.content:
                    if not has_tool_calls:
                        yield delta.content
                    else:
                        assistant_content += delta.content

            if has_tool_calls:
                formatted_tool_calls = []
                for idx in sorted(tool_calls_dict.keys()):
                    tc = tool_calls_dict[idx]
                    formatted_tool_calls.append({
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["arguments"]
                        }
                    })
                
                clean_content = _clean_reply(assistant_content)
                if _RE_EMPTY_XML.match(clean_content):
                    clean_content = ""
                
                messages.append({
                    "role": "assistant",
                    "content": clean_content,
                    "tool_calls": formatted_tool_calls
                })
                
                for tc in formatted_tool_calls:
                    try:
                        fn_args = json.loads(tc["function"]["arguments"]) if tc["function"]["arguments"] else {}
                    except json.JSONDecodeError:
                        fn_args = {}
                    result = self._execute_tool(tc["function"]["name"], fn_args, signal_context)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result
                    })
                
                # Second turn: stream response
                kwargs["messages"] = messages
                if not require_json:
                    kwargs.pop("response_format", None)
                
                stream_response2 = client_to_use.chat.completions.create(stream=True, **kwargs)
                for chunk in stream_response2:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content
                        
        except Exception as e:
            logger.exception("AI 服务流式调用失败")
            yield f"抱歉，AI 服务暂时不可用：{e}"