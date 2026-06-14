// frontend/js/ui.js
// ═══════════════════════════════════════════════
// 随机信号分析 AI 助教 Clar — UI 控制与仿真操作
// ═══════════════════════════════════════════════

let autoGenTimer = null;

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
        fsInput.style.background = 'rgba(201, 92, 22,0.08)';
        fsInput.title = state.msg;
    }
}

function updateNavIndicator(pageId) {
    const activeTab = document.querySelector(`.nav-tabs .tab-item[data-page="${pageId}"]`);
    const indicator = document.getElementById('nav-indicator');
    if (activeTab && indicator) {
        indicator.style.opacity = '1';
        indicator.style.transform = `translateX(${activeTab.offsetLeft}px)`;
        indicator.style.width = `${activeTab.offsetWidth}px`;
    }
}

function navigate(pageId) {
    // Always update the indicator position, even if we're already on this page
    // (useful for initialization)
    updateNavIndicator(pageId);
    
    if (S.page === pageId) return; // ✨ 核心：避免当前页面下的重复导航及 ECharts 图谱重新渲染/刷新！
    
    // Determine direction for slide animation
    const pages = ['signal-lab', 'knowledge-map', 'toolbox', 'radar-tracking']; 
    const oldIndex = pages.indexOf(S.page || 'signal-lab');
    const newIndex = pages.indexOf(pageId);
    
    // "小号向大号滑动，动画向右" -> small to large moves right (starts from left, moves to right)
    // "大号向小号滑动，动画向左" -> large to small moves left (starts from right, moves to left)
    const direction = newIndex > oldIndex ? 'move-right' : (newIndex < oldIndex ? 'move-left' : 'scale');
    
    // Stop radar playback if switching away from radar-tracking
    if (S.page === 'radar-tracking' && pageId !== 'radar-tracking') {
        if (typeof stopRadarPlayback === 'function') {
            stopRadarPlayback();
        }
    }
    
    S.page = pageId;
    document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('active', 'slide-in-right', 'slide-in-left', 'slide-move-right', 'slide-move-left');
    });
    
    const newPage = document.getElementById('page-' + pageId);
    if (newPage) {
        newPage.classList.add('active');
        if (direction === 'move-right') newPage.classList.add('slide-move-right');
        else if (direction === 'move-left') newPage.classList.add('slide-move-left');
    }

    
    document.querySelectorAll('#bottom-bar .tab-item').forEach(btn => btn.classList.toggle('active', btn.dataset.page === pageId));

    if (pageId === 'knowledge-map') {
        S.graphEnterDirection = direction;
        const kg = document.getElementById('knowledge-graph');
        if (kg) {
            kg.classList.remove('kg-jelly-left', 'kg-jelly-right');
            void kg.offsetWidth; // trigger reflow
            if (direction === 'move-left') kg.classList.add('kg-jelly-left');
            else if (direction === 'move-right') kg.classList.add('kg-jelly-right');
        }
        setTimeout(renderGraph, 200);
    }
    if (typeof resetStagnationTimer === 'function') {
        resetStagnationTimer();
    }
    if (window.Telemetry) window.Telemetry.onPageChange(pageId);
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
                  S.signalData = data; S.filteredData = null; S.ensembleData = null;
          if (window.ensembleTimer) clearInterval(window.ensembleTimer);
        S.currentNode = SIG_NODE_MAP[params.signal_type] || 'KP_CH1_01';

        if (shouldNavigate) {
            navigate('signal-lab');
        }
        updatePlots(); // 包含时域频域的下拉框状态自动绘制
        renderMetrics(data.features, params);
        
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
                    <div class="bubble" style="background: rgba(53, 96, 153, 0.05); border-left: 3px solid #356099; padding: 10px 14px; font-size: 13px;">
                        📡 <strong>系统感知同步:</strong> 已生成 ${params.signal_type}（${freqStr}fs=${params.fs}Hz, SNR=${params.snr_db}dB${extraInfo}）。AI 助教 Clar 已同步其数字特征。
                    </div>
                </div>
            `);
            if (shouldScroll) {
                messagesEl.scrollTop = messagesEl.scrollHeight;
            }
        }
        if (typeof checkProactiveAI === 'function') {
            checkProactiveAI();
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
                indicator.style.top = activeBtn.offsetTop + 'px';
                indicator.style.width = activeBtn.offsetWidth + 'px';
                indicator.style.height = activeBtn.offsetHeight + 'px';
                indicator.style.bottom = 'auto';
                indicator.style.opacity = '1';
            } else {
                indicator.style.opacity = '0';
            }
        } else {
            indicator.style.opacity = '0';
        }
    });
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
        S.filteredData = data;
        S.filterParams = { filter_type: type, window_size: windowSize, cutoff_freq: cutoffFreq };

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
        if (typeof checkProactiveAI === 'function') {
            checkProactiveAI();
        }
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
        
        if (typeof checkProactiveAI === 'function') {
            checkProactiveAI();
        }
        if (window.Telemetry) window.Telemetry.onKalmanRun();
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
1. 过程噪声 q 与测量噪声 r 的相对比值（即信噪比/不确定度比值）是如何决定卡尔曼增益 K₁ 和 K₂ 的收敛位置 of the K1 and K2？如果增大测量噪声标准差 r，增益和协方差会如何变化？
2. 为什么位置观测 z(t) 的引入，能够实现对未直接观测变量（速度 v(t)）的估计？这与状态空间的“可观测性”有什么内在联系？
3. 卡尔曼滤波的预测（Predict）和更新（Update）两大核心递推步骤在本次跟踪中具体发挥了什么物理作用？
4. 请用生动的语言解释，为什么误差协方差 P₁₁ 的演进轨迹是快速单调下降并趋于恒定的？这代表了什么物理过程？`;

    sendChat(prompt);
}

function resetAll() {
    S.signalData = null; primaryCardData = null; secondaryCardData = null; lastAiReply = "";
    S.filteredData = null; S.filterParams = null; S.kalmanParams = null; S.kalmanData = null;
    S.radarData = null; S.radarParams = null;
    S.currentNode = null; S.graphNode = null; S.chatHistory = [];
    
    const aiBtn = document.getElementById('btn-ai-analyze');
    if (aiBtn) aiBtn.style.display = 'none';
    
    const signalMetrics = document.getElementById('signal-metrics');
    if (signalMetrics) signalMetrics.style.display = 'none';
    const filterResult = document.getElementById('filter-result');
    if (filterResult) filterResult.style.display = 'none';
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

    // Reset radar tracking views & button
    const rAiBtn = document.getElementById('btn-radar-ai-analyze');
    if (rAiBtn) rAiBtn.style.display = 'none';
    const radarMetricsRow = document.getElementById('radar-metrics-row');
    if (radarMetricsRow) radarMetricsRow.style.display = 'none';
    const radarPlotsContainer = document.getElementById('radar-plots-container');
    if (radarPlotsContainer) radarPlotsContainer.style.display = 'none';
    Plotly.purge('radar-echo-plot');
    Plotly.purge('radar-tracks-plot');
    const radarMathDetails = document.getElementById('radar-math-details');
    if (radarMathDetails) radarMathDetails.innerHTML = '请运行雷达仿真以查看卡尔曼递推计算步骤...';
    
    const timeAnalysisType = document.getElementById('time-analysis-type');
    if (timeAnalysisType) timeAnalysisType.value = 'waveform';
    const freqAnalysisType = document.getElementById('freq-analysis-type');
    if (freqAnalysisType) freqAnalysisType.value = 'amplitude';
    document.querySelectorAll('#time-tabs .analysis-tab-btn').forEach(b => b.classList.toggle('active', b.getAttribute('data-value') === 'waveform'));
    document.querySelectorAll('#freq-tabs .analysis-tab-btn').forEach(b => b.classList.toggle('active', b.getAttribute('data-value') === 'amplitude'));
    updateTabIndicators();
    updateControlVisibility();
    
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) chatMessages.innerHTML = '<div class="chat-msg assistant"><div class="bubble">系统状态已重置，可以开始新的实验。</div></div>';
    const cardsWrapper = document.getElementById('cards-wrapper');
    if (cardsWrapper) cardsWrapper.innerHTML = '<p style="color:#8890a8; font-size:13px; text-align:center; margin-top:30px;">未激活任何知识节点。</p>';
    const knowledgeSlot = document.getElementById('knowledge-slot');
    if (knowledgeSlot) knowledgeSlot.classList.remove('active');
    Plotly.purge('waveform-plot'); Plotly.purge('spectrum-plot');
    navigate('signal-lab');
}

function initScrollMasks() {
    const scrollContainers = [
        document.getElementById('cards-wrapper'),
        document.getElementById('page-toolbox'),
        document.getElementById('page-radar-tracking')
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

// Window resize handler to reposition the sliding nav indicator
window.addEventListener('resize', () => {
    const activeTab = document.querySelector('.nav-tabs .tab-item.active');
    const indicator = document.getElementById('nav-indicator');
    if (activeTab && indicator) {
        indicator.style.transform = `translateX(${activeTab.offsetLeft}px)`;
        indicator.style.width = `${activeTab.offsetWidth}px`;
    }
});

async function generateEnsembleData() {
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
        const data = await api('/api/signal/ensemble', { method: 'POST', body: JSON.stringify({...params, ensemble_n: 15}) });
        if (data.error) { alert(data.error); return; }
        
        if (!S.signalData || S.signalData.features.mean === undefined) {
             await generateSignal(false, false);
        }
        
        S.ensembleData = data;
        navigate('signal-lab');
        
        // Start animation loop
        S.ensembleRenderCount = 1;
        updatePlots();
        
        if (window.ensembleTimer) clearInterval(window.ensembleTimer);
        window.ensembleTimer = setInterval(() => {
            if (S.ensembleRenderCount < data.ensembles_noisy.length) {
                S.ensembleRenderCount++;
                updatePlots();
            } else {
                clearInterval(window.ensembleTimer);
            }
        }, 150); // 150ms delay between each trace
        
    } catch (err) {
        console.error(err);
    }
}
