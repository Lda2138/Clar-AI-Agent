# core/prompts.py
import os
import json
from data.signal_knowledge_base import RANDOM_SIGNAL_KB

def _build_system_prompt(signal_context, knowledge_context=None, require_json=False):
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

    radar_block = ""
    if signal_context and signal_context.get("radar_run"):
        radar_block = (
            f"\n\n## 雷达目标追踪CMLD与卡尔曼仿真状态\n"
            f"虚警概率 Pf: {signal_context.get('radar_pf', '?')}\n"
            f"参考窗 R_ref: {signal_context.get('radar_r_ref', '?')}\n"
            f"保护窗 R_pro: {signal_context.get('radar_r_pro', '?')}\n"
            f"剔除数 D_high: {signal_context.get('radar_drop_high', '?')}\n"
            f"门限偏置 Offset: {signal_context.get('radar_offset', '?')}\n"
            f"过程噪声强度 qs: {signal_context.get('radar_qs', '?')}\n"
            f"关联波门 Gate: {signal_context.get('radar_gate', '?')}\n"
            f"幅度限制 (dB): {signal_context.get('radar_amp_limit', '?')}\n"
            f"累计虚警点数: {signal_context.get('radar_fa_count', '?')} 个\n"
            f"累计漏警点数: {signal_context.get('radar_miss_count', '?')} 个\n"
            f"累计真实航迹点数: {signal_context.get('radar_pts_count', '?')} 个"
        )

    knowledge_block = ""
    if knowledge_context:
        if knowledge_context.get("current_node_id"):
            node = nodes.get(knowledge_context["current_node_id"])
            if node:
                knowledge_block += (
                    f"\n\n## 当前讨论的知识点\n"
                    f"「{node['title']}」（{node['chapter']}）\n"
                    f"核心概念: {node['core_concept']}\n"
                    f"工程意义: {node.get('engineering_meaning', '无')}\n"
                    f"学生正在追问这个知识点的深层问题，请直接切入核心作答。"
                )
        
        if knowledge_context.get("glossary_matches"):
            matches = knowledge_context["glossary_matches"]
            g_desc = "\n".join([f"- {g['symbol']} ({g['name']}): {g['description']}" for g in matches])
            knowledge_block += f"\n\n## 相关术语符号表参考\n{g_desc}"

        if knowledge_context.get("problem_case_match"):
            c = knowledge_context["problem_case_match"]
            knowledge_block += (
                f"\n\n## 相关经典题型与数学推导\n"
                f"题型: {c.get('type_name')}\n问题: {c.get('question')}\n"
                f"解题思路: {c.get('thinking_process')}\n推导: {c.get('math_steps')}"
            )
            
        if knowledge_context.get("error_warning_match"):
            e = knowledge_context["error_warning_match"]
            knowledge_block += (
                f"\n\n## 相关易错避坑指南\n"
                f"现象: {e.get('symptom')}\n"
                f"正解: {e.get('correct_understanding')}\n"
                f"建议: {e.get('tips')}"
            )

    prompt = (
        f"你是《随机信号分析》课程的 AI 助教 Clar，职责是帮助学生真正理解随机信号处理。\n"
        f"你的知识库覆盖以下节点: {node_brief}\n"
        f"此外还有术语符号表、公式库、例题集和常见误区可供查询。"
        f"{signal_block}{filter_block}{kalman_block}{radar_block}{knowledge_block}\n"
        f"\n## 行为准则\n"
        f"1. 遇到概念解释、公式推导、术语定义时，务必先调用工具获取准确信息，不要凭记忆编造\n"
        f"2. 用中文回答，数学公式与变量规范：任何数学自变量、变量、表达式、函数、希腊字母或公式（如 $X(t)$、$A(t)$、$\\Phi(t)$、$\\theta_x(f)$、$\\tau$、$\\sigma^2$ 等），无论多么简单，都必须包裹在单一美元符号 $...$ (行内公式) 或双美元符号 $$...$$ (独立公式) 中，绝对不允许直接写成未包裹公式文本（如 X(t) 或 \\Phi(t)$ 等）。且每个公式首尾必须严格配对，公式在一行内。\n"
        f"3. 结合工程实际举例说明，不要只堆砌公式 and 定义\n"
        f"4. 语气像一位耐心的助教——用简洁清晰的语言把复杂概念讲透\n"
        f"5. 回复末尾单独一行输出 [NODE:节点ID]，关联到与回答最相关的知识卡片\n"
        f"6. 严禁在回复中出现工具调用痕迹（如\"让我查一下\"\"调用函数\"等）\n"
        f"7. 不输出任何 Emoji 表情，用纯文字表达\n"
        f"8. 绝对禁止使用 ~~（波浪号）和 ---（连续减号）\n"
        f"9. 【核心指令】如果你需要调用工具，请直接输出工具调用，绝对禁止在调用工具前输出任何解释性文字！\n"
    )

    if require_json:
        prompt += (
            "\n\n## 结构化 JSON 输出要求\n请务必返回纯净的 JSON 格式（不要用 ```json 包裹），且必须满足以下排版要求：\n"
            "【极其重要】在返回的 JSON 对象中，务必将 \"reply\" 键排在最前面（即 JSON 对象的第一个属性/Key），这样前台可以无延迟地实时流式提取并展示文字，彻底消除等待卡顿。\n"
            "{\n"
            '  "reply": "你对用户问题的详细文字解答",\n'
            '  "new_card": {"title": "提炼的新知识点标题", "core_concept": "新知识点的核心概念"},\n'
            '  "quick_questions": ["追问问题1", "追问问题2", "追问问题3"],\n'
            '  "suggested_page": "signal-lab" | "knowledge-map" | "toolbox" | "radar-tracking" | "none",\n'
            '  "time_analysis_type": null | "waveform" | "autocorr" | "crosscorr" | "pdf",\n'
            '  "freq_analysis_type": null | "amplitude" | "psd" | "phase",\n'
            '  "generate_signal": null | {\n'
            '     "signal_type": "正弦+白噪声" | "方波+白噪声" | "窄带" | "瑞利分布" | "线性调频(LFM)" | "高斯白噪声" | "一阶马尔可夫过程" | "三角波+白噪声" | "双频正弦+白噪声",\n'
            '     "freq": 信号频率/中心频率/起始频率(float，单位Hz，高斯白噪声 and 一阶马尔可夫过程不需要此参数填 null 即可),\n'
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
            "※ suggested_page 说明：根据用户的意图判断是否需要帮用户切换工作区页面。如果用户想生成信号/看时频域波形/分析基底信号特征选 'signal-lab'，想看课程大纲/知识图谱拓扑选 'knowledge-map'，想做滤波实验（包括滑动平均、RC低通、维纳滤波、卡尔曼滤波仿真）选 'toolbox'，想做雷达目标追踪与航迹管理实验选 'radar-tracking'。如果不涉及切换或仅对当前页面已有的实验/仿真结果进行分析，则填 'none'。\n"
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
