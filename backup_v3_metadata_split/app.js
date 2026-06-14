// ═══════════════════════════════════════════════
// 随机信号分析 AI 助教 Clar — 前端逻辑
// ═══════════════════════════════════════════════

const PAGE_NAMES = { 'signal-lab': '信号工坊', 'knowledge-map': '知识图谱', 'toolbox': '工具箱' };
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

const S = { page: 'signal-lab', signalData: null, filteredData: null, currentNode: null, graphNode: null, allNodes: null, allLinks: null, isProgrammaticUpdate: false, uiMode: 'classic' };
let primaryCardData = null;
let secondaryCardData = null;
let lastAiReply = "";

// LocalStorage keys for independent chats
const CLASSIC_HISTORY_KEY = 'clar_classic_history_v1';
const ALL_SESSIONS_KEY = 'clar_all_sessions_v1';
const CURRENT_ALL_SESSION_ID_KEY = 'clar_current_all_session_id_v1';

S.classicMessages = [];
S.allSessions = [];
S.currentAllSessionId = '';

function loadChatHistory() {
    try {
        S.classicMessages = [];
        
        const allSessionsRaw = localStorage.getItem(ALL_SESSIONS_KEY);
        S.allSessions = allSessionsRaw ? JSON.parse(allSessionsRaw) : [];
        
        S.currentAllSessionId = localStorage.getItem(CURRENT_ALL_SESSION_ID_KEY) || '';
        
        if (S.allSessions.length === 0) {
            createNewAllSession(false);
        } else if (!S.currentAllSessionId || !S.allSessions.some(s => s.id === S.currentAllSessionId)) {
            S.currentAllSessionId = S.allSessions[0].id;
        }
    } catch (e) {
        console.error("Failed to load chat history:", e);
        S.classicMessages = [];
        S.allSessions = [];
        createNewAllSession(false);
    }
}

function saveChatHistory() {
    try {
        localStorage.setItem(CLASSIC_HISTORY_KEY, JSON.stringify([]));
        localStorage.setItem(ALL_SESSIONS_KEY, JSON.stringify(S.allSessions || []));
        localStorage.setItem(CURRENT_ALL_SESSION_ID_KEY, S.currentAllSessionId || '');
    } catch (e) {
        console.error("Failed to save chat history:", e);
    }
}

function createNewAllSession(shouldRender = true) {
    const newId = 'session-' + Date.now() + '-' + Math.random().toString(36).substring(2, 7);
    const newSession = {
        id: newId,
        title: '新对话',
        messages: [],
        timestamp: Date.now()
    };
    if (!S.allSessions) S.allSessions = [];
    S.allSessions.unshift(newSession);
    S.currentAllSessionId = newId;
    
    saveChatHistory();
    
    if (shouldRender) {
        const searchInput = document.getElementById('sidebar-search');
        if (searchInput) searchInput.value = '';
        renderSessionList();
        renderMessages();
    }
    return newSession;
}

function deleteSession(sessionId, event) {
    if (event) event.stopPropagation();
    
    const index = S.allSessions.findIndex(s => s.id === sessionId);
    if (index === -1) return;
    
    S.allSessions.splice(index, 1);
    
    if (S.currentAllSessionId === sessionId) {
        if (S.allSessions.length > 0) {
            S.currentAllSessionId = S.allSessions[0].id;
        } else {
            createNewAllSession(false);
        }
    }
    
    saveChatHistory();
    renderSessionList();
    renderMessages();
}

function switchSession(sessionId) {
    if (S.currentAllSessionId === sessionId) return;
    S.currentAllSessionId = sessionId;
    saveChatHistory();
    renderSessionList();
    renderMessages();
}

function renderSessionList(filterQuery = '') {
    const container = document.getElementById('session-list-container');
    if (!container) return;
    
    container.innerHTML = '';
    const sessionsToRender = S.allSessions.filter(s => {
        if (!filterQuery) return true;
        const query = filterQuery.toLowerCase();
        const titleMatch = s.title.toLowerCase().includes(query);
        const messageMatch = s.messages.some(m => m.content.toLowerCase().includes(query));
        return titleMatch || messageMatch;
    });
    
    if (sessionsToRender.length === 0) {
        container.innerHTML = `<div style="text-align:center; padding:20px; font-size:12px; color:var(--text-muted);">未找到匹配的对话</div>`;
        return;
    }
    
    sessionsToRender.forEach(s => {
        const isActive = s.id === S.currentAllSessionId;
        const item = document.createElement('div');
        item.className = `session-item ${isActive ? 'active' : ''}`;
        item.onclick = () => switchSession(s.id);
        
        item.innerHTML = `
            <div class="session-title" title="${s.title}">${s.title}</div>
            <button class="session-delete-btn" onclick="deleteSession('${s.id}', event)">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
            </button>
        `;
        container.appendChild(item);
    });
}

function filterAllSessions() {
    const query = document.getElementById('sidebar-search').value;
    renderSessionList(query);
}

function renderMessages() {
    const messagesEl = document.getElementById('chat-messages');
    if (!messagesEl) return;
    
    messagesEl.innerHTML = '';
    
    let msgs = [];
    if (S.uiMode === 'classic') {
        msgs = S.classicMessages || [];
    } else {
        const session = S.allSessions.find(s => s.id === S.currentAllSessionId);
        msgs = session ? (session.messages || []) : [];
    }
    
    if (msgs.length === 0) {
        const welcomeText = S.uiMode === 'classic' 
            ? '您好！我是《随机信号分析》AI 助教 Clar，先生成信号或直接向我提问即可开始。'
            : '您好！我是《随机信号分析》AI 助教 Clar，在 Clar-all 模式下，我会全自动帮您生成信号、运行滤波和展示对比结果，快向我提问吧！';
        
        messagesEl.innerHTML = `
            <div class="chat-msg assistant">
                <div class="bubble">${welcomeText}</div>
            </div>
        `;
        return;
    }
    
    msgs.forEach((m, idx) => {
        const msgId = `msg-rendered-${idx}-${m.role === 'user' ? 'U' : 'A'}`;
        if (m.role === 'user') {
            const safeText = m.content.replace(/</g, '&lt;').replace(/>/g, '&gt;');
            const userMsgHtml = renderMarkdown(safeText);
            messagesEl.insertAdjacentHTML('beforeend', `
                <div class="chat-msg user" id="${msgId}">
                    <div class="bubble">${userMsgHtml}</div>
                </div>
            `);
            const el = document.getElementById(msgId);
            if (el) renderMath(el);
        } else {
            messagesEl.insertAdjacentHTML('beforeend', `
                <div class="chat-msg assistant" id="${msgId}">
                    <div class="bubble"></div>
                </div>
            `);
            const el = document.getElementById(msgId);
            const bubbleEl = el ? el.querySelector('.bubble') : null;
            if (bubbleEl) {
                let text = m.content;
                if (S.uiMode === 'classic') {
                    text = text.replace(/<div class="ai-chart"[^>]*><\/div>/g, '');
                }
                renderAndAttach(bubbleEl, text, m.quick_questions || [], S.uiMode === 'classic' ? 'signal-lab' : 'toolbox', m);
            }
        }
    });
    
    messagesEl.scrollTop = messagesEl.scrollHeight;
    
    // Update outline navigation
    updateOutlineNav();
}

function updateOutlineNav() {
    const outlineContainer = document.getElementById('chat-outline-nav');
    if (!outlineContainer) return;
    
    outlineContainer.innerHTML = '';
    
    if (S.uiMode !== 'all') {
        return;
    }
    
    const session = S.allSessions.find(s => s.id === S.currentAllSessionId);
    const msgs = session ? (session.messages || []) : [];
    
    const userMsgs = [];
    msgs.forEach((m, idx) => {
        if (m.role === 'user') {
            userMsgs.push({
                content: m.content,
                index: idx,
                id: `msg-rendered-${idx}-U`
            });
        }
    });
    
    if (userMsgs.length === 0) {
        return;
    }
    
    userMsgs.forEach(um => {
        const item = document.createElement('div');
        item.className = 'outline-item';
        
        // Clean question text for label
        let cleanText = um.content.replace(/<[^>]*>/g, '').replace(/[\#\*\`]/g, '').trim();
        const firstLine = cleanText.split('\n')[0].trim();
        cleanText = firstLine.length > 15 ? firstLine.substring(0, 15) + '...' : firstLine;
        
        item.innerHTML = `
            <div class="outline-label" title="${um.content.replace(/"/g, '&quot;')}">${cleanText}</div>
            <div class="outline-dash"></div>
        `;
        
        item.onclick = (e) => {
            e.stopPropagation();
            const targetEl = document.getElementById(um.id);
            const containerEl = document.getElementById('chat-messages');
            if (targetEl && containerEl) {
                scrollToMessage(targetEl, containerEl);
                document.querySelectorAll('.outline-item').forEach(el => el.classList.remove('active'));
                item.classList.add('active');
            }
        };
        
        outlineContainer.appendChild(item);
    });
    
    syncActiveOutlineItem();
}

function syncActiveOutlineItem() {
    const container = document.getElementById('chat-messages');
    const outlineContainer = document.getElementById('chat-outline-nav');
    if (!container || !outlineContainer) return;
    
    const items = outlineContainer.querySelectorAll('.outline-item');
    if (items.length === 0) return;
    
    const session = S.allSessions.find(s => s.id === S.currentAllSessionId);
    const msgs = session ? (session.messages || []) : [];
    
    const userMsgs = [];
    msgs.forEach((m, idx) => {
        if (m.role === 'user') {
            userMsgs.push({
                id: `msg-rendered-${idx}-U`
            });
        }
    });
    
    if (userMsgs.length === 0) return;
    
    let activeIdx = 0;
    const containerRect = container.getBoundingClientRect();
    
    for (let i = 0; i < userMsgs.length; i++) {
        const el = document.getElementById(userMsgs[i].id);
        if (el) {
            const elRect = el.getBoundingClientRect();
            if (elRect.top - containerRect.top < 150) {
                activeIdx = i;
            } else {
                break;
            }
        }
    }
    
    items.forEach((item, idx) => {
        if (idx === activeIdx) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

const API_BASE = (
    window.location.protocol === 'file:' || 
    ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && window.location.port !== '8001')
) 
    ? 'http://127.0.0.1:8001' 
    : '';

async function api(url, opts = {}) {
    const res = await fetch(API_BASE + url, { headers: API_HEADERS, ...opts });
    return res.json();
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

function cleanMarkdown(text) {
    if (!text) return '';
    return text.replace(/<invoke [^>]*>[\s\S]*?<\/invoke>/gi, '').replace(/<parameter [^>]*>[\s\S]*?<\/parameter>/gi, '').trim();
}

function renderMarkdown(text) {
    text = cleanMarkdown(text);
    if (!text) return '';
    let mathBlocks = [];
    const mathRegex = /(\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\)|(?<!\$)\$[^$]+?\$(?!\$))/g;
    text = text.replace(mathRegex, match => {
        mathBlocks.push(match);
        return `%%%MATH_BLOCK_${mathBlocks.length - 1}%%%`;
    });
    let html = text;
    if (typeof marked !== 'undefined') {
        try {
            html = marked.parse(text);
        } catch (e) {
            console.error("marked.parse error:", e);
            html = text;
        }
    }
    mathBlocks.forEach((block, i) => {
        html = html.replace(`%%%MATH_BLOCK_${i}%%%`, () => block);
    });
    return `<div class="markdown-body">${html}</div>`;
}

// ✨ 核心修复：用于按钮等行内元素的 markdown 解析，剥离 block 容器
function renderInlineMarkdown(text) {
    let html = renderMarkdown(text);
    html = html.replace(/^<div class="markdown-body">/, '').replace(/<\/div>$/, '');
    html = html.replace(/^<p>/, '').replace(/<\/p>$/, '');
    return html.trim();
}

function renderMath(el) {
    if (typeof renderMathInElement === 'undefined') {
        console.error("renderMathInElement is not defined!");
        fetch(API_BASE + '/api/log', {
            method: 'POST',
            headers: API_HEADERS,
            body: JSON.stringify({message: "renderMathInElement is not defined!"})
        }).catch(e => {});
        return;
    }
    try {
        renderMathInElement(el, {
            delimiters: [
                {left: '$$', right: '$$', display: true},
                {left: '$', right: '$', display: false},
                {left: '\\(', right: '\\)', display: false},
                {left: '\\[', right: '\\]', display: true}
            ],
            throwOnError: false,
            trust: true
        });
    } catch(e) {
        console.warn("KaTeX render issue:", e);
        fetch(API_BASE + '/api/log', {
            method: 'POST',
            headers: API_HEADERS,
            body: JSON.stringify({message: "KaTeX render issue: " + e.message, error: e.stack})
        }).catch(e => {});
    }
}

// ✨ 核心机制：整合 Markdown、Math 和 追问 的渲染管道
function renderAndAttach(element, markdownText, quickQuestions = [], targetPage = null, msgObj = null) {
    element.innerHTML = renderMarkdown(markdownText);
    renderMath(element);

    // Parse and render inline charts/graphs (for Clar-all mode)
    renderInlineCharts(element, msgObj);

    if (!quickQuestions || quickQuestions.length === 0) {
        quickQuestions = [
            "这个概念在随机信号处理中的物理含义是什么？",
            "能否为我提供一个典型的工程应用场景？",
            "有关于这个知识点的 Python 仿真代码示例吗？"
        ];
    }

    if (quickQuestions && quickQuestions.length > 0) {
        const qContainer = document.createElement('div');
        qContainer.className = 'quick-qs';
        quickQuestions.forEach(q => {
            const btn = document.createElement('button');
            btn.className = 'quick-ask-btn';
            // 解析数学公式并填入按钮
            btn.innerHTML = renderInlineMarkdown(q);
            btn.onclick = () => quickAsk(q, targetPage);
            qContainer.appendChild(btn);
        });
        element.appendChild(qContainer);
        // 对插入的按钮触发二次 Math 渲染保证公式解析
        renderMath(qContainer);
    }
}

// ==========================================
// Clar-all Mode Inline Chart Renderers
// ==========================================
function renderInlineCharts(container, msgObj = null) {
    const chartEls = container.querySelectorAll('.ai-chart');
    chartEls.forEach(el => {
        const type = el.getAttribute('data-type');
        const subtype = el.getAttribute('data-subtype') || '';
        
        el.style.width = '100%';
        el.style.height = '240px';
        el.style.marginTop = '12px';
        el.style.marginBottom = '12px';
        el.style.borderRadius = '12px';
        el.style.background = 'rgba(255, 255, 255, 0.2)';
        el.style.border = '1px solid rgba(255, 255, 255, 0.4)';
        el.style.boxShadow = 'inset 0 1px 2px rgba(255, 255, 255, 0.3), 0 4px 12px rgba(0,0,0,0.02)';
        el.style.overflow = 'hidden';
        el.style.position = 'relative';

        el.innerHTML = '<div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); color:var(--text-muted); font-size:12px; font-weight:600;"><div class="typing-dots"><span></span><span></span><span></span></div> 图表加载中...</div>';

        const chartId = 'inline-chart-' + Math.random().toString(36).substr(2, 9);
        el.id = chartId;

        setTimeout(() => {
            try {
                if (type === 'time-domain') {
                    renderTimeDomainInline(chartId, subtype, msgObj);
                } else if (type === 'freq-domain') {
                    renderFreqDomainInline(chartId, subtype, msgObj);
                } else if (type === 'filter') {
                    renderFilterInline(chartId, msgObj);
                } else if (type === 'kalman') {
                    renderKalmanInline(chartId, msgObj);
                } else if (type === 'knowledge-map') {
                    renderKnowledgeMapInline(chartId, msgObj);
                } else {
                    el.innerHTML = '<div style="padding:20px; color:red; font-size:12px;">未知图表类型</div>';
                }
            } catch (err) {
                console.error("渲染行内图表失败:", err);
                el.innerHTML = '<div style="padding:20px; color:red; font-size:12px;">图表渲染失败: ' + err.message + '</div>';
            }
        }, 100);
    });
}

function updateInlineCharts() {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    const chartEls = container.querySelectorAll('.ai-chart[data-waiting="true"]');
    chartEls.forEach(el => {
        const type = el.getAttribute('data-type');
        const subtype = el.getAttribute('data-subtype') || '';
        const chartId = el.id;
        if (!chartId) return;
        
        try {
            if (type === 'time-domain' && S.signalData) {
                renderTimeDomainInline(chartId, subtype);
            } else if (type === 'freq-domain' && S.signalData) {
                renderFreqDomainInline(chartId, subtype);
            } else if (type === 'filter' && S.filteredData) {
                renderFilterInline(chartId);
            } else if (type === 'kalman' && S.kalmanData) {
                renderKalmanInline(chartId);
            }
        } catch (err) {
            console.error("更新行内图表失败:", err);
        }
    });
}

function renderTimeDomainInline(containerId, subtype, msgObj = null) {
    const el = document.getElementById(containerId);
    if (!el) return;
    const data = (msgObj && msgObj.signalData) ? msgObj.signalData : S.signalData;
    if (!data) {
        el.setAttribute('data-waiting', 'true');
        el.innerHTML = '<div style="padding:20px; color:#e67e22; font-size:12.5px; font-weight:600; text-align:center; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:100%;"><div class="typing-dots"><span></span><span></span><span></span></div> 📡 观测序列生成中，请稍候...</div>';
        return;
    }
    el.setAttribute('data-rendered', 'true');
    el.removeAttribute('data-waiting');
    el.innerHTML = '';
    const baseLayout = {
        margin: { l: 40, r: 15, t: 15, b: 35 }, autosize: true, showlegend: true,
        legend: { orientation: 'h', y: 1.25, font: { size: 9 } },
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        yaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 9 }, zeroline: false, showline: false }
    };
    let traces = [];
    let layout = { ...baseLayout };
    
    if (subtype === 'autocorr') {
        layout.xaxis = { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 9 }, title: { text: '延时 τ (s)', font: { size: 9 } }, zeroline: false, showline: false };
        traces = [{ y: data.autocorr, x: data.autocorr_lags, name: '自相关 Rx(τ)', line: { width: 1.5, color: '#e67e22' } }];
    } else if (subtype === 'crosscorr') {
        layout.xaxis = { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 9 }, title: { text: '延时 τ (s)', font: { size: 9 } }, zeroline: false, showline: false };
        traces = [{ y: data.crosscorr || [], x: data.crosscorr_lags || [], name: '互相关 Rsx(τ)', line: { width: 1.5, color: '#9b59b6' } }];
    } else if (subtype === 'pdf') {
        layout.xaxis = { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 9 }, title: { text: '幅度', font: { size: 9 } }, zeroline: false, showline: false };
        traces = [
            { x: data.pdf_x, y: data.pdf_y, type: 'bar', name: '观测 PDF', marker: { color: 'rgba(231, 76, 60, 0.6)' } }
        ];
        if (data.pdf_x_clean) {
            traces.push({ x: data.pdf_x_clean, y: data.pdf_y_clean, mode: 'lines', name: '纯净 PDF', line: { width: 1.5, color: '#4285f4' } });
        }
    } else { // waveform
        const type = data.signal_type || (document.getElementById('sig-type') ? document.getElementById('sig-type').value : '');
        const freq = data.freq || (parseFloat(document.getElementById('sig-freq') ? document.getElementById('sig-freq').value : 200) || 200);
        const tMax = (type === '线性调频(LFM)' || type === '瑞利分布' || type === '高斯白噪声' || type === '一阶马尔可夫过程')
            ? data.t[data.t.length - 1]
            : Math.min(data.t[data.t.length - 1], Math.max(0.01, 8 / freq));
        layout.xaxis = { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 9 }, range: [0, tMax], zeroline: false, showline: false };
        traces = [
            { y: data.clean_fine || data.clean, x: data.t_fine || data.t, name: '纯净 s(t)', line: { width: 1.5, color: '#4285f4' } },
            { y: data.noisy_fine || data.noisy, x: data.t_fine || data.t, name: '观测 X(t)', line: { width: 1, color: '#e74c3c' } }
        ];
    }
    Plotly.newPlot(containerId, traces, layout, { responsive: true, displayModeBar: false });
}

function renderFreqDomainInline(containerId, subtype, msgObj = null) {
    const el = document.getElementById(containerId);
    if (!el) return;
    const data = (msgObj && msgObj.signalData) ? msgObj.signalData : S.signalData;
    if (!data) {
        el.setAttribute('data-waiting', 'true');
        el.innerHTML = '<div style="padding:20px; color:#e67e22; font-size:12.5px; font-weight:600; text-align:center; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:100%;"><div class="typing-dots"><span></span><span></span><span></span></div> 📡 频谱计算中，请稍候...</div>';
        return;
    }
    el.setAttribute('data-rendered', 'true');
    el.removeAttribute('data-waiting');
    el.innerHTML = '';
    const baseLayout = {
        margin: { l: 40, r: 15, t: 15, b: 35 }, autosize: true, showlegend: true,
        legend: { orientation: 'h', y: 1.25, font: { size: 9 } },
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        yaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 9 }, zeroline: false, showline: false }
    };
    let traces = [];
    let layout = { ...baseLayout };
    
    if (subtype === 'amplitude') {
        layout.xaxis = { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 9 }, title: { text: '频率 (Hz)', font: { size: 9 } }, zeroline: false, showline: false };
        traces = [
            { y: data.spec_clean, x: data.freqs, name: '|S(f)|', line: { width: 1.5, color: '#27ae60' } },
            { y: data.spec_noisy, x: data.freqs, name: '|X(f)|', line: { width: 1, color: '#e74c3c' } }
        ];
    } else if (subtype === 'phase') {
        layout.xaxis = { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 9 }, title: { text: '频率 (Hz)', font: { size: 9 } }, zeroline: false, showline: false };
        traces = [
            { y: data.phase_noisy, x: data.freqs, name: 'θx(f)', line: { width: 1, color: '#e74c3c', opacity: 0.7 } }
        ];
        if (data.phase_clean) {
            traces.push({ y: data.phase_clean, x: data.freqs, name: 'θs(f)', line: { width: 1.5, color: '#2980b9' } });
        }
    } else { // psd
        layout.xaxis = { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 9 }, title: { text: '频率 (Hz)', font: { size: 9 } }, zeroline: false, showline: false };
        traces = [];
        if (data.psd_clean) {
            traces.push({ y: data.psd_clean, x: data.psd_freqs, name: 'Gs(f)', line: { width: 1.5, color: '#27ae60' } });
        }
        traces.push({ y: data.psd_noisy, x: data.psd_freqs, name: 'Gx(f)', line: { width: 1, color: '#e74c3c' } });
    }
    Plotly.newPlot(containerId, traces, layout, { responsive: true, displayModeBar: false });
}

function renderFilterInline(containerId, msgObj = null) {
    const el = document.getElementById(containerId);
    if (!el) return;
    const data = (msgObj && msgObj.filteredData) ? msgObj.filteredData : S.filteredData;
    if (!data) {
        el.setAttribute('data-waiting', 'true');
        el.innerHTML = '<div style="padding:20px; color:#e67e22; font-size:12.5px; font-weight:600; text-align:center; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:100%;"><div class="typing-dots"><span></span><span></span><span></span></div> ⚙️ 滤波分析运行中，请稍候...</div>';
        return;
    }
    el.setAttribute('data-rendered', 'true');
    el.removeAttribute('data-waiting');
    el.innerHTML = '';
    const layout = {
        margin: { l: 40, r: 15, t: 15, b: 35 }, autosize: true, showlegend: true,
        legend: { orientation: 'h', y: 1.25, font: { size: 9 } },
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        xaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 9 }, range: [0, data.t[data.t.length - 1] / 4], zeroline: false, showline: false },
        yaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 9 }, zeroline: false, showline: false }
    };
    const traces = [
        { y: data.noisy, x: data.t, name: '滤波前 X(t)', line: { width: 1, color: '#e74c3c', opacity: 0.5 } },
        { y: data.filtered, x: data.t, name: '滤波后 Y(t)', line: { width: 1.5, color: '#2ecc71' } }
    ];
    if (data.clean) {
        traces.push({ y: data.clean, x: data.t, name: '真实 s(t)', line: { width: 1.2, color: '#4285f4', dash: 'dash' } });
    }
    Plotly.newPlot(containerId, traces, layout, { responsive: true, displayModeBar: false });
}

function renderKalmanInline(containerId, msgObj = null) {
    const el = document.getElementById(containerId);
    if (!el) return;
    const data = (msgObj && msgObj.kalmanData) ? msgObj.kalmanData : S.kalmanData;
    if (!data) {
        el.setAttribute('data-waiting', 'true');
        el.innerHTML = '<div style="padding:20px; color:#e67e22; font-size:12.5px; font-weight:600; text-align:center; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:100%;"><div class="typing-dots"><span></span><span></span><span></span></div> ⚙️ 卡尔曼递归估计运行中，请稍候...</div>';
        return;
    }
    el.setAttribute('data-rendered', 'true');
    el.removeAttribute('data-waiting');
    el.innerHTML = '';
    const layout = {
        margin: { l: 40, r: 15, t: 15, b: 35 }, autosize: true, showlegend: true,
        legend: { orientation: 'h', y: 1.25, font: { size: 9 } },
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        xaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 9 }, zeroline: false, showline: false },
        yaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 9 }, zeroline: false, showline: false }
    };
    const traces = [
        { y: data.true_pos, x: data.t, name: '真实位置', line: { width: 1.5, color: '#2ecc71' } },
        { y: data.obs_pos, x: data.t, name: '观测样本', mode: 'markers', marker: { size: 3, color: '#e74c3c', opacity: 0.6 } },
        { y: data.est_pos, x: data.t, name: '估计位置', line: { width: 1.5, color: '#3498db' } }
    ];
    Plotly.newPlot(containerId, traces, layout, { responsive: true, displayModeBar: false });
}

async function renderKnowledgeMapInline(containerId, msgObj = null) {
    const el = document.getElementById(containerId);
    if (!el) return;
    
    if (!S.allNodes) {
        try {
            const data = await api('/api/knowledge/graph');
            S.allNodes = data.nodes;
            S.allLinks = data.links;
        } catch(e) {
            el.innerHTML = '<div style="padding:20px; color:red; font-size:11px;">加载图谱数据失败: ' + e.message + '</div>';
            return;
        }
    }
    
    el.innerHTML = '';
    const graphInstance = echarts.init(el);
    const activeNodeId = (msgObj && msgObj.nodeId) ? msgObj.nodeId : S.currentNode;
    let activeNodeName = "";
    if (activeNodeId && S.allNodes) {
        const matched = S.allNodes.find(n => n.kp_node_id === activeNodeId || n.id === activeNodeId);
        if (matched) activeNodeName = matched.name;
    }
    const activeCardTitle = activeNodeName || (secondaryCardData ? secondaryCardData.title : "");
    let hasFixedActive = false;
    
    const mappedNodes = S.allNodes.map(n => {
        const isActive = (n.kp_node_id && n.kp_node_id === activeNodeId) || 
                         (activeNodeName && (n.name === activeNodeName || n.name.includes(activeNodeName) || activeNodeName.includes(n.name))) ||
                         (activeCardTitle && (n.name === activeCardTitle || n.name.includes(activeCardTitle) || activeCardTitle.includes(n.name)));
        const shouldFix = isActive && !hasFixedActive;
        if (shouldFix) hasFixedActive = true;
        
        return {
            id: n.id,
            name: n.name,
            symbolSize: isActive ? (n.symbolSize * 1.5) : (n.symbolSize * 1.0),
            category: n.category === 0 ? '章节' : n.category === 1 ? '小节' : '核心知识点',
            itemStyle: {
                color: isActive ? '#f59e0b' : n.itemStyle.color,
                shadowBlur: isActive ? 15 : 4,
                shadowColor: isActive ? '#f59e0b' : 'rgba(0,0,0,0.1)'
            },
            label: {
                show: isActive || n.category < 2,
                position: 'right',
                fontSize: isActive ? 10 : 8,
                color: isActive ? '#d97706' : '#5c6479'
            },
            node_type: n.node_type,
            chapter: n.chapter,
            section: n.section,
            topics: n.topics,
            kp_node_id: n.kp_node_id,
            fixed: shouldFix,
            x: shouldFix ? 0 : undefined,
            y: shouldFix ? 0 : undefined
        };
    });
    
    const option = {
        tooltip: {
            trigger: 'item',
            formatter: function (params) {
                if (params.dataType === 'node') {
                    return `<div style="font-weight:600;font-size:11px;">${params.data.name}</div>`;
                }
                return '';
            }
        },
        series: [{
            type: 'graph',
            layout: 'force',
            data: mappedNodes,
            links: S.allLinks,
            categories: [{ name: '章节' }, { name: '小节' }, { name: '核心知识点' }],
            roam: true,
            force: { repulsion: 80, edgeLength: 45, gravity: 0.08 },
            lineStyle: { color: 'rgba(0,0,0,0.1)', width: 1.0, curveness: 0.05 }
        }]
    };
    graphInstance.setOption(option);
    
    graphInstance.on('click', function(params) {
        if (document.body.classList.contains('chat-locked')) return;
        if (params.dataType === 'node' && params.data) {
            const node = params.data;
            if (node.node_type === 'chapter') {
                sendChat(`我想学习《随机信号分析》大纲中的章节：【${node.name}】。`);
            } else if (node.node_type === 'section') {
                sendChat(`我想学习小节：【${node.name}】（属于章节：${node.chapter}）。`);
            } else {
                if (node.kp_node_id) {
                    S.currentNode = node.kp_node_id;
                    S.graphNode = node.name;
                    fetchNodeAndShowCard(node.kp_node_id);
                }
                sendChat(`请帮我深入剖析核心知识点：【${node.name}】。`);
            }
        }
    });
}

function updateControlVisibility() {
    const type = document.getElementById('sig-type').value;
    const bwCtrl = document.getElementById('ctrl-bandwidth');
    const feCtrl = document.getElementById('ctrl-freq-end');
    const maCtrl = document.getElementById('ctrl-markov-a');
    const f2Ctrl = document.getElementById('ctrl-freq2');
    const freqInput = document.getElementById('sig-freq');
    const freqCtrl = freqInput ? freqInput.closest('.ctrl-item') : null;

    if (!bwCtrl || !feCtrl || !maCtrl || !f2Ctrl) return;

    // Reset displays
    bwCtrl.style.display = 'none';
    feCtrl.style.display = 'none';
    maCtrl.style.display = 'none';
    f2Ctrl.style.display = 'none';
    if (freqCtrl) freqCtrl.style.display = 'flex';

    if (type === '窄带' || type === '瑞利分布') {
        bwCtrl.style.display = 'flex';
    } else if (type === '线性调频(LFM)') {
        feCtrl.style.display = 'flex';
    } else if (type === '一阶马尔可夫过程') {
        maCtrl.style.display = 'flex';
        if (freqCtrl) freqCtrl.style.display = 'none';
    } else if (type === '双频正弦+白噪声') {
        f2Ctrl.style.display = 'flex';
    } else if (type === '高斯白噪声') {
        if (freqCtrl) freqCtrl.style.display = 'none';
    }
}

let autoGenTimer = null;
function autoGenerate() {
    updateControlVisibility();
    if (S.isProgrammaticUpdate) return;
    clearTimeout(autoGenTimer);
    autoGenTimer = setTimeout(() => generateSignal(), 500);
}

// ✨ 核心修复：采样率与频率联动判定（考虑不同信号的实际最高频率，避免 aliasing 误判）
function checkNyquist(freq, fs) {
    const type = document.getElementById('sig-type') ? document.getElementById('sig-type').value : '';
    if (type === '高斯白噪声' || type === '一阶马尔可夫过程') return { ok: true };
    if (!Number.isFinite(freq) || !Number.isFinite(fs) || fs <= 0) return { ok: true };
    let fMax = freq;
    if (type === '线性调频(LFM)') {
        const feVal = parseFloat(document.getElementById('sig-freq-end').value);
        fMax = Number.isFinite(feVal) ? feVal : (freq + 100.0);
    } else if (type === '窄带') {
        const bwVal = parseFloat(document.getElementById('sig-bandwidth').value);
        fMax = freq + (Number.isFinite(bwVal) ? bwVal : 50.0) / 2;
    } else if (type === '双频正弦+白噪声') {
        const f2Val = parseFloat(document.getElementById('sig-freq2').value) || 300;
        fMax = Math.max(freq, f2Val);
    }
    const ratio = fs / fMax;
    if (ratio < 2) return { ok: false, level: 'alias', msg: `采样率 ${fs} Hz 已低于临界 Nyquist 频率 2×${fMax.toFixed(0)}=${(2*fMax).toFixed(0)} Hz，将出现频谱混叠。` };
    if (ratio < 4) return { ok: false, level: 'warn',  msg: `采样率 ${fs} Hz 接近 Nyquist 下限（${(2*fMax).toFixed(0)} Hz），波形重建分辨率可能不足。` };
    return { ok: true };
}

// 频率变化时：仅在采样率明显违反奈奎斯特时轻量提示，不再覆盖用户的手动设定
function syncSampleRate() {
    const freqInput = document.getElementById('sig-freq');
    const fsInput = document.getElementById('sig-fs');
    const freq = parseFloat(freqInput.value) || 200;
    const currentFs = parseInt(fsInput.value) || 10000;
    applyFsVisualState(checkNyquist(freq, currentFs), fsInput);
    autoGenerate();
}

// 采样率变化时：校验奈奎斯特并触发重绘 + AI 联动
function validateSampleRate() {
    const freq = parseFloat(document.getElementById('sig-freq').value) || 200;
    const fsInput = document.getElementById('sig-fs');
    const fs = parseInt(fsInput.value);
    applyFsVisualState(checkNyquist(freq, fs), fsInput);
    autoGenerate();
}

function applyFsVisualState(state, fsInput) {
    if (!fsInput) return;
    if (state.ok) {
        fsInput.style.color = '';
        fsInput.style.background = '';
        fsInput.title = '';
    } else if (state.level === 'alias') {
        fsInput.style.color = '#c0392b';
        fsInput.style.background = 'rgba(231,76,60,0.10)';
        fsInput.title = state.msg;
    } else {
        fsInput.style.color = '#b7791f';
        fsInput.style.background = 'rgba(245,158,11,0.08)';
        fsInput.title = state.msg;
    }
}

function navigate(pageId) {
    if (S.page === pageId) return; // ✨ 核心：避免当前页面下的重复导航及 ECharts 图谱重新渲染/刷新！
    S.page = pageId;
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('page-' + pageId).classList.add('active');
    document.querySelectorAll('#bottom-bar .tab-item').forEach(btn => btn.classList.toggle('active', btn.dataset.page === pageId));
    if (pageId === 'knowledge-map') setTimeout(renderGraph, 200);
}

function saveModeInputs(mode) {
    const state = {};
    const ids = [
        'sig-type', 'sig-freq', 'sig-fs', 'sig-snr', 'sig-bandwidth', 
        'sig-freq-end', 'sig-markov-a', 'sig-freq2', 
        'filter-window-size', 'filter-cutoff', 
        'kalman-q', 'kalman-r', 'kalman-v0'
    ];
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            state[id] = el.value;
        }
    });
    if (mode === 'classic') {
        S.classicInputs = state;
    } else {
        S.allInputs = state;
    }
}

function restoreModeInputs(mode) {
    const state = (mode === 'classic') ? S.classicInputs : S.allInputs;
    if (!state) return;
    Object.keys(state).forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.value = state[id];
        }
    });
    updateControlVisibility();
}

function replotClassicWorkspace() {
    if (S.signalData) {
        updateTimePlot();
        updateFreqPlot();
        renderMetrics(S.signalData.features, {
            freq: parseFloat(document.getElementById('sig-freq').value) || 200,
            fs: parseInt(document.getElementById('sig-fs').value) || 10000
        });
    } else {
        const metricsEl = document.getElementById('signal-metrics');
        if (metricsEl) metricsEl.style.display = 'none';
        Plotly.purge('waveform-plot');
        Plotly.purge('spectrum-plot');
    }
    
    if (S.filteredData && S.filterParams) {
        document.getElementById('filter-result').style.display = 'flex';
        const filterNames = { 'moving_average': '滑动平均滤波器输出', 'rc_lowpass': 'RC低通滤波器输出', 'wiener': '自适应维纳滤波最佳线性估计输出' };
        document.getElementById('filter-title').innerText = filterNames[S.filterParams.filter_type] || '线性系统输出特性';
        
        const el = document.getElementById('filter-plot');
        Plotly.purge(el);
        
        const freq = parseFloat(document.getElementById('sig-freq').value) || 200;
        const sigType = document.getElementById('sig-type').value;
        const tMax = (sigType === '线性调频(LFM)' || sigType === '瑞利分布')
            ? S.signalData.t[S.signalData.t.length - 1]
            : Math.min(S.signalData.t[S.signalData.t.length - 1], Math.max(0.01, 8 / freq));
        const fs = parseInt(document.getElementById('sig-fs').value) || 10000;
        const visibleSamplesCount = tMax * fs;

        const layout = { 
            height: 270,
            margin: { l: 40, r: 15, t: 15, b: 35 }, 
            paper_bgcolor: 'transparent', 
            plot_bgcolor: 'transparent',
            xaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, range: [0, tMax], zeroline: false, showline: false },
            yaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, zeroline: false, showline: false },
            showlegend: true,
            legend: { orientation: 'h', y: 1.15, font: { size: 10 } }
        };

        const filterTraces = [
            { 
                y: S.filteredData.noisy_fine || S.filteredData.noisy, 
                x: S.filteredData.t_fine || S.signalData.t, 
                name: '输入信号 X(t)', 
                line: { width: 0.8, color: '#ccc' } 
            },
            { 
                y: S.filteredData.filtered_fine || S.filteredData.filtered, 
                x: S.filteredData.t_fine || S.signalData.t, 
                name: '响应输出 Y(t)', 
                line: { width: 1.4, color: '#e74c3c' } 
            }
        ];

        if (visibleSamplesCount <= 150) {
            filterTraces.push({
                y: S.filteredData.filtered,
                x: S.signalData.t,
                name: '滤波样本点',
                mode: 'markers',
                marker: { size: 5, color: '#e74c3c' }
            });
        }
        Plotly.newPlot(el, filterTraces, layout, { responsive: true, displayModeBar: false });
    } else {
        document.getElementById('filter-result').style.display = 'none';
    }

    if (S.kalmanData && S.kalmanParams) {
        document.getElementById('kalman-result').style.display = 'flex';
        const data = S.kalmanData;
        
        const posEl = document.getElementById('kalman-pos-plot');
        if (posEl) {
            Plotly.purge(posEl);
            const posLayout = {
                height: 230,
                margin: { l: 40, r: 15, t: 15, b: 35 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                xaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, zeroline: false, showline: false },
                yaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, zeroline: false, showline: false },
                showlegend: true,
                legend: { orientation: 'h', y: 1.15, font: { size: 10 } }
            };
            const posTraces = [
                { y: data.pos_true, x: data.t, name: '真实位置 p(t)', line: { width: 2, color: '#4285f4' } },
                { y: data.pos_meas, x: data.t, name: '含噪观测 z(t)', mode: 'markers', marker: { size: 3, color: '#e74c3c', opacity: 0.5 } },
                { y: data.pos_est, x: data.t, name: '卡尔曼估计 ̂p(t)', line: { width: 2, color: '#27ae60' } }
            ];
            Plotly.newPlot(posEl, posTraces, posLayout, { responsive: true, displayModeBar: false });
        }
        
        const velEl = document.getElementById('kalman-vel-plot');
        if (velEl) {
            Plotly.purge(velEl);
            const velLayout = {
                height: 210,
                margin: { l: 40, r: 15, t: 15, b: 35 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                xaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, zeroline: false, showline: false },
                yaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, zeroline: false, showline: false },
                showlegend: true,
                legend: { orientation: 'h', y: 1.15, font: { size: 10 } }
            };
            const velTraces = [
                { y: data.vel_true, x: data.t, name: '真实速度 v(t)', line: { width: 1.5, color: '#9b59b6' } },
                { y: data.vel_est, x: data.t, name: '估计速度 ̂v(t)', line: { width: 2, color: '#f1c40f' } }
            ];
            Plotly.newPlot(velEl, velTraces, velLayout, { responsive: true, displayModeBar: false });
        }
        
        const covEl = document.getElementById('kalman-cov-plot');
        if (covEl) {
            Plotly.purge(covEl);
            const covLayout = {
                height: 210,
                margin: { l: 40, r: 15, t: 15, b: 35 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                xaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, zeroline: false, showline: false },
                yaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, zeroline: false, showline: false },
                showlegend: true,
                legend: { orientation: 'h', y: 1.15, font: { size: 10 } }
            };
            const covTraces = [
                { y: data.p_error_pos, x: data.t, name: '协方差 P₁₁ (位置)', line: { width: 1.5, color: '#e67e22' } },
                { y: data.k_gain_pos, x: data.t, name: '卡尔曼增益 K₁ (位置)', line: { width: 1.5, color: '#1abc9c' } },
                { y: data.k_gain_vel, x: data.t, name: '卡尔曼增益 K₂ (速度)', line: { width: 1.5, color: '#34495e' } }
            ];
            Plotly.newPlot(covEl, covTraces, covLayout, { responsive: true, displayModeBar: false });
        }
    } else {
        document.getElementById('kalman-result').style.display = 'none';
    }
}

function toggleUIMode(event) {
    if (event) event.stopPropagation();
    const toggleEl = document.getElementById('ui-mode-toggle');
    if (!toggleEl) {
        fetch('/api/log', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: "toggleUIMode called but toggleEl not found"})
        }).catch(e => {});
        return;
    }
    
    const prevMode = S.uiMode;
    saveModeInputs(prevMode);
    if (prevMode === 'classic') {
        S.classicSignalData = S.signalData;
        S.classicFilteredData = S.filteredData;
        S.classicKalmanData = S.kalmanData;
        S.classicFilterParams = S.filterParams;
        S.classicKalmanParams = S.kalmanParams;
    } else {
        S.allSignalData = S.signalData;
        S.allFilteredData = S.filteredData;
        S.allKalmanData = S.kalmanData;
        S.allFilterParams = S.filterParams;
        S.allKalmanParams = S.kalmanParams;
    }
    
    if (S.uiMode === 'classic') {
        S.uiMode = 'all';
        toggleEl.classList.remove('mode-classic');
        toggleEl.classList.add('mode-all');
        document.body.classList.add('clar-all-mode');
        renderSessionList();
    } else {
        S.uiMode = 'classic';
        toggleEl.classList.remove('mode-all');
        toggleEl.classList.add('mode-classic');
        document.body.classList.remove('clar-all-mode');
    }
    
    restoreModeInputs(S.uiMode);
    if (S.uiMode === 'classic') {
        S.signalData = S.classicSignalData || null;
        S.filteredData = S.classicFilteredData || null;
        S.kalmanData = S.classicKalmanData || null;
        S.filterParams = S.classicFilterParams || null;
        S.kalmanParams = S.classicKalmanParams || null;
        
        replotClassicWorkspace();
    } else {
        S.signalData = S.allSignalData || null;
        S.filteredData = S.allFilteredData || null;
        S.kalmanData = S.allKalmanData || null;
        S.filterParams = S.allFilterParams || null;
        S.kalmanParams = S.allKalmanParams || null;
    }
    
    S.currentNode = "";
    S.graphNode = "";
    const slotEl = document.getElementById('knowledge-slot');
    if (slotEl) {
        slotEl.classList.remove('active');
    }
    if (S.page === 'knowledge-map') {
        renderGraph();
    }
    
    renderMessages();
    
    fetch('/api/log', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: "toggleUIMode executed. Prev: " + prevMode + ", Current: " + S.uiMode})
    }).catch(e => {});
    
    // Trigger resizing of Plotly plots and ECharts
    setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
        if (graphChart) {
            try { graphChart.resize(); } catch(e) {}
        }
    }, 550);
}

async function generateSignal(shouldNavigate = true, shouldScroll = true) {
    try {
        const params = {
            signal_type: document.getElementById('sig-type').value,
            freq: parseFloat(document.getElementById('sig-freq').value) || 200,
            fs: parseInt(document.getElementById('sig-fs').value) || 10000,
            snr_db: parseFloat(document.getElementById('sig-snr').value) || 10,
            bandwidth: parseFloat(document.getElementById('sig-bandwidth').value) || 50,
            freq_end: parseFloat(document.getElementById('sig-freq-end').value) || 300,
            markov_a: parseFloat(document.getElementById('sig-markov-a').value) || 0.9,
            freq2: parseFloat(document.getElementById('sig-freq2').value) || 300,
        };
        const data = await api('/api/signal/generate', { method: 'POST', body: JSON.stringify(params) });
        if (data.error) { alert(data.error); return; }
        data.signal_type = params.signal_type;
        data.freq = params.freq;
        S.signalData = data; S.filteredData = null;
        S.currentNode = SIG_NODE_MAP[params.signal_type] || 'KP_CH1_01';
        fetchNodeAndShowCard(S.currentNode); // 当生成特定信号时，右侧卡片同步拉取并显示与之关联的《随机信号分析》知识卡片

        if (shouldNavigate) {
            navigate('signal-lab');
        }
        updatePlots(); // 包含时域频域的下拉框状态自动绘制
        renderMetrics(data.features, params);
        updateInlineCharts();
        
        // 显示 Clar 分析按钮
        const aiBtn = document.getElementById('btn-ai-analyze');
        if (aiBtn) aiBtn.style.display = 'inline-block';

        // 插入本地系统提示，同步感知，而不再强行发送 API 对话
        const messagesEl = document.getElementById('chat-messages');
        if (messagesEl) {
            let extraInfo = '';
            if (params.signal_type === '线性调频(LFM)') {
                extraInfo = `, 终止频=${params.freq_end}Hz`;
            } else if (params.signal_type === '窄带' || params.signal_type === '瑞利分布') {
                extraInfo = `, 带宽=${params.bandwidth}Hz`;
            } else if (params.signal_type === '一阶马尔可夫过程') {
                extraInfo = `, 系数a=${params.markov_a}`;
            } else if (params.signal_type === '双频正弦+白噪声') {
                extraInfo = `, 频率2=${params.freq2}Hz`;
            }

            let freqStr = '';
            if (params.signal_type !== '高斯白噪声' && params.signal_type !== '一阶马尔可夫过程') {
                freqStr = `${params.freq}Hz, `;
            }

            messagesEl.insertAdjacentHTML('beforeend', `
                <div class="chat-msg assistant" style="opacity: 0.9; margin: 4px 0;">
                    <div class="bubble" style="background: rgba(66,133,244,0.05); border-left: 3px solid #f59e0b; padding: 10px 14px; font-size: 13px;">
                        📡 <strong>系统感知同步:</strong> 已生成 ${params.signal_type}（${freqStr}fs=${params.fs}Hz, SNR=${params.snr_db}dB${extraInfo}）。AI 助教 Clar 已同步其数字特征。
                    </div>
                </div>
            `);
            if (shouldScroll) {
                messagesEl.scrollTop = messagesEl.scrollHeight;
            }
        }
    } catch(e) { console.error("信号生成中断:", e); }
}

async function analyzeCurrentSignal() {
    if (!S.signalData) return;
    const type = document.getElementById('sig-type').value;
    const freq = parseFloat(document.getElementById('sig-freq').value) || 200;
    const fs = parseInt(document.getElementById('sig-fs').value) || 10000;
    const snr = parseFloat(document.getElementById('sig-snr').value) || 10;
    const bw = parseFloat(document.getElementById('sig-bandwidth').value) || 50;
    const fe = parseFloat(document.getElementById('sig-freq-end').value) || 300;
    
    const nyq = checkNyquist(freq, fs);
    let nyqText = nyq.ok 
        ? `满足奈奎斯特采样定理（可观测最高频率为 ${fs / 2} Hz，无混叠）` 
        : `警告：${nyq.msg}`;
        
    let extraParamsText = "";
    if (type === '线性调频(LFM)') {
        extraParamsText = `，扫频终止频率为 ${fe} Hz`;
    } else if (type === '窄带' || type === '瑞利分布') {
        extraParamsText = `，信号带宽为 ${bw} Hz`;
    } else if (type === '一阶马尔可夫过程') {
        const ma = parseFloat(document.getElementById('sig-markov-a').value) || 0.9;
        extraParamsText = `，回归系数 a = ${ma}`;
    } else if (type === '双频正弦+白噪声') {
        const f2 = parseFloat(document.getElementById('sig-freq2').value) || 300;
        extraParamsText = `，第二频率 = ${f2} Hz`;
    }

    let baseParamsText = `中心频率/起始频率 = ${freq} Hz`;
    if (type === '高斯白噪声') {
        baseParamsText = `纯高斯白噪声`;
    } else if (type === '一阶马尔可夫过程') {
        baseParamsText = `一阶自回归过程`;
    }

    const feats = S.signalData.features;
    const featuresText = `均值 E[X] = ${feats.mean.toFixed(4)}，均方差 D[X] = ${feats.variance.toFixed(4)}，均方值 RMS = ${feats.rms.toFixed(4)}，峰峰值 = ${feats.peak_to_peak.toFixed(4)}`;

    const prompt = `我刚才生成了「${type}」过程，基本参数为：${baseParamsText}${extraParamsText}，采样率 fs = ${fs} Hz，信噪比 SNR = ${snr} dB。
${nyqText}。
计算得到的时域数字特征为：${featuresText}。
请结合课程大纲及该信号的物理性质，为我全面且通俗易懂地剖析：
1. 该随机信号的物理意义（是高斯过程吗？是平稳的吗？各态历经性如何？）
2. 时域数字特征计算结果的物理含义（如均值、均方差是否合乎公式推导预期？）
3. 在香农-奈奎斯特带宽 [0, ${fs / 2} Hz] 内，该信号的幅度谱呈现什么分布规律？是否存在混叠？
4. 给出一到两条实用的仿真避坑指南。`;

    sendChat(prompt);
}

function updateTabIndicators() {
    document.querySelectorAll('.analysis-tabs').forEach(tabsContainer => {
        const activeBtn = tabsContainer.querySelector('.analysis-tab-btn.active');
        let indicator = tabsContainer.querySelector('.analysis-tabs-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'analysis-tabs-indicator';
            tabsContainer.insertBefore(indicator, tabsContainer.firstChild);
        }
        if (activeBtn) {
            if (activeBtn.offsetWidth > 0) {
                indicator.style.left = activeBtn.offsetLeft + 'px';
                indicator.style.width = activeBtn.offsetWidth + 'px';
                indicator.style.opacity = '1';
            } else {
                indicator.style.opacity = '0';
            }
        } else {
            indicator.style.opacity = '0';
        }
    });
}

function updatePlots() {
    updateTimePlot();
    updateFreqPlot();
    setTimeout(updateTabIndicators, 0);
}

function updateTimePlot() {
    const data = S.signalData;
    if (!data) return;
    const plotId = 'waveform-plot';
    Plotly.purge(plotId);

    const type = document.getElementById('sig-type').value;
    const timeAnalysis = document.getElementById('time-analysis-type').value;
    const cardTitleEl = document.getElementById('time-card-title');

    const baseLayout = {
        margin: { l: 45, r: 15, t: 15, b: 35 }, autosize: true, showlegend: true,
        legend: { orientation: 'h', y: 1.15, font: { size: 10 } },
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        yaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, zeroline: false, showline: false }
    };

    let traces = [];
    let layout = { ...baseLayout };

    if (timeAnalysis === 'waveform') {
        if (cardTitleEl) cardTitleEl.innerText = `时域波形 X(t)`;
        const freq = parseFloat(document.getElementById('sig-freq').value) || 200;
        const tMax = (type === '线性调频(LFM)' || type === '瑞利分布' || type === '高斯白噪声' || type === '一阶马尔可夫过程')
            ? data.t[data.t.length - 1]
            : Math.min(data.t[data.t.length - 1], Math.max(0.01, 8 / freq));
        const fs = parseInt(document.getElementById('sig-fs').value) || 10000;
        const visibleSamplesCount = tMax * fs;

        layout.xaxis = { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, range: [0, tMax], zeroline: false, showline: false };

        traces = [
            { 
                y: data.clean_fine || data.clean, 
                x: data.t_fine || data.t, 
                name: '纯净信号 s(t)', 
                line: { width: 1.5, color: '#4285f4' } 
            },
            { 
                y: data.noisy_fine || data.noisy, 
                x: data.t_fine || data.t, 
                name: '观测序列 X(t)', 
                line: { width: 1, color: '#e74c3c' } 
            }
        ];

        if (visibleSamplesCount <= 150) {
            traces.push({
                y: data.noisy,
                x: data.t,
                name: '观测样本点',
                mode: 'markers',
                marker: { size: 5, color: '#e74c3c' }
            });
        }
    } else if (timeAnalysis === 'autocorr') {
        if (cardTitleEl) cardTitleEl.innerText = `自相关函数 Rx(τ)`;
        layout.xaxis = { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, title: { text: '延时 τ (s)', font: { size: 10 } }, zeroline: false, showline: false };
        
        traces = [
            {
                y: data.autocorr,
                x: data.autocorr_lags,
                name: '含噪自相关 Rx(τ)',
                line: { width: 1.5, color: '#e67e22' }
            }
        ];
    } else if (timeAnalysis === 'crosscorr') {
        if (cardTitleEl) cardTitleEl.innerText = `互相关函数 Rsx(τ)`;
        layout.xaxis = { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, title: { text: '延时 τ (s)', font: { size: 10 } }, zeroline: false, showline: false };
        
        traces = [
            {
                y: data.crosscorr || [],
                x: data.crosscorr_lags || [],
                name: '互相关 Rsx(τ)',
                line: { width: 1.5, color: '#9b59b6' }
            }
        ];
    } else if (timeAnalysis === 'pdf') {
        if (cardTitleEl) cardTitleEl.innerText = `概率密度 (PDF)`;
        layout.xaxis = { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, title: { text: '幅度', font: { size: 10 } }, zeroline: false, showline: false };
        
        traces = [
            {
                x: data.pdf_x,
                y: data.pdf_y,
                type: 'bar',
                name: '观测序列 PDF',
                marker: { color: 'rgba(231, 76, 60, 0.6)', line: { color: 'rgba(231, 76, 60, 1.0)', width: 1 } }
            }
        ];
        if (data.pdf_x_clean && data.pdf_x_clean.length > 0) {
            traces.push({
                x: data.pdf_x_clean,
                y: data.pdf_y_clean,
                mode: 'lines',
                name: '纯净信号 PDF',
                line: { width: 2, color: '#4285f4' }
            });
        }
    }

    Plotly.newPlot(plotId, traces, layout, { responsive: true, displayModeBar: false });
}

function updateFreqPlot() {
    const data = S.signalData;
    if (!data) return;
    const plotId = 'spectrum-plot';
    Plotly.purge(plotId);

    const freqAnalysis = document.getElementById('freq-analysis-type').value;
    const cardTitleEl = document.getElementById('freq-card-title');

    const baseLayout = {
        margin: { l: 45, r: 15, t: 15, b: 35 }, autosize: true, showlegend: true,
        legend: { orientation: 'h', y: 1.15, font: { size: 10 } },
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        yaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, zeroline: false, showline: false }
    };

    let traces = [];
    let layout = { ...baseLayout };

    if (freqAnalysis === 'amplitude') {
        if (cardTitleEl) cardTitleEl.innerText = `幅度谱 (香农-奈奎斯特带宽)`;
        layout.xaxis = { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, title: { text: '频率 (Hz)', font: { size: 10 } }, zeroline: false, showline: false };

        traces = [
            { y: data.spec_clean, x: data.freqs, name: '纯净幅度谱 |S(f)|', line: { width: 1.5, color: '#27ae60' } },
            { y: data.spec_noisy, x: data.freqs, name: '含噪幅度谱 |X(f)|', line: { width: 1, color: '#e74c3c' } }
        ];
    } else if (freqAnalysis === 'psd') {
        if (cardTitleEl) cardTitleEl.innerText = `功率谱密度 (PSD)`;
        layout.xaxis = { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, title: { text: '频率 (Hz)', font: { size: 10 } }, zeroline: false, showline: false };

        traces = [];
        if (data.psd_clean && data.psd_clean.length > 0) {
            traces.push({
                y: data.psd_clean,
                x: data.psd_freqs,
                name: '纯净功率谱 Gs(f)',
                line: { width: 1.5, color: '#27ae60' }
            });
        }
        traces.push({
            y: data.psd_noisy,
            x: data.psd_freqs,
            name: '含噪功率谱 Gx(f)',
            line: { width: 1, color: '#e74c3c' }
        });
    } else if (freqAnalysis === 'phase') {
        if (cardTitleEl) cardTitleEl.innerText = `相位谱 θ(f)`;
        layout.xaxis = { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, title: { text: '频率 (Hz)', font: { size: 10 } }, zeroline: false, showline: false };
        layout.yaxis.title = { text: '相位 (rad)', font: { size: 10 } };

        traces = [];
        if (data.phase_clean && data.phase_clean.length > 0) {
            traces.push({
                y: data.phase_clean,
                x: data.freqs,
                name: '纯净相位谱 θs(f)',
                line: { width: 1.5, color: '#2980b9' }
            });
        }
        traces.push({
            y: data.phase_noisy,
            x: data.freqs,
            name: '含噪相位谱 θx(f)',
            line: { width: 1, color: '#e74c3c', opacity: 0.7 }
        });
    }

    Plotly.newPlot(plotId, traces, layout, { responsive: true, displayModeBar: false });
}

function renderMetrics(feats, params) {
    const el = document.getElementById('signal-metrics');
    if (!el) return;
    el.style.display = 'flex';

    let paramTiles = '';
    if (params) {
        const nyq = checkNyquist(params.freq, params.fs);
        const fsClass = nyq.ok ? '' : (nyq.level === 'alias' ? 'metric--alias' : 'metric--warn');
        const fsHint  = nyq.ok ? `f_s/f_max = ${(params.fs / (params.signal_type === '线性调频(LFM)' ? params.freq_end : (params.signal_type === '窄带' ? params.freq + params.bandwidth / 2 : params.freq))).toFixed(1)}×` : nyq.msg;
        
        let extraTile = '';
        if (params.signal_type === '线性调频(LFM)') {
            extraTile = `
                <div class="metric">
                    <div class="val pop">${params.freq_end} Hz</div>
                    <div class="lbl">终止频率 f_end</div>
                </div>
            `;
        } else if (params.signal_type === '窄带' || params.signal_type === '瑞利分布') {
            extraTile = `
                <div class="metric">
                    <div class="val pop">${params.bandwidth} Hz</div>
                    <div class="lbl">信号带宽 B</div>
                </div>
            `;
        }

        paramTiles = `
            <div class="metric ${fsClass}" title="${fsHint}">
                <div class="val pop">${params.fs} Hz</div>
                <div class="lbl">采样率 fs（Nyq=${(params.fs/2).toFixed(0)} Hz）</div>
            </div>
            <div class="metric">
                <div class="val pop">${params.freq} Hz</div>
                <div class="lbl">信号频率 f₀</div>
            </div>
            ${extraTile}
            <div class="metric">
                <div class="val pop">${params.snr_db} dB</div>
                <div class="lbl">信噪比 SNR</div>
            </div>
        `;
    }

    el.innerHTML = paramTiles + `
        <div class="metric"><div class="val pop">${feats.mean.toFixed(3)}</div><div class="lbl">数学期望 E[X]</div></div>
        <div class="metric"><div class="val pop">${feats.variance.toFixed(3)}</div><div class="lbl">均方差 D[X]</div></div>
        <div class="metric"><div class="val pop">${feats.rms.toFixed(3)}</div><div class="lbl">均方值 RMS</div></div>
    `;
}

function quickAsk(text, targetPage = null) {
    document.getElementById('chatFloatInput').value = '';
    
    const textLower = text.toLowerCase();
    let navigated = false;
    
    // 如果当前已经在知识图谱页面，点击右侧气泡追问时默认保持在当前页面，不要因为问句中的关键字跳走
    if (S.page === 'knowledge-map') {
        navigated = true;
    }
    
    // 1. 优先根据问句中的核心关键词导航至最匹配的页面
    if (!navigated && (textLower.includes("滤波") || textLower.includes("一阶") || textLower.includes("低通") || textLower.includes("滑动平均") || textLower.includes("lti") || textLower.includes("系统") || textLower.includes("冲击") || textLower.includes("卷积") || textLower.includes("卡尔曼") || textLower.includes("kalman") || textLower.includes("状态空间") || textLower.includes("协方差") || textLower.includes("增益") || textLower.includes("维纳") || textLower.includes("wiener") || textLower.includes("估计") || textLower.includes("估值") || textLower.includes("状态") || textLower.includes("递归") || textLower.includes("预测") || textLower.includes("更新") || textLower.includes("收敛") || textLower.includes("过程噪声") || textLower.includes("测量噪声"))) {
        navigate('toolbox');
        navigated = true;
    } else if (!navigated && (textLower.includes("图谱") || textLower.includes("大纲") || textLower.includes("章节") || textLower.includes("小节") || textLower.includes("知识树") || textLower.includes("课程"))) {
        navigate('knowledge-map');
        navigated = true;
    } else if (!navigated && (textLower.includes("信号") || textLower.includes("波形") || textLower.includes("期望") || textLower.includes("方差") || textLower.includes("期待值") || textLower.includes("均值") || textLower.includes("高斯") || textLower.includes("平稳") || textLower.includes("各态历经") || textLower.includes("混叠") || textLower.includes("奈奎斯特") || textLower.includes("采样率") || textLower.includes("snr") || textLower.includes("白噪声") || textLower.includes("lfm") || textLower.includes("瑞利"))) {
        navigate('signal-lab');
        navigated = true;
    }
    
    // 2. 如果关键词未命中，且指定了目标页面，则使用目标页面
    if (!navigated && targetPage) {
        navigate(targetPage);
    }
    
    sendChat(text);
}

function appendQuickQuestions(cardEl, questions) {
    if (!questions || questions.length === 0) {
        questions = [
            "这个知识点在考试或考研中经常怎么考？",
            "这个概念的物理直觉是什么？",
            "有没有 Python 代码实现这个概念的例子？"
        ];
    }
    const qqWrap = document.createElement('div');
    qqWrap.className = 'quick-qs';
    questions.forEach(q => {
        const btn = document.createElement('button');
        btn.className = 'quick-ask-btn';
        btn.innerHTML = renderInlineMarkdown(q);
        btn.onclick = () => quickAsk(q, 'knowledge-map');
        qqWrap.appendChild(btn);
    });
    cardEl.appendChild(qqWrap);
}

function updateKnowledgeCards(responseData) {
    if (secondaryCardData) {
        primaryCardData = secondaryCardData;
    }
    secondaryCardData = responseData.new_card ? {
        title: responseData.new_card.title,
        core_concept: responseData.new_card.core_concept,
        quick_questions: responseData.quick_questions || []
    } : null;

    const wrapper = document.getElementById('cards-wrapper');
    if (!wrapper) return;
    wrapper.innerHTML = '';

    if (primaryCardData) {
        const pCard = document.createElement('div');
        pCard.className = 'kc-card kc-card--primary';
        pCard.innerHTML = `<h4>📌 基石脉络: ${primaryCardData.title}</h4><div class="kc-concept">${renderMarkdown(primaryCardData.core_concept)}</div>`;
        if (lastAiReply) pCard.innerHTML += `<div class="ai-insight"><strong>💡 上轮追索关联推导:</strong><br>${renderMarkdown(lastAiReply)}</div>`;
        appendQuickQuestions(pCard, primaryCardData.quick_questions);
        wrapper.appendChild(pCard);
    }
    if (secondaryCardData) {
        const sCard = document.createElement('div');
        sCard.className = 'kc-card kc-card--secondary';
        sCard.innerHTML = `<h4>🔥 当前聚焦新知: ${secondaryCardData.title}</h4><div class="kc-concept">${renderMarkdown(secondaryCardData.core_concept)}</div>`;
        appendQuickQuestions(sCard, secondaryCardData.quick_questions);
        wrapper.appendChild(sCard);
    }

    renderMath(wrapper);

    lastAiReply = responseData.reply || "";
    document.getElementById('knowledge-slot').classList.add('active');
}

async function fetchNodeAndShowCard(nodeId) {
    if (!nodeId) return;
    try {
        const res = await api('/api/knowledge/node/' + nodeId);
        if (res && !res.error) {
            const qList = [];
            if (res.errors && res.errors.length > 0) {
                res.errors.forEach(e => {
                    if (e && e.title) qList.push(`如何避开「${res.title}」中关于“${e.title}”的误区？`);
                });
            }
            if (qList.length === 0) {
                qList.push(
                    `请详细解释「${res.title}」的核心概念及物理直觉？`,
                    `「${res.title}」在《随机信号分析》课程中的考查重点是什么？`,
                    `能否提供一个用于验证「${res.title}」的 Python 仿真代码示例？`
                );
            }
            
            updateKnowledgeCards({
                reply: lastAiReply || "",
                new_card: {
                    title: res.title,
                    core_concept: res.core_concept
                },
                quick_questions: qList
            });
        }
    } catch(e) {
        console.error("Failed to fetch node card:", e);
    }
}

function buildSignalContext() {
    const context = {
        signal_generated: !!S.signalData,
        signal_type: document.getElementById('sig-type').value,
        freq: parseFloat(document.getElementById('sig-freq').value) || 200,
        fs: parseInt(document.getElementById('sig-fs').value) || 10000,
        snr_db: parseFloat(document.getElementById('sig-snr').value) || 10,
        bandwidth: parseFloat(document.getElementById('sig-bandwidth').value) || 50,
        freq_end: parseFloat(document.getElementById('sig-freq-end').value) || 300,
        markov_a: parseFloat(document.getElementById('sig-markov-a').value) || 0.9,
        freq2: parseFloat(document.getElementById('sig-freq2').value) || 300,
        features: (S.signalData && S.signalData.features) ? S.signalData.features : null,
        
        filter_run: !!S.filteredData,
        filter_type: (S.filterParams && S.filterParams.filter_type) ? S.filterParams.filter_type : null,
        filter_window_size: (S.filterParams && S.filterParams.window_size) ? S.filterParams.window_size : null,
        filter_cutoff_freq: (S.filterParams && S.filterParams.cutoff_freq) ? S.filterParams.cutoff_freq : null,
        filter_features: (S.filteredData && S.filteredData.features) ? S.filteredData.features : null,
        
        kalman_run: !!S.kalmanData,
        kalman_q: (S.kalmanParams && S.kalmanParams.q !== undefined) ? S.kalmanParams.q : null,
        kalman_r: (S.kalmanParams && S.kalmanParams.r !== undefined) ? S.kalmanParams.r : null,
        kalman_v0: (S.kalmanParams && S.kalmanParams.v0 !== undefined) ? S.kalmanParams.v0 : null,
        kalman_p_final: null,
        kalman_k1_final: null,
        kalman_k2_final: null
    };

    if (S.kalmanData) {
        const pHistory = S.kalmanData.p_error_pos;
        const kGainPos = S.kalmanData.k_gain_pos;
        const kGainVel = S.kalmanData.k_gain_vel;
        if (pHistory && pHistory.length > 0) {
            context.kalman_p_final = pHistory[pHistory.length - 1];
        }
        if (kGainPos && kGainPos.length > 0) {
            context.kalman_k1_final = kGainPos[kGainPos.length - 1];
        }
        if (kGainVel && kGainVel.length > 0) {
            context.kalman_k2_final = kGainVel[kGainVel.length - 1];
        }
    }
    return context;
}

// Keep track of AbortControllers for active queries so they can be recalled/cancelled
if (!S.activeControllers) {
    S.activeControllers = {};
}

function lockChat() {
    document.body.classList.add('chat-locked');
    const input = document.getElementById('chatFloatInput');
    const sendBtn = document.querySelector('.send-btn');
    const chatInputWrap = document.querySelector('.chat-input-wrap');
    if (input) input.disabled = true;
    if (sendBtn) sendBtn.disabled = true;
    if (chatInputWrap) chatInputWrap.classList.add('locked');
}

function unlockChat() {
    document.body.classList.remove('chat-locked');
    const input = document.getElementById('chatFloatInput');
    const sendBtn = document.querySelector('.send-btn');
    const chatInputWrap = document.querySelector('.chat-input-wrap');
    if (input) {
        input.disabled = false;
        input.focus();
    }
    if (sendBtn) sendBtn.disabled = false;
    if (chatInputWrap) chatInputWrap.classList.remove('locked');
}

async function sendChat(overrideText = null) {
    if (document.body.classList.contains('chat-locked')) return;
    const input = document.getElementById('chatFloatInput');
    const textToSend = overrideText || input.value.trim();
    if (!textToSend) return;
    input.value = '';
    input.style.height = '56px'; // Reset textarea height on send

    // 当用户手动输入提问切换话题时，清除上一次的高亮状态，实现视觉同步
    if (overrideText === null) {
        S.currentNode = "";
        S.graphNode = "";
        if (S.page === 'knowledge-map') {
            renderGraph();
        }
        // 当切换话题时，自动收起右侧知识卡片面板，等待新话题的高亮卡片打开
        const slotEl = document.getElementById('knowledge-slot');
        if (slotEl) {
            slotEl.classList.remove('active');
        }
    }

    const messagesEl = document.getElementById('chat-messages');
    const originPage = S.page; // 记录提问时的页面来源

    // Append user message to memory
    if (S.uiMode === 'classic') {
        if (!S.classicMessages) S.classicMessages = [];
        S.classicMessages.push({ role: 'user', content: textToSend });
    } else {
        let session = S.allSessions.find(s => s.id === S.currentAllSessionId);
        if (!session) {
            session = createNewAllSession(false);
        }
        session.messages.push({ role: 'user', content: textToSend });
        
        // Update session title based on first query if default
        if (session.title === '新对话' && session.messages.filter(m => m.role === 'user').length === 1) {
            session.title = textToSend.substring(0, 16) + (textToSend.length > 16 ? '...' : '');
            renderSessionList();
        }
    }
    saveChatHistory();

    // 对用户消息也执行安全防破译的渲染
    const safeText = textToSend.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const userMsgHtml = renderMarkdown(safeText);

    // ✨ 彻底移除飞行动画，改用无缝插入
    const userMsgId = 'msg-' + Date.now() + '-U';
    const loadingId = 'msg-' + Date.now() + '-A';

    messagesEl.insertAdjacentHTML('beforeend', `
        <div class="chat-msg user" id="${userMsgId}">
            <div class="bubble">${userMsgHtml}</div>
            <button class="msg-recall-btn" onclick="recallMessage('${userMsgId}', '${loadingId}', '${encodeURIComponent(textToSend)}')">撤回</button>
        </div>
        <div class="chat-msg assistant" id="${loadingId}">
            <div class="bubble">
                <div class="typing-dots"><span></span><span></span><span></span></div>
            </div>
        </div>
    `);

    // 对用户气泡公式生效
    const userEl = document.getElementById(userMsgId);
    if(userEl) renderMath(userEl);

    messagesEl.scrollTop = messagesEl.scrollHeight;
    
    // Update outline navigation
    updateOutlineNav();

    // Create abort controller for this message
    const controller = new AbortController();
    S.activeControllers[userMsgId] = controller;

    // Setup 5-second automatic removal for the recall button
    setTimeout(() => {
        const recallBtn = document.querySelector(`#${userMsgId} .msg-recall-btn`);
        if (recallBtn) {
            recallBtn.classList.add('hide-active');
            setTimeout(() => recallBtn.remove(), 550);
        }
        if (S.activeControllers[userMsgId] === controller) {
            delete S.activeControllers[userMsgId];
        }
    }, 5000);

    let historyList = [];
    if (S.uiMode === 'classic') {
        historyList = S.classicMessages || [];
    } else {
        const session = S.allSessions.find(s => s.id === S.currentAllSessionId);
        historyList = session ? (session.messages || []) : [];
    }
    const historyToSend = historyList.slice(0, -1).slice(-10).map(m => ({
        role: m.role,
        content: m.content
    }));

    const payload = { 
        prompt: textToSend, 
        signal_context: buildSignalContext(),
        current_node_id: S.currentNode || "",
        graph_node_name: S.graphNode || "",
        ui_mode: S.uiMode || "classic",
        history: historyToSend
    };

    try {
        lockChat();
        const resp = await fetch(API_BASE + '/api/chat', { 
            method: 'POST', 
            headers: API_HEADERS, 
            body: JSON.stringify(payload),
            signal: controller.signal
        });

        // Remove the recall button immediately upon successful response
        const recallBtn = document.querySelector(`#${userMsgId} .msg-recall-btn`);
        if (recallBtn) {
            recallBtn.classList.add('hide-active');
            setTimeout(() => recallBtn.remove(), 550);
        }
        if (S.activeControllers[userMsgId] === controller) {
            delete S.activeControllers[userMsgId];
        }

        const loadingEl = document.getElementById(loadingId);
        const bubbleEl = loadingEl ? loadingEl.querySelector('.bubble') : null;
        if (bubbleEl) {
            bubbleEl.innerHTML = '';
        }

        const reader = resp.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';
        let replyText = '';
        let data = null;

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep the last incomplete line

            for (const line of lines) {
                const cleanLine = line.trim();
                if (!cleanLine.startsWith('data:')) continue;

                try {
                    const jsonStr = cleanLine.substring(5).trim();
                    const msg = JSON.parse(jsonStr);

                    if (msg.type === 'text') {
                        replyText += msg.content;
                        if (bubbleEl) {
                            const isAtBottom = messagesEl.scrollHeight - messagesEl.scrollTop - messagesEl.clientHeight < 120;
                            // Show raw streaming text before final markdown render
                            bubbleEl.innerText = replyText.replace(/\[NODE:\s*\w+\]/g, '').trim();
                            if (messagesEl && isAtBottom) {
                                messagesEl.scrollTop = messagesEl.scrollHeight;
                            }
                        }
                    } else if (msg.type === 'metadata') {
                        data = msg;
                    }
                } catch (e) {
                    console.error("Error parsing stream chunk:", e, cleanLine);
                }
            }
        }

        // Process final buffer if any
        if (buffer.trim().startsWith('data:')) {
            try {
                const jsonStr = buffer.trim().substring(5).trim();
                const msg = JSON.parse(jsonStr);
                if (msg.type === 'metadata') {
                    data = msg;
                }
            } catch (e) {}
        }

        if (!data) {
            data = {
                code: 200,
                reply: replyText,
                suggested_page: 'none',
                quick_questions: []
            };
        }

        if (data.node_id) {
            S.currentNode = data.node_id;
            // 同步更新 S.graphNode，以便清除/重置之前的手动高亮，保持状态机同步
            if (S.allNodes) {
                const matchedNode = S.allNodes.find(n => n.kp_node_id === data.node_id);
                S.graphNode = matchedNode ? matchedNode.name : "";
            } else {
                S.graphNode = "";
            }
        } else if (data.new_card && data.new_card.title) {
            S.graphNode = data.new_card.title;
            if (S.allNodes) {
                const matchedNode = S.allNodes.find(n => n.name === data.new_card.title || n.name.includes(data.new_card.title));
                S.currentNode = matchedNode && matchedNode.kp_node_id ? matchedNode.kp_node_id : "";
            } else {
                S.currentNode = "";
            }
        } else {
            // 如果 AI 回复没有关联任何知识点或新卡片，说明已切换到通用话题，清除上一次的高亮状态
            S.currentNode = "";
            S.graphNode = "";
        }

        let safeReply = (data.reply || replyText || '').replace(/~~/g, '').replace(/---/g, '\n\n');
        
        let assistantMsgObj = {
            role: 'assistant',
            content: safeReply,
            quick_questions: data.quick_questions,
            nodeId: data.node_id || (data.new_card ? data.new_card.title : null),
            signalData: null,
            filteredData: null,
            kalmanData: null
        };
        
        // Append assistant response to memory
        if (S.uiMode === 'classic') {
            S.classicMessages.push(assistantMsgObj);
        } else {
            const session = S.allSessions.find(s => s.id === S.currentAllSessionId);
            if (session) {
                session.messages.push(assistantMsgObj);
            }
        }

        // ✨ AI direct signal generation execution (only if valid generate_signal is returned)
        if (data.generate_signal) {
            S.isProgrammaticUpdate = true;
            const sig = data.generate_signal;
            if (sig.signal_type) {
                const nativeSelect = document.getElementById('sig-type');
                if (nativeSelect) {
                    nativeSelect.value = sig.signal_type;
                    nativeSelect.dispatchEvent(new Event('change'));
                }
            }
            if (sig.freq !== undefined && sig.freq !== null) {
                const inputFreq = document.getElementById('sig-freq');
                if (inputFreq) inputFreq.value = sig.freq;
            }
            if (sig.fs !== undefined && sig.fs !== null) {
                const inputFs = document.getElementById('sig-fs');
                if (inputFs) inputFs.value = sig.fs;
            }
            if (sig.snr_db !== undefined && sig.snr_db !== null) {
                const inputSnr = document.getElementById('sig-snr');
                if (inputSnr) inputSnr.value = sig.snr_db;
            }
            if (sig.bandwidth !== undefined && sig.bandwidth !== null) {
                const inputBw = document.getElementById('sig-bandwidth');
                if (inputBw) inputBw.value = sig.bandwidth;
            }
            if (sig.freq_end !== undefined && sig.freq_end !== null) {
                const inputFe = document.getElementById('sig-freq-end');
                if (inputFe) inputFe.value = sig.freq_end;
            }
            if (sig.markov_a !== undefined && sig.markov_a !== null) {
                const inputMarkovA = document.getElementById('sig-markov-a');
                if (inputMarkovA) inputMarkovA.value = sig.markov_a;
            }
            if (sig.freq2 !== undefined && sig.freq2 !== null) {
                const inputFreq2 = document.getElementById('sig-freq2');
                if (inputFreq2) inputFreq2.value = sig.freq2;
            }
            
            // Sync UI states & validation
            updateControlVisibility();
            const freqVal = parseFloat(document.getElementById('sig-freq').value) || 200;
            const fsInput = document.getElementById('sig-fs');
            const fsVal = parseInt(fsInput.value) || 10000;
            applyFsVisualState(checkNyquist(freqVal, fsVal), fsInput);
            
            S.isProgrammaticUpdate = false;

            // Always transition to signal lab on explicit generation in Classic mode, or if requested
            if (S.uiMode === 'classic') {
                navigate('signal-lab');
            }
            
            // Trigger generation
            await generateSignal(S.uiMode === 'classic', false);
            assistantMsgObj.signalData = JSON.parse(JSON.stringify(S.signalData));
        }

        if (data.run_toolbox) {
            const tb = data.run_toolbox;
            if (tb.operation === 'moving_average') {
                if (tb.params && tb.params.window_size !== undefined && tb.params.window_size !== null) {
                    const el = document.getElementById('filter-window-size');
                    if (el) el.value = tb.params.window_size;
                }
                if (S.uiMode === 'classic') navigate('toolbox');
                await applyFilter('moving_average', false);
                assistantMsgObj.filteredData = JSON.parse(JSON.stringify(S.filteredData));
                assistantMsgObj.signalData = JSON.parse(JSON.stringify(S.signalData));
            } else if (tb.operation === 'rc_lowpass') {
                if (tb.params && tb.params.cutoff_freq !== undefined && tb.params.cutoff_freq !== null) {
                    const el = document.getElementById('filter-cutoff');
                    if (el) el.value = tb.params.cutoff_freq;
                }
                if (S.uiMode === 'classic') navigate('toolbox');
                await applyFilter('rc_lowpass', false);
                assistantMsgObj.filteredData = JSON.parse(JSON.stringify(S.filteredData));
                assistantMsgObj.signalData = JSON.parse(JSON.stringify(S.signalData));
            } else if (tb.operation === 'wiener') {
                if (S.uiMode === 'classic') navigate('toolbox');
                await applyFilter('wiener', false);
                assistantMsgObj.filteredData = JSON.parse(JSON.stringify(S.filteredData));
                assistantMsgObj.signalData = JSON.parse(JSON.stringify(S.signalData));
            } else if (tb.operation === 'kalman') {
                if (tb.params) {
                    if (tb.params.q !== undefined && tb.params.q !== null) {
                        const el = document.getElementById('kalman-q');
                        if (el) el.value = tb.params.q;
                    }
                    if (tb.params.r !== undefined && tb.params.r !== null) {
                        const el = document.getElementById('kalman-r');
                        if (el) el.value = tb.params.r;
                    }
                    if (tb.params.v0 !== undefined && tb.params.v0 !== null) {
                        const el = document.getElementById('kalman-v0');
                        if (el) el.value = tb.params.v0;
                    }
                }
                if (S.uiMode === 'classic') navigate('toolbox');
                await runKalmanSimulation(false);
                assistantMsgObj.kalmanData = JSON.parse(JSON.stringify(S.kalmanData));
            }
        } else if (!data.generate_signal) {
            // Only switch page automatically in Classic mode
            if (S.uiMode === 'classic' && data.suggested_page && data.suggested_page !== 'none' && PAGE_NAMES[data.suggested_page]) {
                if (originPage !== 'knowledge-map') {
                    navigate(data.suggested_page);
                }
            }
        }

        // Ensure that any active workspace data is snapshotted to the message object
        // so that historical charts render correctly even if no new data was generated in this turn
        if (!assistantMsgObj.signalData && S.signalData) {
            assistantMsgObj.signalData = JSON.parse(JSON.stringify(S.signalData));
        }
        if (!assistantMsgObj.filteredData && S.filteredData) {
            assistantMsgObj.filteredData = JSON.parse(JSON.stringify(S.filteredData));
        }
        if (!assistantMsgObj.kalmanData && S.kalmanData) {
            assistantMsgObj.kalmanData = JSON.parse(JSON.stringify(S.kalmanData));
        }
        if (!assistantMsgObj.nodeId && S.currentNode) {
            assistantMsgObj.nodeId = S.currentNode;
        }

        saveChatHistory();

        if (bubbleEl) {
            const targetPage = (data.suggested_page && data.suggested_page !== 'none') ? data.suggested_page : originPage;
            
            // Clean up charts for classic mode bubble
            let contentToRender = safeReply;
            if (S.uiMode === 'classic') {
                contentToRender = contentToRender.replace(/<div class="ai-chart"[^>]*><\/div>/g, '');
            }
            
            const isAtBottom = messagesEl.scrollHeight - messagesEl.scrollTop - messagesEl.clientHeight < 120;
            renderAndAttach(bubbleEl, contentToRender, data.quick_questions, targetPage, assistantMsgObj);
            if (messagesEl && isAtBottom) {
                scrollToMessage(bubbleEl, messagesEl);
            }
        }

        // ✨ 触发时域与频域子选项卡自动切换
        if (data.time_analysis_type) {
            const btn = document.querySelector(`#time-tabs .analysis-tab-btn[data-value="${data.time_analysis_type}"]`);
            if (btn) btn.click();
        }
        if (data.freq_analysis_type) {
            const btn = document.querySelector(`#freq-tabs .analysis-tab-btn[data-value="${data.freq_analysis_type}"]`);
            if (btn) btn.click();
        }

        if (data.new_card) {
            updateKnowledgeCards(data);
        } else if (data.node_id) {
            lastAiReply = data.reply || replyText || "";
            fetchNodeAndShowCard(data.node_id);
        }

        // ✨ 触发知识图谱高亮更新
        if (S.page === 'knowledge-map') {
            renderGraph();
        }
        unlockChat();
    } catch (e) {
        unlockChat();
        if (e.name === 'AbortError') return; // Ignore abort errors
        const errEl = document.getElementById(loadingId);
        if (errEl) errEl.innerHTML = `<div class="bubble" style="color:#e74c3c;">智能体网络连接超时。</div>`;
    }
}

// Global function to recall a message
window.recallMessage = function(userMsgId, loadingId, encodedText) {
    const controller = S.activeControllers && S.activeControllers[userMsgId];
    if (controller) {
        controller.abort();
        delete S.activeControllers[userMsgId];
    }
    
    // Add quick fade out animation to bubbles
    const userEl = document.getElementById(userMsgId);
    if (userEl) {
        userEl.style.opacity = '0';
        userEl.style.transform = 'translateY(8px) scale(0.95)';
    }
    const loadingEl = document.getElementById(loadingId);
    if (loadingEl) {
        loadingEl.style.opacity = '0';
        loadingEl.style.transform = 'translateY(8px) scale(0.95)';
    }
    
    setTimeout(() => {
        if (userEl) userEl.remove();
        if (loadingEl) loadingEl.remove();
    }, 300);
    
    // Remove from memory
    const plainText = decodeURIComponent(encodedText);
    if (S.uiMode === 'classic') {
        if (S.classicMessages && S.classicMessages.length > 0) {
            const lastMsg = S.classicMessages[S.classicMessages.length - 1];
            if (lastMsg && lastMsg.role === 'user' && lastMsg.content === plainText) {
                S.classicMessages.pop();
            }
        }
    } else {
        const session = S.allSessions.find(s => s.id === S.currentAllSessionId);
        if (session && session.messages.length > 0) {
            const lastMsg = session.messages[session.messages.length - 1];
            if (lastMsg && lastMsg.role === 'user' && lastMsg.content === plainText) {
                session.messages.pop();
            }
        }
    }
    saveChatHistory();
    
    // Update outline navigation
    updateOutlineNav();
    
    // Put text back to input box and focus
    const input = document.getElementById('chatFloatInput');
    if (input) {
        input.value = plainText;
        input.style.height = '56px';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        input.focus();
    }
};

let graphChart = null;
async function renderGraph() {
    const el = document.getElementById('knowledge-graph');
    if (!el) return;
    
    // 复用已初始化的图表，避免每次点击节点重新加载力导向导致跳跃
    if (!graphChart) {
        graphChart = echarts.init(el);
    }

    try {
        // 使用状态机缓存，避免每次渲染都发起请求
        if (!S.allNodes) {
            const data = await api('/api/knowledge/graph');
            S.allNodes = data.nodes;
            S.allLinks = data.links;
        }

        const activeCardTitle = secondaryCardData ? secondaryCardData.title : "";
        let hasFixedActive = false;

        // 根据当前的聚焦状态决定节点的高亮样式
        const mappedNodes = S.allNodes.map(n => {
            const isActive = (n.kp_node_id && n.kp_node_id === S.currentNode) || 
                             (S.graphNode && (n.name === S.graphNode || n.name.includes(S.graphNode) || S.graphNode.includes(n.name))) ||
                             (activeCardTitle && (n.name === activeCardTitle || n.name.includes(activeCardTitle) || activeCardTitle.includes(n.name)));
            
            // 仅固定第一个匹配的高亮节点在中心 (0, 0)，其他节点围绕其漂浮
            const shouldFix = isActive && !hasFixedActive;
            if (shouldFix) {
                hasFixedActive = true;
            }

            return {
                id: n.id,
                name: n.name,
                symbolSize: isActive ? (n.symbolSize * 1.8) : (n.symbolSize * 1.3),
                category: n.category === 0 ? '章节' : n.category === 1 ? '小节' : '核心知识点',
                itemStyle: {
                    color: isActive ? '#f59e0b' : n.itemStyle.color,
                    shadowBlur: isActive ? 25 : 8,
                    shadowColor: isActive ? '#f59e0b' : 'rgba(0,0,0,0.1)',
                    borderColor: isActive ? '#fff' : 'transparent',
                    borderWidth: isActive ? 3 : 0
                },
                label: {
                    show: isActive || n.category < 2,
                    position: 'right',
                    fontSize: isActive ? 12 : 10,
                    color: isActive ? '#d97706' : '#2d3748',
                    fontWeight: isActive ? 'bold' : (n.category === 0 ? 'bold' : 'normal')
                },
                node_type: n.node_type,
                chapter: n.chapter,
                section: n.section,
                topics: n.topics,
                kp_node_id: n.kp_node_id,
                fixed: shouldFix,
                x: shouldFix ? 0 : undefined,
                y: shouldFix ? 0 : undefined
            };
        });

        // 侦测当前激活节点是否发生变化
        const currentActiveKey = S.currentNode || S.graphNode || activeCardTitle || "";
        const isNodeChanged = !graphChart.lastActiveNode || graphChart.lastActiveNode !== currentActiveKey;
        if (isNodeChanged) {
            graphChart.lastActiveNode = currentActiveKey;
        }

        const option = {
            tooltip: {
                trigger: 'item',
                formatter: function (params) {
                    if (params.dataType === 'node') {
                        let html = `<div style="font-weight:600;margin-bottom:4px;">${params.data.name}</div>`;
                        html += `<div style="font-size:11px;color:#718096;">类别: ${params.data.node_type === 'chapter' ? '章节' : params.data.node_type === 'section' ? '小节' : '核心知识点'}</div>`;
                        if (params.data.chapter) html += `<div style="font-size:11px;color:#718096;">章节: ${params.data.chapter}</div>`;
                        if (params.data.section) html += `<div style="font-size:11px;color:#718096;">小节: ${params.data.section}</div>`;
                        return html;
                    }
                    return '';
                }
            },
            legend: [{
                data: ['章节', '小节', '核心知识点'],
                textStyle: { color: '#5c6479', fontSize: 12 },
                bottom: 10
            }],
            series: [{
                type: 'graph',
                layout: 'force',
                data: mappedNodes,
                links: S.allLinks,
                categories: [
                    { name: '章节' },
                    { name: '小节' },
                    { name: '核心知识点' }
                ],
                roam: true,
                // 当聚焦节点变化时，清除之前的平移缩放状态，复位到中心视口
                center: isNodeChanged ? null : undefined,
                zoom: isNodeChanged ? 1 : undefined,
                force: {
                    repulsion: 180,
                    edgeLength: 70,
                    gravity: 0.08
                },
                lineStyle: {
                    color: 'rgba(0,0,0,0.12)',
                    width: 1.5,
                    curveness: 0.05
                },
                emphasis: {
                    focus: 'adjacency',
                    lineStyle: { width: 3 }
                }
            }]
        };
        graphChart.setOption(option);
        
        // 移除旧的监听，避免事件重复叠加
        graphChart.off('click');
        graphChart.on('click', function(params) {
            if (document.body.classList.contains('chat-locked')) {
                return;
            }
            if (params.dataType === 'node' && params.data) {
                const node = params.data;
                if (node.node_type === 'chapter') {
                    S.currentNode = "";
                    S.graphNode = node.name;
                    renderGraph(); // 立即触发点击高亮
                    sendChat(`我想学习《随机信号分析》大纲中的章节：【${node.name}】。请为我梳理这一章的核心研究对象、前后知识关联以及它能解决什么工程问题。`);
                } else if (node.node_type === 'section') {
                    S.currentNode = "";
                    S.graphNode = node.name;
                    renderGraph(); // 立即触发点击高亮
                    sendChat(`我想学习小节：【${node.name}】（属于章节：${node.chapter}）。请帮我梳理这一节的核心概念、它们在物理上的直觉理解，以及常见的工程应用场景。`);
                } else { // topic
                    if (node.kp_node_id) {
                        S.currentNode = node.kp_node_id;
                        S.graphNode = node.name;
                        fetchNodeAndShowCard(node.kp_node_id); // 立即拉取并更新右侧的知识点卡片，实现即时渲染
                    } else {
                        S.currentNode = "";
                        S.graphNode = node.name;
                    }
                    renderGraph(); // 立即触发点击高亮
                    sendChat(`请帮我深入剖析核心知识点：【${node.name}】。希望包含它的数学公式定义、物理含义、以及我们在做系统实验或仿真时需要注意的常见误区。`);
                }
            }
        });

        // ✨ 动态微调力导向参数，生成极其平缓和微妙的漂浮/呼吸感抖动动效
        if (!graphChart.driftTimer) {
            let t = 0;
            graphChart.driftTimer = setInterval(() => {
                t += 0.08; // 极其缓慢的自增步长，使波动更柔和
                if (graphChart && S.page === 'knowledge-map') {
                    graphChart.setOption({
                        series: [{
                            force: {
                                repulsion: 180 + 3 * Math.sin(t), // 微小的斥力波动
                                gravity: 0.08 + 0.002 * Math.cos(t) // 极其细微的重力摆动
                            }
                        }]
                    });
                } else {
                    clearInterval(graphChart.driftTimer);
                    graphChart.driftTimer = null;
                }
            }, 2500); // 延长重绘周期至 2.5 秒，降低重绘频次和能耗
        }
    } catch (e) {
        console.error("渲染知识图谱失败:", e);
    }
}

async function explainNode(node) {
    const messagesEl = document.getElementById('chat-messages');
    if (!messagesEl) return;
    
    const userMsgId = 'msg-' + Date.now() + '-U';
    const loadingId = 'msg-' + Date.now() + '-A';

    messagesEl.insertAdjacentHTML('beforeend', `
        <div class="chat-msg user" id="${userMsgId}">
            <div class="bubble">请讲解「${node.name}」</div>
        </div>
        <div class="chat-msg assistant" id="${loadingId}">
            <div class="bubble">
                <div class="typing-dots"><span></span><span></span><span></span></div>
            </div>
        </div>
    `);
    messagesEl.scrollTop = messagesEl.scrollHeight;

    try {
        const payload = {
            name: node.name,
            node_type: node.node_type,
            chapter: node.chapter || "",
            section: node.section || "",
            topics: node.topics || []
        };
        const data = await api('/api/knowledge/ai-explain', { method: 'POST', body: JSON.stringify(payload) });
        
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) {
            const bubbleEl = loadingEl.querySelector('.bubble');
            renderAndAttach(bubbleEl, data.reply, []);
        }
        scrollToMessage(loadingEl, messagesEl);
    } catch(e) {
        const errEl = document.getElementById(loadingId);
        if (errEl) errEl.innerHTML = `<div class="bubble" style="color:#e74c3c;">智能体讲解生成失败。</div>`;
    }
}

async function applyFilter(type, shouldScroll = true) {
    if (!S.signalData) { alert("请先在信号工坊生成基底观测序列！"); return; }
    try {
        const windowSize = parseInt(document.getElementById('filter-window-size').value) || 10;
        const cutoffFreq = parseFloat(document.getElementById('filter-cutoff').value) || 500;
        const body = {
            signal_type: document.getElementById('sig-type').value,
            freq: parseFloat(document.getElementById('sig-freq').value) || 200,
            fs: parseInt(document.getElementById('sig-fs').value) || 10000,
            snr_db: parseFloat(document.getElementById('sig-snr').value) || 10,
            filter_type: type,
            window_size: windowSize,
            cutoff_freq: cutoffFreq,
            bandwidth: parseFloat(document.getElementById('sig-bandwidth').value) || 50,
            freq_end: parseFloat(document.getElementById('sig-freq-end').value) || 300,
        };
        const data = await api('/api/signal/filter', { method: 'POST', body: JSON.stringify(body) });
        if (data.error) { alert(data.error); return; }
        data.filter_type = type;
        data.signal_type = body.signal_type;
        data.freq = body.freq;
        S.filteredData = data;
        S.filterParams = { filter_type: type, window_size: windowSize, cutoff_freq: cutoffFreq };
        updateInlineCharts();

        // 插入本地系统提示，同步感知
        const messagesEl = document.getElementById('chat-messages');
        if (messagesEl) {
            const filterNames = { 'moving_average': '滑动平均滤波', 'rc_lowpass': 'RC一阶低通滤波', 'wiener': '自适应维纳滤波' };
            const filterName = filterNames[type] || type;
            let paramDetail = "";
            if (type === 'moving_average') {
                paramDetail = `（窗口大小 N=${windowSize}）`;
            } else if (type === 'rc_lowpass') {
                paramDetail = `（截止频率 f_c=${cutoffFreq} Hz）`;
            } else if (type === 'wiener') {
                paramDetail = `（自适应 MMSE 估计）`;
            }
            messagesEl.insertAdjacentHTML('beforeend', `
                <div class="chat-msg assistant" style="opacity: 0.9; margin: 4px 0;">
                    <div class="bubble" style="background: rgba(46,204,113,0.05); border-left: 3px solid #2ecc71; padding: 10px 14px; font-size: 13px;">
                        ⚙️ <strong>系统感知同步:</strong> 已运行${filterName}${paramDetail}。AI 助教 Clar 已同步输入与响应的数字特征，您可以点击“💡 让 Clar 分析滤波结果”按钮进行分析。
                    </div>
                </div>
            `);
            if (shouldScroll) {
                messagesEl.scrollTop = messagesEl.scrollHeight;
            }
        }

        document.getElementById('filter-result').style.display = 'flex';
        const aiBtn = document.getElementById('btn-filter-ai-analyze');
        if (aiBtn) aiBtn.style.display = 'inline-block';
        const filterNames = { 'moving_average': '滑动平均滤波器输出', 'rc_lowpass': 'RC低通滤波器输出', 'wiener': '自适应维纳滤波最佳线性估计输出' };
        document.getElementById('filter-title').innerText = filterNames[type] || '线性系统输出特性';
        const el = document.getElementById('filter-plot');
        Plotly.purge(el);

        const freq = parseFloat(document.getElementById('sig-freq').value) || 200;
        const sigType = document.getElementById('sig-type').value;
        const tMax = (sigType === '线性调频(LFM)' || sigType === '瑞利分布')
            ? S.signalData.t[S.signalData.t.length - 1]
            : Math.min(S.signalData.t[S.signalData.t.length - 1], Math.max(0.01, 8 / freq));
        const fs = parseInt(document.getElementById('sig-fs').value) || 10000;
        const visibleSamplesCount = tMax * fs;

        const layout = { 
            height: 270,
            margin: { l: 40, r: 15, t: 15, b: 35 }, 
            paper_bgcolor: 'transparent', 
            plot_bgcolor: 'transparent',
            xaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, range: [0, tMax], zeroline: false, showline: false },
            yaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, zeroline: false, showline: false },
            showlegend: true,
            legend: { orientation: 'h', y: 1.15, font: { size: 10 } }
        };

        const filterTraces = [
            { 
                y: data.noisy_fine || data.noisy, 
                x: data.t_fine || S.signalData.t, 
                name: '输入信号 X(t)', 
                line: { width: 0.8, color: '#ccc' } 
            },
            { 
                y: data.filtered_fine || data.filtered, 
                x: data.t_fine || S.signalData.t, 
                name: '响应输出 Y(t)', 
                line: { width: 1.4, color: '#e74c3c' } 
            }
        ];

        if (visibleSamplesCount <= 150) {
            filterTraces.push({
                y: data.filtered,
                x: S.signalData.t,
                name: '滤波样本点',
                mode: 'markers',
                marker: { size: 5, color: '#e74c3c' }
            });
        }

        Plotly.newPlot(el, filterTraces, layout, { responsive: true, displayModeBar: false });
    } catch(e) {
        alert('滤波失败: ' + e.message);
    }
}

async function runKalmanSimulation(shouldScroll = true) {
    try {
        const qInput = document.getElementById('kalman-q');
        const rInput = document.getElementById('kalman-r');
        const v0Input = document.getElementById('kalman-v0');

        let qVal = parseFloat(qInput.value);
        let rVal = parseFloat(rInput.value);
        let v0Val = parseFloat(v0Input.value);

        if (isNaN(qVal)) { qVal = 0.1; qInput.value = "0.1"; }
        if (isNaN(rVal)) { rVal = 1.0; rInput.value = "1.0"; }
        if (isNaN(v0Val)) { v0Val = 1.0; v0Input.value = "1.0"; }
        
        const body = {
            q: qVal,
            r: rVal,
            v0: v0Val,
            duration: 0.5,
            fs: 1000
        };
        
        const data = await api('/api/signal/kalman', { method: 'POST', body: JSON.stringify(body) });
        if (data.error) { alert(data.error); return; }
        S.kalmanData = data;
        S.kalmanParams = { q: qVal, r: rVal, v0: v0Val };
        updateInlineCharts();
        
        // 插入本地系统提示，同步感知
        const messagesEl = document.getElementById('chat-messages');
        if (messagesEl) {
            messagesEl.insertAdjacentHTML('beforeend', `
                <div class="chat-msg assistant" style="opacity: 0.9; margin: 4px 0;">
                    <div class="bubble" style="background: rgba(155,89,182,0.05); border-left: 3px solid #9b59b6; padding: 10px 14px; font-size: 13px;">
                        ⚙️ <strong>系统感知同步:</strong> 已运行卡尔曼递归估计仿真（参数：过程噪声强度 q=${qVal}, 测量噪声标准差 σ_v=${rVal}, 初速度 v₀=${v0Val}）。收敛误差协方差与卡尔曼增益特征已同步，您可以点击“💡 让 Clar 分析卡尔曼仿真”按钮进行分析。
                    </div>
                </div>
            `);
            if (shouldScroll) {
                messagesEl.scrollTop = messagesEl.scrollHeight;
            }
        }
        
        document.getElementById('kalman-result').style.display = 'flex';
        const aiBtn = document.getElementById('btn-kalman-ai-analyze');
        if (aiBtn) aiBtn.style.display = 'inline-block';
        
        // Plot 1: Position Tracking (pos_true, pos_meas, pos_est)
        const posEl = document.getElementById('kalman-pos-plot');
        Plotly.purge(posEl);
        
        const posLayout = {
            height: 230,
            margin: { l: 40, r: 15, t: 15, b: 35 },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            xaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, zeroline: false, showline: false },
            yaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, zeroline: false, showline: false },
            showlegend: true,
            legend: { orientation: 'h', y: 1.15, font: { size: 10 } }
        };
        
        const posTraces = [
            { y: data.pos_true, x: data.t, name: '真实位置 p(t)', line: { width: 2, color: '#4285f4' } },
            { y: data.pos_meas, x: data.t, name: '含噪观测 z(t)', mode: 'markers', marker: { size: 3, color: '#e74c3c', opacity: 0.5 } },
            { y: data.pos_est, x: data.t, name: '卡尔曼估计 ̂p(t)', line: { width: 2, color: '#27ae60' } }
        ];
        
        Plotly.newPlot(posEl, posTraces, posLayout, { responsive: true, displayModeBar: false });
        
        // Plot 2: Velocity Tracking (vel_true, vel_est)
        const velEl = document.getElementById('kalman-vel-plot');
        Plotly.purge(velEl);
        
        const velLayout = {
            height: 210,
            margin: { l: 40, r: 15, t: 15, b: 35 },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            xaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, zeroline: false, showline: false },
            yaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, zeroline: false, showline: false },
            showlegend: true,
            legend: { orientation: 'h', y: 1.15, font: { size: 10 } }
        };
        
        const velTraces = [
            { y: data.vel_true, x: data.t, name: '真实速度 v(t)', line: { width: 1.5, color: '#9b59b6' } },
            { y: data.vel_est, x: data.t, name: '估计速度 ̂v(t)', line: { width: 2, color: '#f1c40f' } }
        ];
        
        Plotly.newPlot(velEl, velTraces, velLayout, { responsive: true, displayModeBar: false });
        
        // Plot 3: Covariance & Gain Convergence (p_error_pos, k_gain_pos, k_gain_vel)
        const covEl = document.getElementById('kalman-cov-plot');
        Plotly.purge(covEl);
        
        const covLayout = {
            height: 210,
            margin: { l: 40, r: 15, t: 15, b: 35 },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            xaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, zeroline: false, showline: false },
            yaxis: { gridcolor: 'rgba(0,0,0,0.03)', tickfont: { size: 10 }, zeroline: false, showline: false },
            showlegend: true,
            legend: { orientation: 'h', y: 1.15, font: { size: 10 } }
        };
        
        const covTraces = [
            { y: data.p_error_pos, x: data.t, name: '协方差 P₁₁ (位置)', line: { width: 1.5, color: '#e67e22' } },
            { y: data.k_gain_pos, x: data.t, name: '卡尔曼增益 K₁ (位置)', line: { width: 1.5, color: '#1abc9c' } },
            { y: data.k_gain_vel, x: data.t, name: '卡尔曼增益 K₂ (速度)', line: { width: 1.5, color: '#34495e' } }
        ];
        
        Plotly.newPlot(covEl, covTraces, covLayout, { responsive: true, displayModeBar: false });
        
        // Dispatch resize to align ECharts / Plotly correctly
        window.dispatchEvent(new Event('resize'));
        
    } catch(e) {
        alert('卡尔曼仿真失败: ' + e.message);
    }
}

async function analyzeFilterResult() {
    if (!S.signalData || !S.filteredData || !S.filterParams) return;
    const type = document.getElementById('sig-type').value;
    const freq = parseFloat(document.getElementById('sig-freq').value) || 200;
    const fs = parseInt(document.getElementById('sig-fs').value) || 10000;
    const snr = parseFloat(document.getElementById('sig-snr').value) || 10;
    
    const filterType = S.filterParams.filter_type;
    const filterName = { 'moving_average': '滑动平均滤波', 'rc_lowpass': 'RC一阶低通滤波', 'wiener': '维纳滤波' }[filterType];
    
    let filterParamsText = "";
    if (filterType === 'moving_average') {
        filterParamsText = `窗口大小 N = ${S.filterParams.window_size}`;
    } else if (filterType === 'rc_lowpass') {
        filterParamsText = `截止频率 f_c = ${S.filterParams.cutoff_freq} Hz`;
    } else if (filterType === 'wiener') {
        filterParamsText = `在最小均方误差准则下估计`;
    }

    const featsBefore = S.signalData.features;
    const featsAfter = S.filteredData.features;

    const beforeText = `均值 E[X] = ${featsBefore.mean.toFixed(4)}，方差 D[X] = ${featsBefore.variance.toFixed(4)}，均方值 RMS = ${featsBefore.rms.toFixed(4)}`;
    const afterText = `均值 E[Y] = ${featsAfter.mean.toFixed(4)}，方差 D[Y] = ${featsAfter.variance.toFixed(4)}，均方值 RMS = ${featsAfter.rms.toFixed(4)}`;

    const prompt = `我刚才使用「${filterName}」（参数：${filterParamsText}）处理了「${type}」含噪观测序列。
基底参数为：起始/中心频率 = ${freq} Hz，采样率 fs = ${fs} Hz，信噪比 SNR = ${snr} dB。
滤波前特征：${beforeText}
滤波后特征：${afterText}
请帮我深入剖析本次线性系统实验的物理和理论机制：
1. 观察特征指标的变化（如方差/均方值的下降幅度），分析该滤波器对宽带白噪声的抑制能力是否符合期望，并解释均值在滤波前后的变化（系统是否无偏？）。
2. 从频域系统函数的角度，剖析该滤波器是如何对输入序列的功率谱进行整形的。
3. 结合本次滤波类型（如是滑动平均的时域平滑，RC低通的冲激响应卷积，还是维纳滤波的最佳均方估值），说明其背后的核心数学原理与工程应用场景。
4. 提示一个该滤波方式容易产生的仿真误差或实际局限（如过渡带、时延、或者Wiener非因果实现问题）。`;

    sendChat(prompt);
}

async function analyzeKalmanResult() {
    if (!S.kalmanParams || !S.kalmanData) return;
    const q = S.kalmanParams.q;
    const r = S.kalmanParams.r;
    const v0 = S.kalmanParams.v0;

    const pHistory = S.kalmanData.p_error_pos;
    const kGainPos = S.kalmanData.k_gain_pos;
    const kGainVel = S.kalmanData.k_gain_vel;

    const pFinal = pHistory[pHistory.length - 1];
    const k1Final = kGainPos[kGainPos.length - 1];
    const k2Final = kGainVel[kGainVel.length - 1];

    const prompt = `我刚才运行了二维状态空间卡尔曼滤波跟踪模拟。
仿真配置参数为：
过程噪声强度 q = ${q}，测量噪声标准差 r = ${r}，初速度 v₀ = ${v0}。
卡尔曼滤波收敛状态：
最终位置误差协方差 P₁₁ ＝ ${pFinal.toFixed(6)}，最终位置增益 K₁ ＝ ${k1Final.toFixed(6)}，最终速度增益 K₂ ＝ ${k2Final.toFixed(6)}。
请结合卡尔曼滤波的状态空间递推理论，为我剖析以下内容：
1. 过程噪声 q 与测量噪声 r 的相对比值（即信噪比/不确定度比值）是如何决定卡尔曼增益 K₁ 和 K₂ 的收敛位置的？如果增大测量噪声标准差 r，增益和协方差会如何变化？
2. 为什么位置观测 z(t) 的引入，能够实现对未直接观测变量（速度 v(t)）的估计？这与状态空间的“可观测性”有什么内在联系？
3. 卡尔曼滤波的预测（Predict）和更新（Update）两大核心递推步骤在本次跟踪中具体发挥了什么物理作用？
4. 请用生动的语言解释，为什么误差协方差 P₁₁ 的演进轨迹是快速单调下降并趋于恒定的？这代表了什么物理过程？`;

    sendChat(prompt);
}

function resetAll() {
    S.signalData = null; primaryCardData = null; secondaryCardData = null; lastAiReply = "";
    S.filteredData = null; S.filterParams = null; S.kalmanParams = null; S.kalmanData = null;
    S.currentNode = null; S.graphNode = null;
    
    const aiBtn = document.getElementById('btn-ai-analyze');
    if (aiBtn) aiBtn.style.display = 'none';
    
    document.getElementById('signal-metrics').style.display = 'none';
    document.getElementById('filter-result').style.display = 'none';
    const fAiBtn = document.getElementById('btn-filter-ai-analyze');
    if (fAiBtn) fAiBtn.style.display = 'none';
    
    if(document.getElementById('kalman-result')) {
        document.getElementById('kalman-result').style.display = 'none';
        Plotly.purge('kalman-pos-plot');
        Plotly.purge('kalman-vel-plot');
        Plotly.purge('kalman-cov-plot');
    }
    const kAiBtn = document.getElementById('btn-kalman-ai-analyze');
    if (kAiBtn) kAiBtn.style.display = 'none';
    
    document.getElementById('time-analysis-type').value = 'waveform';
    document.getElementById('freq-analysis-type').value = 'amplitude';
    document.querySelectorAll('#time-tabs .analysis-tab-btn').forEach(b => b.classList.toggle('active', b.getAttribute('data-value') === 'waveform'));
    document.querySelectorAll('#freq-tabs .analysis-tab-btn').forEach(b => b.classList.toggle('active', b.getAttribute('data-value') === 'amplitude'));
    updateTabIndicators();
    updateControlVisibility();
    
    document.getElementById('chat-messages').innerHTML = '<div class="chat-msg assistant"><div class="bubble">系统状态已重置，可以开始新的实验。</div></div>';
    document.getElementById('cards-wrapper').innerHTML = '<p style="color:#8890a8; font-size:13px; text-align:center; margin-top:30px;">未激活任何知识节点。</p>';
    document.getElementById('knowledge-slot').classList.remove('active');
    Plotly.purge('waveform-plot'); Plotly.purge('spectrum-plot');
    navigate('signal-lab');
}

function initScrollMasks() {
    const scrollContainers = [
        document.getElementById('cards-wrapper'),
        document.getElementById('page-toolbox')
    ];
    
    scrollContainers.forEach(el => {
        if (!el) return;
        
        let lastState = null;
        
        const updateMask = () => {
            const scrollTop = el.scrollTop;
            const scrollHeight = el.scrollHeight;
            const clientHeight = el.clientHeight;
            
            // Check if there is actual overflow
            if (scrollHeight <= clientHeight + 4) {
                if (lastState !== 'none') {
                    el.style.maskImage = 'none';
                    el.style.webkitMaskImage = 'none';
                    lastState = 'none';
                }
                return;
            }
            
            const hasScrollTop = scrollTop > 6;
            const hasScrollBottom = scrollTop + clientHeight < scrollHeight - 6;
            
            const currentState = `${hasScrollTop}-${hasScrollBottom}`;
            if (currentState === lastState) return;
            lastState = currentState;
            
            let mask = 'none';
            if (hasScrollTop && hasScrollBottom) {
                mask = 'linear-gradient(to bottom, transparent 0%, black 24px, black calc(100% - 24px), transparent 100%)';
            } else if (hasScrollTop) {
                mask = 'linear-gradient(to bottom, transparent 0%, black 24px, black 100%)';
            } else if (hasScrollBottom) {
                mask = 'linear-gradient(to bottom, black 0%, black calc(100% - 24px), transparent 100%)';
            }
            
            el.style.maskImage = mask;
            el.style.webkitMaskImage = mask;
        };
        
        el.addEventListener('scroll', updateMask);
        
        // Listen for changes in children (e.g. chat messages added)
        const observer = new MutationObserver(updateMask);
        observer.observe(el, { childList: true, subtree: true, characterData: true });
        
        updateMask();
        el.updateScrollMask = updateMask;
    });
}

function initCustomSelect() {
    const wrapper = document.getElementById('sig-type-wrapper');
    const trigger = document.getElementById('sig-type-trigger');
    const optionsContainer = document.getElementById('sig-type-options');
    const nativeSelect = document.getElementById('sig-type');
    
    if (!wrapper || !trigger || !optionsContainer || !nativeSelect) return;
    
    const selectText = trigger.querySelector('.custom-select-text');
    
    // Toggle dropdown on trigger click
    trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        wrapper.classList.toggle('open');
    });
    
    // Close dropdown on clicking outside
    document.addEventListener('click', (e) => {
        if (!wrapper.contains(e.target)) {
            wrapper.classList.remove('open');
        }
    });
    
    // Handle option click
    const options = optionsContainer.querySelectorAll('.custom-option');
    options.forEach(opt => {
        opt.addEventListener('click', (e) => {
            e.stopPropagation();
            const val = opt.getAttribute('data-value');
            
            // Update native select
            nativeSelect.value = val;
            
            // Update UI text
            selectText.innerText = val;
            
            // Update active styling
            options.forEach(o => o.classList.remove('active'));
            opt.classList.add('active');
            
            // Close dropdown
            wrapper.classList.remove('open');
            
            // Trigger native change event for autoGenerate() etc.
            nativeSelect.dispatchEvent(new Event('change'));
        });
    });
    
    // Sync if native select is modified programmatically
    nativeSelect.addEventListener('change', () => {
        const val = nativeSelect.value;
        selectText.innerText = val;
        options.forEach(o => {
            o.classList.toggle('active', o.getAttribute('data-value') === val);
        });
    });
}

function init() {
    if (typeof marked !== 'undefined') marked.setOptions({ breaks: true, gfm: true });
    updateControlVisibility();
    initScrollMasks();
    initCustomSelect();
    
    // Load chat history & render messages
    loadChatHistory();
    renderMessages();
    
    // Add scroll tracking for outline navigation
    const chatMessagesEl = document.getElementById('chat-messages');
    if (chatMessagesEl) {
        chatMessagesEl.addEventListener('scroll', () => {
            if (S.uiMode === 'all') {
                syncActiveOutlineItem();
            }
        });
    }
    
    if (S.uiMode === 'all') {
        renderSessionList();
    }
    
    const toggleEl = document.getElementById('ui-mode-toggle');
    if (toggleEl) {
        toggleEl.addEventListener('click', toggleUIMode);
        fetch('/api/log', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: "Attached click listener to #ui-mode-toggle successfully"})
        }).catch(e => {});
    } else {
        fetch('/api/log', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: "Could NOT find #ui-mode-toggle in init()"})
        }).catch(e => {});
    }

    document.getElementById('bottom-bar').addEventListener('click', e => {
        const btn = e.target.closest('.tab-item');
        if (btn) navigate(btn.dataset.page);
    });

    // Add keydown and input auto-expand event listeners for textarea
    const chatInput = document.getElementById('chatFloatInput');
    if (chatInput) {
        chatInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                if (event.shiftKey) {
                    // Shift + Enter: Allow default newline behavior
                    return;
                } else {
                    // Enter: Send chat and prevent newline
                    event.preventDefault();
                    sendChat();
                }
            }
        });
        chatInput.addEventListener('input', function() {
            this.style.height = '56px';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
    }
    const resizeObserver = new ResizeObserver(() => {
        if (graphChart) graphChart.resize();
        const plots = ['waveform-plot', 'spectrum-plot', 'filter-plot', 'kalman-pos-plot', 'kalman-vel-plot', 'kalman-cov-plot'];
        plots.forEach(id => {
            const el = document.getElementById(id);
            if (el && el.offsetWidth > 0 && el.offsetHeight > 0 && el.innerHTML !== '') {
                try { Plotly.Plots.resize(el); } catch(err) {}
            }
        });
        
        // Update masks on resize
        const scrollContainers = ['chat-messages', 'cards-wrapper', 'page-toolbox'];
        scrollContainers.forEach(id => {
            const el = document.getElementById(id);
            if (el && el.updateScrollMask) el.updateScrollMask();
        });
        updateTabIndicators();
    });
    resizeObserver.observe(document.getElementById('main-workspace'));
    // 监听所有页面容器的显示隐藏导致的尺寸变更（解决切换选项卡时图表未渲染完全的 Bug）
    document.querySelectorAll('.page').forEach(p => resizeObserver.observe(p));
    // 监听所有 Plotly 图表容器自身的尺寸变更（解决动态显示结果面板时的尺寸对齐问题）
    ['waveform-plot', 'spectrum-plot', 'filter-plot', 'kalman-pos-plot', 'kalman-vel-plot', 'kalman-cov-plot'].forEach(id => {
        const el = document.getElementById(id);
        if (el) resizeObserver.observe(el);
    });
    // 监听 ECharts 图谱容器
    const graphEl = document.getElementById('knowledge-graph');
    if (graphEl) resizeObserver.observe(graphEl);
    
    // Setup click handlers for segmented tab selectors in time/freq cards
    document.querySelectorAll('.analysis-tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const parent = this.parentElement;
            parent.querySelectorAll('.analysis-tab-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            updateTabIndicators();
            
            const val = this.getAttribute('data-value');
            if (parent.id === 'time-tabs') {
                document.getElementById('time-analysis-type').value = val;
                updateTimePlot();
            } else if (parent.id === 'freq-tabs') {
                document.getElementById('freq-analysis-type').value = val;
                updateFreqPlot();
            }
        });
    });
    
    navigate('signal-lab');
    setTimeout(updateTabIndicators, 100);
}

window.addEventListener('load', init);
window.addEventListener('resize', () => graphChart && graphChart.resize());

// Document-level event delegation for the Clar UI mode toggle switch (absolute safety)
document.addEventListener('click', function(e) {
    const toggleBtn = e.target.closest('#ui-mode-toggle');
    if (toggleBtn) {
        fetch('/api/log', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: "Document level delegate: UI mode switch clicked! Target tag: " + e.target.tagName + ", Class: " + e.target.className})
        }).catch(err => {});
        toggleUIMode(e);
    }
}, { capture: true }); // Use capture phase to intercept clicks before other stopPropagation handlers!