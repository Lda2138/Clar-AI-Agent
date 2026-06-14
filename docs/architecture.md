# 📖 Clar AI 助教全栈系统架构设计

本文档详述《随机信号分析》AI 助教 Clar 系统的模块化架构、全局状态机定义、核心接口边界以及事件交互流向。随着系统版本的演进，核心代码已完成**深度解耦**（CSS 分离、后端引擎微服务化拆分），以解决项目各模块之间的复杂耦合，规范代码开发。

---

## 1. 全栈目录结构与领域划分

系统采用轻量级的前后端分离架构，通过 FastAPI 驱动后端引擎，Vanilla JS 驱动前端视图渲染。

```text
ClarAgent/
├── backend/                  # FastAPI 路由与通信网关
│   ├── server.py             # 核心服务主干，CORS 与路由注册
│   ├── models.py             # Pydantic 严格数据验证模型 (SignalParams, EnsembleParams 等)
│   └── signal_routes.py      # 信号流端点定义 (/api/signal/generate, /api/signal/ensemble)
├── core/                     # 后端核心计算引擎与 AI 逻辑
│   ├── signal_engine.py      # 【Facade 门面网关】向下调度各算法子模块
│   └── signal/               # 【重构解耦】的物理算法层
│       ├── generators.py     # 专职：各类确定性与随机波形的生成 (高斯、马尔可夫等)
│       ├── analyzers.py      # 专职：频域 FFT、功率谱 PSD、PDF 概率特征分析
│       └── filters.py        # 专职：滑动平均、维纳滤波、卡尔曼解算
├── frontend/                 # 纯原生前端 UI 层
│   ├── index.html            # 纯粹的 DOM 骨架 (HTML)
│   ├── css/                  # 【重构解耦】的全局与模块化样式表
│   │   └── style.css         # 抽离后的完整样式定义
│   └── js/                   # 模块化的原生 JS 引擎
│       ├── app.js            # 入口协调者
│       ├── ui.js             # UI 交互、参数采集、蒙特卡洛动画引擎
│       ├── charts.js         # 基于 Plotly 和 Echarts 的高速渐进式渲染引擎
│       ├── state.js          # 全局状态机 (State Machine) 注册表
│       └── ...               # (包含 chat.js, radar.js, telemetry.js 等独立微模块)
└── docs/                     # 系统维护说明文档与规范字典
```

---

## 2. 全局状态机 (State Machine)

系统的全局状态及公共配置集中定义在 `frontend/js/state.js` 中的常量对象 `S` 内。

| 状态变量 | 类型 | 描述 | 归属/管理模块 |
| :--- | :--- | :--- | :--- |
| `S.page` | `String` | 当前激活的选项卡页面名称（`signal-lab` \| `knowledge-map` 等） | `ui.js` |
| `S.aiMode` | `String` | 助教交互模式（`classic`：侧边栏 \| `clar-ball`：呼吸浮球） | `chat.js` |
| `S.signalData` | `Object` | 当前生成的单次时频域数据及特征集 | `ui.js` |
| `S.ensembleData`| `Object` | 蒙特卡洛平行宇宙的全部数据包 (ensembles_noisy, pdf_y) | `ui.js` |
| `S.ensembleRenderCount` | `Int` | 蒙特卡洛前端流式渲染计数器，用于动画帧控制 | `ui.js` |
| `S.filteredData` | `Object` | 滤波器运算后输出的滤噪波形 | `ui.js` |
| `S.chatHistory` | `Array` | 当前会话上下文，最大保留 10 轮交互 | `chat.js` |

---

## 3. 模块职责边界与数据流

### 3.1 界面交互路由层 (`ui.js`)
* **职责**：参数合法性校调、控制流分发。
* **主要 API**：
  * `generateSignal()`: 读取界面参数，请求后端引擎计算。
  * `generateEnsembleData()`: 发起极速蒙特卡洛请求，并**挂载定时器执行前端渐进式生长动画**。

### 3.2 仿真与动画渲染引擎 (`charts.js`)
* **职责**：处理庞大的数据阵列可视化，控制卡尔曼滤波与蒙特卡洛的高帧率刷新。
* **机制设计**：采用分离渲染逻辑。对于蒙特卡洛系综，通过动态获取 `S.ensembleRenderCount` 控制波形叠绘，并在前端通过 O(N) 级别原生运算实时累加计算 PDF 的密度收敛。

### 3.3 会话控制与主动诊断 (`chat.js` / `proactive_card.js`)
* **流转逻辑**：当 `ui.js` 检测到极端异常波形（如严重低信噪比被淹没）或算法卡顿，立即抛出隐式异常事件 -> `checkProactiveAI()` 拦截事件 -> 向后端 GPT-4 引擎请求诊断 -> `proactive_card.js` 唤出带有磨砂光感的左侧提示悬浮窗。

### 3.4 后端微计算层 (`core/signal/`)
* **流转逻辑**：
  * 路由层 `backend/signal_routes.py` 将 Pydantic 字典拆解，调用 `signal_engine.py` 的门面。
  * `generators.py` 根据 `signal_type` 映射函数。
  * **(针对极速模式)** 当路由到 `/api/signal/ensemble` 时，引擎会直接跨过 $O(N^2)$ 的 `analyzers.py`（避免 `np.correlate` 灾难），只用 `np.histogram` 返回收敛结果，保障毫秒级并发运算。
