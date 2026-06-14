# 项目展示代码与讲解手册 (NotebookLM 专用资料)

本文档汇集了《随机信号分析》AI 助教项目在“感知-决策-控制”三层架构体系下的核心代码片段，并配有演示时的口述演讲词，完美契合技术展示的需求。

---

## 1. 感知层代码 (Perception) —— 重点展示“如何捕获用户环境”

### 推荐展示内容 A：全场景屏幕感知 (Telemetry)
展示前端如何通过 DOM 回溯和意图判定防抖，实现对用户行为的无感捕捉。

**代码截取 (`frontend/js/telemetry.js`)：**
```javascript
// 核心状态解析：根据鼠标停留位置动态生成上下文
resolveSensingTarget(el) {
    if (!el) return null;
    let tooltipEl = el.closest('[data-ai-tooltip]');
    if (tooltipEl) {
        let text = tooltipEl.getAttribute('data-ai-tooltip');
        
        // 动态穿透图表状态（时域/频域卡片）
        if (tooltipEl.id === 'time-card' || tooltipEl.querySelector('#waveform-plot')) {
            const timeTab = document.getElementById('time-analysis-type')?.value || 'waveform';
            const tabNames = { 'waveform': '时域波形 X(t)', 'autocorr': '自相关函数 Rx(τ)' };
            text = `时域分析图表 - 当前正在查看 ${sigType} 的 ${tabNames[timeTab]}`;
        } else if (tooltipEl.id === 'freq-card' || tooltipEl.querySelector('#spectrum-plot')) {
            const freqTab = document.getElementById('freq-analysis-type')?.value || 'amplitude';
            const tabNames = { 'amplitude': '幅度谱 |X(f)|', 'phase': '相位谱 θ(f)' };
            text = `频域分析图表 - 当前正在查看 ${sigType} 的 ${tabNames[freqTab]}`;
        }
        return { element: tooltipEl, text: text };
    }
}
```

**🗣️ 讲解话术：**
> “正如大家刚才在演示中看到的，小精灵能在鼠标悬停时自动诊断。在感知层，我们通过监听全局事件和 DOM 树回溯，实时捕获图表的时频域特征并封装为上下文，让 AI 拥有了‘视力’。”

### 推荐展示内容 B：信号特征提取引擎
展示后端如何严谨地计算时域和频域特征，为 LLM 提供数字化的“感官”。

**代码截取 (`core/signal_engine.py`)：**
```python
def analyze_features(signal_data: np.ndarray, fs: int) -> Dict[str, Any]:
    n = len(signal_data)
    mean_val = float(np.mean(signal_data))
    
    # 1. 无偏自相关函数估计 (Auto-correlation)
    sig_centered = signal_data - mean_val
    autocorr = np.correlate(sig_centered, sig_centered, mode="full")
    autocorr = autocorr[n - 1:] / (n - np.arange(n))
    
    # 2. 基于 FFT 的功率谱密度 (Power Spectral Density)
    freqs, psd = scipy_signal.periodogram(signal_data, fs)
    
    # 3. 相位谱 (Phase Spectrum)
    fft_noisy = np.fft.rfft(signal_data)
    phase = np.angle(fft_noisy)

    return {"autocorr": autocorr, "psd": psd, "phase": phase, "mean": mean_val}
```

**🗣️ 讲解话术：**
> “AI 懂物理，是因为我们喂给它的不是图片，而是高精度的数字特征。在这个特征引擎中，我们利用无偏估计计算自相关函数，利用 FFT 还原功率谱密度，将波形转化为大模型能理解的绝对结构化数据。”

---

## 2. 决策层代码 (Decision & LLM) —— 重点展示“大模型如何与专业知识结合”

### 推荐展示内容：Function Calling 与工具挂载
展示 AI 如何从聊天引擎跃升为操作系统的“大脑”。

**代码截取 (`core/agent_brain.py`)：**
```python
# 核心对话流：带有内置工具集 (TOOLS) 的模型推演
def chat(self, user_message, signal_context, knowledge_context):
    messages = [{"role": "system", "content": system_prompt}]
    
    # 第一轮推演：抛给大模型进行自主决策
    response = self.client.chat.completions.create(tools=TOOLS, messages=messages)
    msg = response.choices[0].message
    
    # 捕获并执行模型主动发起的工具调用
    if msg.tool_calls:
        for tc in msg.tool_calls:
            fn_args = json.loads(tc.function.arguments)
            # 例如：挂载执行 get_current_signal() 或 get_error_warning()
            result = _execute_tool(tc.function.name, fn_args, signal_context)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            
        # 携带工具执行结果进行第二轮推演
        response2 = self.client.chat.completions.create(messages=messages)
        return response2.choices[0].message.content
```

**🗣️ 讲解话术：**
> “在这里，LLM 不再是简单的聊天机器人。我们将后端的离散统计特征与专家题库封装成了 LLM 可调用的 Tool（工具），让大模型的大脑能实时‘看’到仿真波形数据并作出专业决策，这也是它能发现奈奎斯特混叠的奥秘所在。”

---

## 3. 控制层代码 (Control) —— 重点展示“AI如何静默控制前端界面”

### 推荐展示内容：流式 JSON 实时解析器
展示 AI 如何在打字的同时，就完成了前端界面的接管和指令下发。

**代码截取 (`backend/parser.py` 解析器状态机核心思路)：**
```python
class JSONReplyStreamParser:
    """
    流式状态机解析器：能够在 AI 返回完整 JSON 前，
    提前阻截并逐字符剥离出 'reply' 对话字段推给前端，消除首字延迟。
    """
    def feed(self, chunk: str):
        self.buffer += chunk
        
        # 实时嗅探 JSON 流中的 'reply' 键名
        if not self.reply_started:
            match = re.search(r'"reply"\s*:\s*"', self.buffer)
            if match:
                self.reply_started = True
                self.buffer = self.buffer[match.end():]
                
        # 一旦嗅探成功，开始向前端发射脱水的纯文字流
        if self.reply_started:
            out_chars = []
            for char in self.buffer:
                # 状态机：处理 \n, \t 和 Unicode 等边界情况...
                out_chars.append(char)
            yield "".join(out_chars)
```

**🗣️ 讲解话术：**
> “大家刚看到 AI 的回答和参数调整是‘零延迟’同步的。因为我们在控制层编写了这个高阶流式解析器，AI 一边生成庞大的 JSON 结构，系统一边利用状态机逐字符提取对话立刻发给前端，而在后台静默完成 generateSignal() 参数组装，实现了毫无卡顿的‘口令即操作’。”

---

## 4. 算法与知识点映射代码 (Algorithm) —— 重点展示“课程专业度”

### 推荐展示内容：高分辨率波形重建与物理失真对比
展示系统并非简单调用绘图库，而是深度融入了信号处理理论。

**代码截取 (`core/signal_engine.py`)：**
```python
def generate_high_res_clean(signal_type: str, freq: float, duration: float) -> np.ndarray:
    """
    高分辨率重建策略：在用户输入低采样率发生失真时，
    系统强行注入 100,000 点的高密度采样基准线，以直观对比香农定理。
    """
    n_samples = 100000
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    # 注入微小随机相位，打破与图表像素的周期性锁定
    if signal_type != "线性调频(LFM)":
        t += np.random.uniform(0, 1.0 / freq)
        
    if signal_type == "正弦+白噪声":
        return np.sin(2 * np.pi * freq * t)
    elif signal_type == "双频正弦+白噪声":
        freq2 = freq * 1.5
        return 0.5 * (np.sin(2 * np.pi * freq * t) + np.sin(2 * np.pi * freq2 * t))
```

**🗣️ 讲解话术：**
> “为了保证底层学术的严谨性，我们的系统不仅是调库。对于低采样率下波形失真的经典问题，我们通过代码加入了 10 万点级的高分辨率细粒度插值基准线，完美在图表上对比了‘模拟连续信号’与‘离散采样点’的物理差异，让学生秒懂奈奎斯特采样定律。”
