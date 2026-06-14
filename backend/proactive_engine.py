# backend/proactive_engine.py
import logging

logger = logging.getLogger("proactive_engine")

def evaluate_proactive_triggers(signal_context):
    """
    Evaluate the current signal context against random signal processing heuristics.
    Returns a dict with trigger info if a rule is hit, otherwise None.
    """
    if not signal_context:
        return None

    # --- Rule 1: Nyquist Sampling Theorem Violation ---
    # We check this first as it is a fundamental physical limitation
    signal_generated = signal_context.get("signal_generated") or signal_context.get("generated")
    if signal_generated:
        sig_type = signal_context.get("signal_type")
        fs = float(signal_context.get("fs") or 10000)
        freq = float(signal_context.get("freq") or 0)
        freq2 = float(signal_context.get("freq2") or 0)
        freq_end = float(signal_context.get("freq_end") or 0)
        
        # Check standard Nyquist limit
        if sig_type in ["正弦+白噪声", "方波+白噪声", "窄带", "瑞利分布", "三角波+白噪声"] and freq > 0:
            if freq >= fs / 2.0:
                return {
                    "type": "nyquist_violation",
                    "title": "采样定理违背 (频谱混叠)",
                    "params": {"freq": freq, "fs": fs},
                    "prompt": (
                        f"【系统触发：采样定理违背】\n"
                        f"检测到学生配置了 $f_0 = {freq}\\text{{ Hz}}$ 的{sig_type}，但采样率仅为 $f_s = {fs}\\text{{ Hz}}$。\n"
                        f"这违反了奈奎斯特采样定理（$f_s > 2 f_0$），导致严重的频谱混叠（Aliasing）。\n"
                        f"请以 Clar 的语气，主动以带有 '💡' 开头的主动指导卡片形式指出该错误，"
                        f"用直观的语言解释混叠的原因和危害，并引导学生点击快捷建议来恢复正确的参数（例如将采样率设为至少 {int(freq*2.5)} Hz）。"
                    )
                }
                
        # Check double sine
        if sig_type == "双频正弦+白噪声" and (freq > 0 or freq2 > 0):
            max_f = max(freq, freq2)
            if max_f >= fs / 2.0:
                return {
                    "type": "nyquist_violation_double",
                    "title": "双频采样定理违背",
                    "params": {"freq1": freq, "freq2": freq2, "fs": fs},
                    "prompt": (
                        f"【系统触发：采样定理违背】\n"
                        f"检测到学生配置了双频正弦信号（$f_1 = {freq}\\text{{ Hz}}$ 和 $f_2 = {freq2}\\text{{ Hz}}$），但采样率 $f_s = {fs}\\text{{ Hz}}$ 不足以解析最高频率分量（$f_s < 2 \\times {max_f}$）。\n"
                        f"请以 Clar 的语气主动指出由于采样率过低导致的高频分量丢失与混叠现象，"
                        f"解释如何根据最大频率分量选择合理的采样率，并提供修改采样率的快捷方式。"
                    )
                }
                
        # Check LFM
        if sig_type == "线性调频(LFM)" and freq_end > 0:
            if freq_end >= fs / 2.0:
                return {
                    "type": "nyquist_violation_lfm",
                    "title": "线性调频采样定理违背",
                    "params": {"freq_end": freq_end, "fs": fs},
                    "prompt": (
                        f"【系统触发：线性调频采样定理违背】\n"
                        f"检测到学生配置的线性调频（LFM）扫频终止频率 $f_{{end}} = {freq_end}\\text{{ Hz}}$ 超过了奈奎斯特频率 $f_s / 2 = {fs/2}\\text{{ Hz}}$。\n"
                        f"在扫频后期会出现严重的频域混叠，使时域波形看起来像是一个反向扫频的信号或杂乱信号。\n"
                        f"请作为 Clar 主动指出此物理现象，解释扫频信号防混叠的条件，并给出优化建议。"
                    )
                }

    # --- Rule 2: Filter Cutoff Frequency Misconfiguration ---
    filter_run = signal_context.get("filter_run")
    if filter_run:
        filter_type = signal_context.get("filter_type")
        fs = float(signal_context.get("fs") or 10000)
        freq = float(signal_context.get("freq") or 200)
        
        if filter_type == "rc_lowpass":
            cutoff = float(signal_context.get("filter_cutoff_freq") or 0)
            if cutoff >= fs / 2.0:
                return {
                    "type": "filter_cutoff_too_high",
                    "title": "滤波器截止频率越界",
                    "params": {"cutoff": cutoff, "fs": fs},
                    "prompt": (
                        f"【系统触发：截止频率过高】\n"
                        f"检测到学生将 RC 一阶低通滤波器的截止频率设为 $f_c = {cutoff}\\text{{ Hz}}$，已经超过或等于奈奎斯特频率（$f_s / 2 = {fs/2}\\text{{ Hz}}$）。\n"
                        f"这使得滤波器几乎没有滤除任何数字域中的高频噪声（数字域最大频率只到 $f_s/2$），导致滤波形同虚设。\n"
                        f"请以 Clar 的语气指出此设计的冗余性，并科普数字低通滤波中截止频率选择与采样率的关系。"
                    )
                }
            elif cutoff <= freq and signal_context.get("signal_type") in ["正弦+白噪声", "双频正弦+白噪声", "三角波+白噪声"]:
                return {
                    "type": "filter_cutoff_too_low",
                    "title": "截止频率过低滤除有用成分",
                    "params": {"cutoff": cutoff, "freq": freq},
                    "prompt": (
                        f"【系统触发：截止频率过低】\n"
                        f"检测到学生将低通滤波器截止频率设为 $f_c = {cutoff}\\text{{ Hz}}$，而原始信号的主载波频率为 $f_0 = {freq}\\text{{ Hz}}$。\n"
                        f"这会导致有用的正弦成分被大量衰减甚至完全滤除，输出信号只剩下微弱的基带直流或残留部分，严重降低信噪比。\n"
                        f"请以 Clar 的语气主动介入，提醒学生“切忌滤除有用成分”，引导其理解滤波器通带与有用信号频段匹配的工程常识。"
                    )
                }

    # --- Rule 3: Kalman Filter Convergence / Noise Misconfiguration ---
    kalman_run = signal_context.get("kalman_run")
    if kalman_run:
        q = float(signal_context.get("kalman_q") or 0)
        r = float(signal_context.get("kalman_r") or 0)
        
        if r >= 10.0 and q <= 0.005 and q > 0:
            return {
                "type": "kalman_over_smoothing",
                "title": "卡尔曼滤波器过度平滑 (失去跟踪灵敏度)",
                "params": {"q": q, "r": r},
                "prompt": (
                    f"【系统触发：卡尔曼滤波配置异常】\n"
                    f"检测到量测噪声协方差 $r = {r}$ 极高，而过程噪声协方差 $q = {q}$ 极低，即信噪比 $q/r \\le 0.0005$。\n"
                    f"这会导致卡尔曼增益 $K_k$ 收敛到非常小的值。滤波器将几乎完全忽略新的测量值 $z_k$，固守匀速物理模型预测状态。\n"
                    f"当真实目标发生机动（如突然加速）时，滤波器将无法跟上，产生巨大的延迟和跟踪偏差。\n"
                    f"请以 Clar 的语气，主动剖析为什么增益会过小，并提示如何微调 $q$ 或 $r$ 来实现实时敏捷跟踪。"
                )
            }
        elif q >= 2.0 and r <= 0.1 and r > 0:
            return {
                "type": "kalman_noise_jitter",
                "title": "卡尔曼滤波器极度抖动 (过度信任测量)",
                "params": {"q": q, "r": r},
                "prompt": (
                    f"【系统触发：卡尔曼滤波抖动异常】\n"
                    f"检测到过程噪声 $q = {q}$ 极大，而测量噪声 $r = {r}$ 极小。\n"
                    f"这意味着滤波器认为物理模型极不可信，而每一次的传感器测量极其完美。\n"
                    f"这将导致滤波器几乎退化为直接把测量的噪声位置作为估计输出，滤波完全失去了平滑降噪的意义，轨迹抖动极度剧烈。\n"
                    f"请以 Clar 的语气主动介入，生动解释卡尔曼滤波在模型不确定度与测量精密度之间的天平作用。"
                )
            }

    # --- Rule 4: Radar Target Loss (CFAR Threshold issues) ---
    radar_run = signal_context.get("radar_run")
    if radar_run:
        fa_count = int(signal_context.get("radar_fa_count") or 0)
        miss_count = int(signal_context.get("radar_miss_count") or 0)
        pts_count = int(signal_context.get("radar_pts_count") or 0)
        
        # High false alarm (threshold too low or Offset too small)
        if fa_count >= 50 and pts_count > 0:
            return {
                "type": "radar_high_false_alarm",
                "title": "雷达虚警率过高",
                "params": {"fa_count": fa_count, "offset": signal_context.get("radar_offset")},
                "prompt": (
                    f"【系统触发：雷达虚警率过高】\n"
                    f"检测到雷达目标跟踪实验中产生了大量的虚警点（当前累计虚警高达 {fa_count} 个）。\n"
                    f"虚警是由噪声突破 CFAR 检测门限引起的，这说明当前设定的 '门限偏置 Offset' ({signal_context.get('radar_offset')}) 偏小，导致检测门限偏低，杂波和噪声被误判为真实航迹点。\n"
                    f"请作为 Clar 解释恒虚警检测中噪声包络与检测门限的动态关系，并主动引导学生通过快捷按键将 Offset 适当调大以压制虚警。"
                )
            }
        # High miss alarm (threshold too high)
        elif miss_count >= 15 and pts_count > 0:
            return {
                "type": "radar_high_miss_rate",
                "title": "雷达漏警率过高 (丢失目标航迹)",
                "params": {"miss_count": miss_count, "offset": signal_context.get("radar_offset")},
                "prompt": (
                    f"【系统触发：雷达漏警率过高】\n"
                    f"检测到雷达检测与跟踪实验中漏警点数过多（当前累计漏警达 {miss_count} 个），导致航迹无法连续，甚至发生航迹丢失。\n"
                    f"漏警是由于检测门限设置过高，导致较弱的真实目标回波信号无法突破门限。\n"
                    f"这与门限偏置 Offset ({signal_context.get('radar_offset')}) 设定过大直接相关。\n"
                    f"请作为 Clar 主动介入，解释虚警概率与漏警概率之间的此消彼长（Trade-off）关系，并给出合理的 Offset 建议值。"
                )
            }

    # --- Rule 5: Learning Stagnation (User Idle on Knowledge Map) ---
    stagnation = signal_context.get("stagnation") or (signal_context.get("idle_time", 0) >= 90 and signal_context.get("current_page") == "knowledge-map")
    if stagnation:
        current_node_id = signal_context.get("current_node_id") or "KP_CH3_03"
        node_name = signal_context.get("graph_node_name") or "平稳随机过程的线性变换"
        return {
            "type": "learning_stagnation",
            "title": "学习停滞引导",
            "params": {"node_id": current_node_id, "node_name": node_name},
            "prompt": (
                f"【系统触发：学习停滞引导】\n"
                f"检测到学生在知识图谱的【{node_name}】（节点ID: {current_node_id}）这一节停留了超过90秒，没有任何操作。\n"
                f"这是本章的难点，涉及维纳-欣钦定理和传递函数的结合。\n"
                f"请作为 Clar 主动介入，以温柔、鼓舞的语气主动提供一些启发性的讲解，并说明该小节在随机信号分析课程中的地位，"
                f"并提供 3 个快捷建议按钮（例如“出一道经典考研自测题”、“通俗解释维纳-欣钦定理”、“有什么工程应用案例”），"
                f"帮助学生打破僵局，继续深入学习。"
            )
        }

    return None

def evaluate_implicit_telemetry(telemetry_context, signal_context=None):
    """
    Evaluate the implicit telemetry context (e.g. from polling) and return
    a structured dict for the Proactive Action Card if an intervention is needed.
    """
    if not telemetry_context:
        return None

    # Scenario A: Knowledge to Tool Pre-computation
    page = telemetry_context.get("page")
    node_id = telemetry_context.get("active_node_id")
    dwell_time = telemetry_context.get("dwell_time", 0)
    node_name = telemetry_context.get("active_node_name", "")

    if page == "knowledge-map" and dwell_time >= 45 and ("维纳" in node_name or node_id == "KP_CH4_02"):
        if signal_context and signal_context.get("signal_generated"):
            return {
                "type": "pre_computation",
                "insight": f"发现您在学习「{node_name}」时停留了较长的时间，且工作区已有一段含噪信号。",
                "pre_computation_text": "我已在后台基于您当前的信号，预先执行了维纳滤波的最优均方误差估计，准备好了对比结果。",
                "action_type": "run_wiener_filter",
                "action_payload": {},
                "action_label": "查看维纳滤波对比"
            }
        else:
            return {
                "type": "pre_computation",
                "insight": f"发现您在学习「{node_name}」时停留了较长的时间，但您尚未生成含噪信号。",
                "pre_computation_text": "维纳滤波的最佳理解方式是动手实践。点击下方按钮，我将带您去信号工坊生成一段包含高斯白噪声的测试信号！",
                "action_type": "navigate_to_signal_lab",
                "action_payload": {},
                "action_label": "去生成测试信号"
            }

    # Scenario B: Blind Parameter Tuning (Kalman)
    kalman_runs = telemetry_context.get("kalman_runs", 0)
    kalman_time_window = telemetry_context.get("kalman_time_window", 999)
    
    if kalman_runs >= 4 and kalman_time_window <= 30:
        # Reset telemetry kalman stats via client response or client logic
        return {
            "type": "behavioral_intervention",
            "insight": "我注意到您在短时间内频繁调节卡尔曼滤波的参数，可能遇到了收敛瓶颈。",
            "pre_computation_text": "分析当前真实运动模型，您目前的参数可能存在偏差。我为您计算了一组平衡的协方差参数 (q=0.05, r=1.5)，以获得更平滑的估计轨迹。",
            "action_type": "apply_kalman_params",
            "action_payload": {"q": 0.05, "r": 1.5},
            "action_label": "应用优化参数 (q=0.05, r=1.5)"
        }

    return None
