# 🛠️ 开发者指南与接口规范 (Developer Guidelines)

本文档是《随机信号分析》AI 助教 Clar 系统的官方“使用词典”与“修改地图”。旨在规范后续版本的二次开发、新功能接入以及核心 API 的使用标准。

---

## 1. 核心业务全链路实现流程

### 1.1 单次信号生成与分析流 (Single Realization Flow)
这是系统中最基础的数据流水线，描述了当用户点击“生成信号”按钮时，发生了什么：

1. **[UI 采集]** `frontend/js/ui.js` 读取拉杆和下拉框的值。
2. **[网络请求]** 调用 `api_service.js` 构建 `SignalParams` JSON 并 POST 给后端 `/api/signal/generate`。
3. **[后端解包]** `backend/signal_routes.py` 接收验证数据，并调用门面 `core/signal_engine.py`。
4. **[生成与分析]** 
   - 门面调度 `core/signal/generators.py` 按指定的波形方程生成时域数据（包括纯净信号和含噪信号）。
   - 调度 `core/signal/analyzers.py` 计算出 FFT 频谱、PSD 功率谱、相位谱和 PDF 直方图。
5. **[前端渲染]** 路由组装 JSON 返回前端。`charts.js` 中的 `updatePlots()` 将数据推入 Plotly / Echarts 图层完成渲染，并通过 `telemetry.js` 静默上报用户行为。

### 1.2 蒙特卡洛流式动画与系综收敛流 (Monte Carlo Stream)
这是为了突破 $O(N^2)$ 性能瓶颈而设计的极速渐进式渲染流程：

1. **[极速生成]** 后端 `/api/signal/ensemble` **不再调用** `analyzers.py` 进行全局特征提取。而是使用高速的 `np.histogram` 在 5ms 内计算出 15 组数据的全局概率密度。
2. **[流式渲染]** 前端 `ui.js` 的 `generateEnsembleData()` 接收数据后，立即开启一个 `setInterval(150ms)` 定时器。
3. **[动态叠绘]** `charts.js` 读取不断递增的 `S.ensembleRenderCount` 控制渲染层级，像示波器余晖一样逐根画线。
4. **[原生收敛]** 伴随波形叠绘，前端在图表回调函数中直接执行轻量级累积样本直方图算法，实现了 PDF 从参差不齐到平滑钟形曲线的物理“生长”动画。

---

## 2. 接口字典 (REST API Specs)

### 2.1 信号生成接口
* **Endpoint**: `POST /api/signal/generate`
* **Request (SignalParams)**:
  ```json
  {
    "signal_type": "sine",     // 信号类型: sine, square, gaussian_white_noise 等
    "freq": 10.0,              // 主频率 (Hz)
    "fs": 10000,               // 采样率
    "snr_db": 5.0,             // 信噪比 (dB)
    "duration": 1.0            // 时长 (s)
    // 可选参数: bandwidth, freq_end, markov_a 等
  }
  ```
* **Response**:
  ```json
  {
    "t": [...],                // 时间轴 (抽样后)
    "clean": [...],            // 纯净波形
    "noisy": [...],            // 含噪波形
    "freqs": [...],            // 频率轴
    "spec_noisy": [...],       // 幅度谱
    "psd": [...],              // 功率谱密度
    "autocorr": [...],         // 自相关函数
    "pdf_x": [...], "pdf_y": [...] // 概率密度函数
  }
  ```

### 2.2 系综（蒙特卡洛）生成接口
* **Endpoint**: `POST /api/signal/ensemble`
* **Request (EnsembleParams)**: 在 `SignalParams` 基础上新增 `ensemble_n` (平行宇宙数量)。
* **Response**:
  ```json
  {
    "t_ensemble": [...],
    "ensembles_noisy": [[...], [...], ...], // N 组含噪波形
    "ensembles_clean": [[...], [...], ...], // N 组纯净波形
    "pdf_x_ensemble": [...],                // 收敛后的理论横轴
    "pdf_y_ensemble": [...]                 // 收敛后的理论纵轴
  }
  ```

---

## 3. 核心修改规范 (Modification Specs)

系统的深层解耦赋予了您极大的自由度。以下是常见扩展任务的修改清单。

### 3.1 如何添加一种全新的信号波形？
1. **添加生成逻辑**：打开 `core/signal/generators.py`，新增一个名为 `_gen_new_signal` 的函数。
2. **注册路由**：在 `generators.py` 底部的 `_SIGNAL_GENERATORS` 字典中注册它的调用键值（例如 `"my_signal": _gen_new_signal`）。
3. **暴露前端选项**：在 `frontend/index.html` 的下拉菜单 `<select id="signal-type">` 中添加对应的 `<option value="my_signal">` 即可。零配置、热插拔生效！

### 3.2 如何修改页面的配色、尺寸或布局？
* 所有 CSS 均已脱离 HTML！请前往 `frontend/css/style.css` 进行修改。
* **修改配色**：在文件顶部寻找 `:root` 变量池，例如 `--accent-color: #C95C16;`，修改此处将全局联动替换高亮色。
* **修改图表宽高**：查找 `.chart-container` 和 `.chart-box`，其采用了 CSS Grid + Flex 混合排版，修改栅格比例即可改变图表尺寸。

### 3.3 关于前端缓存强制刷新
* **重要规则**：由于浏览器缓存机制，每次您修改了 `js/*.js` 或 `css/*.css` 文件后，必须前往 `frontend/index.html`。
* 找到 `<link>` 和 `<script>` 标签后方的 `?v=x.x.x` 参数。
* 将其递增（例如从 `?v=6.0.0` 改为 `?v=6.0.1`），这会强制用户的浏览器穿透缓存拉取您最新的代码。
