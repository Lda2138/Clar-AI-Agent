// frontend/js/state.js
// ═══════════════════════════════════════════════
// 随机信号分析 AI 助教 Clar — 全局状态与基础配置
// ═══════════════════════════════════════════════

const PAGE_NAMES = { 'signal-lab': '信号工坊', 'knowledge-map': '知识图谱', 'toolbox': '工具箱', 'radar-tracking': '雷达追踪' };
const VERSION = '2.1.2';


const SIG_NODE_MAP = { 
    '正弦+白噪声': 'KP_CH2_01', 
    '窄带': 'KP_CH1_02', 
    '瑞利分布': 'KP_CH1_01', 
    '方波+白噪声': 'KP_CH2_01', 
    '线性调频(LFM)': 'KP_CH1_02',
    '高斯白噪声': 'KP_CH2_01',
    '一阶马尔可夫过程': 'KP_CH1_01',
    '三角波+白噪声': 'KP_CH2_01',
    '双频正弦+白噪声': 'KP_CH1_02'
};

const API_HEADERS = { 
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true'
};

// 全局状态机
const S = { 
    page: 'signal-lab', 
    signalData: null,
    ensembleData: null, 
    filteredData: null, 
    filterParams: null,
    kalmanParams: null,
    kalmanData: null,
    radarData: null,
    radarParams: null,
    currentNode: null, 
    graphNode: null, 
    allNodes: null, 
    allLinks: null, 
    isProgrammaticUpdate: false,
    activeControllers: {},
    chatHistory: [],
    aiMode: 'classic'
};

let primaryCardData = null;
let secondaryCardData = null;
let lastAiReply = "";
let graphChart = null;

const API_BASE = (
    window.location.protocol === 'file:' || 
    ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && window.location.port !== '8001')
) 
    ? 'http://127.0.0.1:8001' 
    : '';

async function api(url, opts = {}) {
    const res = await fetch(API_BASE + url, { headers: API_HEADERS, ...opts });
    if (!res.ok) {
        console.error(`API error: ${res.status} ${res.statusText} for ${url}`);
        return null;
    }
    try {
        return await res.json();
    } catch (e) {
        console.error(`API JSON parse error for ${url}:`, e);
        return null;
    }
}

// ✨ 核心机制：自适应高度重绘的流畅滚动路由器（解决 KaTeX 异步加载高度变化导致滚动条被截断的 Bug）
function scrollToMessage(element, container, offset = 76) {
    if (!element || !container) return;
    let lastHeight = element.offsetHeight;
    let checkCount = 0;
    
    const doScroll = () => {
        const containerRect = container.getBoundingClientRect();
        const elementRect = element.getBoundingClientRect();
        const newScrollTop = container.scrollTop + (elementRect.top - containerRect.top) - offset;
        container.scrollTo({
            top: newScrollTop,
            behavior: 'smooth'
        });
    };

    const checkAndScroll = () => {
        const currentHeight = element.offsetHeight;
        checkCount++;
        if (currentHeight !== lastHeight) {
            lastHeight = currentHeight;
            doScroll();
        }
        if (checkCount < 12) { // 持续监视 600 毫秒（每 50ms 轮询一次）
            setTimeout(checkAndScroll, 50);
        }
    };

    doScroll();
    setTimeout(checkAndScroll, 80);
}
