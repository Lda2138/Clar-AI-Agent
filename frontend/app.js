// frontend/app.js
// ═══════════════════════════════════════════════
// 随机信号分析 AI 助教 Clar — 主程序入口
// ═══════════════════════════════════════════════

function init() {
    if (typeof marked !== 'undefined') marked.setOptions({ breaks: true, gfm: true });
    updateControlVisibility();
    initScrollMasks();
    initCustomSelect();
    document.getElementById('bottom-bar').addEventListener('click', e => {
        const btn = e.target.closest('.tab-item');
        if (btn) navigate(btn.dataset.page);
    });
    
    // Double click to expand/collapse AI panel
    const aiPanel = document.getElementById('ai-panel');
    const knowledgeSlot = document.getElementById('knowledge-slot');
    if (aiPanel && knowledgeSlot) {
        aiPanel.addEventListener('dblclick', function(e) {
            const tag = e.target.tagName.toLowerCase();
            if (tag === 'textarea' || tag === 'button' || tag === 'a' || tag === 'img' || e.target.closest('.chat-input-wrap')) {
                return; // Ignore if clicked inside input area, interactive elements, or images
            }
            
            if (aiPanel.classList.contains('expanded')) {
                aiPanel.classList.remove('expanded');
                if (S.currentNode) {
                    knowledgeSlot.classList.add('active');
                }
            } else {
                aiPanel.classList.add('expanded');
                knowledgeSlot.classList.remove('active');
            }
            
            // Wait for CSS transition (0.4s) to finish, then adjust scroll
            setTimeout(() => {
                const msgs = document.getElementById('chat-messages');
                if (msgs) msgs.scrollTop = msgs.scrollHeight;
            }, 400);
        });
    }

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
            
            // Trigger scroll masks update if the container has masks
            const chatMessages = document.getElementById('chat-messages');
            if (chatMessages && chatMessages.updateScrollMask) {
                chatMessages.updateScrollMask();
            }
        });
    }
    const resizeObserver = new ResizeObserver(() => {
        if (graphChart) graphChart.resize();
        const plots = ['waveform-plot', 'spectrum-plot', 'filter-plot', 'kalman-pos-plot', 'kalman-vel-plot', 'kalman-cov-plot', 'radar-echo-plot', 'radar-tracks-plot'];
        plots.forEach(id => {
            const el = document.getElementById(id);
            if (el && el.offsetWidth > 0 && el.offsetHeight > 0 && el.innerHTML !== '') {
                try { Plotly.Plots.resize(el); } catch(err) {}
            }
        });
        
        // Update masks on resize
        const scrollContainers = ['chat-messages', 'cards-wrapper', 'page-toolbox', 'page-radar-tracking'];
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
    ['waveform-plot', 'spectrum-plot', 'filter-plot', 'kalman-pos-plot', 'kalman-vel-plot', 'kalman-cov-plot', 'radar-echo-plot', 'radar-tracks-plot'].forEach(id => {
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
    
    // Preload radar default simulation data in the background
    if (typeof preloadRadarData === 'function') {
        preloadRadarData();
    }
    
    // 自动触发一次默认信号生成，避免页面图表空白
    setTimeout(() => {
        if (typeof generateSignal === 'function') {
            generateSignal();
        }
    }, 300);
}

window.addEventListener('load', init);
window.addEventListener('resize', () => graphChart && graphChart.resize());
