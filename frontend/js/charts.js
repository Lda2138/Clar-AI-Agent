// frontend/js/charts.js
// ═══════════════════════════════════════════════
// 随机信号分析 AI 助教 Clar — 绘图与可视化配置
// ═══════════════════════════════════════════════

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

        
        if (S.ensembleData) {
            // Plot ensemble traces
            const ensembles = S.ensembleData.ensembles_noisy;
            const renderCount = S.ensembleRenderCount || ensembles.length;
            for(let idx=0; idx<renderCount; idx++) {
                const ens = ensembles[idx];
                traces.push({
                    y: ens,
                    x: S.ensembleData.t,
                    name: idx === 0 ? '系综实现' : '',
                    showlegend: idx === 0,
                    line: { width: 1, color: 'rgba(231, 76, 60, 0.15)' },
                    hoverinfo: 'skip'
                });
            }
            traces.push({
                y: data.clean_fine || data.clean, 
                x: data.t_fine || data.t, 
                name: '纯净信号 s(t)', 
                line: { width: 2.5, color: '#4285f4' } 
            });
        } else {
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
                    name: '含噪信号 x(t)', 
                    line: { width: 1, color: '#e74c3c' } 
                }
            ];
        }
} else if (timeAnalysis === 'autocorr') {
        if (cardTitleEl) cardTitleEl.innerText = `自相关函数 Rx(τ)`;
        const freq = parseFloat(document.getElementById('sig-freq').value) || 200;
        const type = document.getElementById('sig-type').value;
        const maxLagInArray = data.autocorr_lags && data.autocorr_lags.length > 0 
            ? data.autocorr_lags[data.autocorr_lags.length - 1] 
            : 0.4;
        
        let tMaxLag = 0.05;
        if (type === '高斯白噪声') {
            tMaxLag = 0.02;
        } else if (type === '一阶马尔可夫过程') {
            tMaxLag = 0.1;
        } else if (type === '瑞利分布' || type === '窄带') {
            tMaxLag = 0.2;
        } else {
            tMaxLag = Math.min(maxLagInArray, Math.max(0.02, 8 / freq));
        }

        layout.xaxis = { 
            gridcolor: 'rgba(0,0,0,0.03)', 
            tickfont: { size: 10 }, 
            title: { text: '延时 τ (s)', font: { size: 10 } }, 
            range: [0, tMaxLag],
            zeroline: false, 
            showline: false 
        };
        
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
        const freq = parseFloat(document.getElementById('sig-freq').value) || 200;
        const type = document.getElementById('sig-type').value;
        const maxLagInArray = data.crosscorr_lags && data.crosscorr_lags.length > 0 
            ? data.crosscorr_lags[data.crosscorr_lags.length - 1] 
            : 0.4;
        
        let tMaxLag = 0.05;
        if (type === '高斯白噪声') {
            tMaxLag = 0.02;
        } else if (type === '一阶马尔可夫过程') {
            tMaxLag = 0.1;
        } else if (type === '瑞利分布' || type === '窄带') {
            tMaxLag = 0.2;
        } else {
            tMaxLag = Math.min(maxLagInArray, Math.max(0.02, 8 / freq));
        }

        layout.xaxis = { 
            gridcolor: 'rgba(0,0,0,0.03)', 
            tickfont: { size: 10 }, 
            title: { text: '延时 τ (s)', font: { size: 10 } }, 
            range: [0, tMaxLag],
            zeroline: false, 
            showline: false 
        };
        
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
        
        
        if (S.ensembleData) {
            if (cardTitleEl) cardTitleEl.innerText = '系综概率密度 (Ensemble PDF)';
            traces = [
                (function(){
                    const renderCount = S.ensembleRenderCount || S.ensembleData.ensembles_noisy.length;
                    let all_pts = [];
                    for(let i=0; i<renderCount; i++) {
                        all_pts = all_pts.concat(S.ensembleData.ensembles_noisy[i]);
                    }
                    // Simple histogram
                    let min = Math.min(...all_pts);
                    let max = Math.max(...all_pts);
                    if(min === max) { min -= 1; max += 1; }
                    let bins = 100;
                    let binWidth = (max - min) / bins;
                    let counts = new Array(bins).fill(0);
                    for(let val of all_pts) {
                        let b = Math.floor((val - min) / binWidth);
                        if(b >= bins) b = bins - 1;
                        counts[b]++;
                    }
                    // Normalize to density
                    let area = all_pts.length * binWidth;
                    let density = counts.map(c => c / area);
                    let binCenters = counts.map((_, i) => min + (i + 0.5) * binWidth);
                    
                    return {
                        x: binCenters,
                        y: density,
                        type: 'bar',
                        name: `系综 PDF (N=${renderCount})`,
                        marker: { color: 'rgba(231, 76, 60, 0.6)', line: { color: 'rgba(231, 76, 60, 1.0)', width: 1 } }
                    };
                })()
            ];
        } else {
            traces = [
                {
                    x: data.pdf_x,
                    y: data.pdf_y,
                    type: 'bar',
                    name: '观测序列 PDF',
                    marker: { color: 'rgba(231, 76, 60, 0.6)', line: { color: 'rgba(231, 76, 60, 1.0)', width: 1 } }
                }
            ];
        }
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

        const specClean = data.spec_clean || [];
        const phaseClean = data.phase_clean || [];
        const specNoisy = data.spec_noisy || [];
        const phaseNoisy = data.phase_noisy || [];
        const freqs = data.freqs || [];

        let filteredPhaseClean = [];
        let filteredPhaseNoisySignal = [];
        let filteredPhaseNoisyNoise = [];

        let hasCleanSignal = false;
        let maxClean = 0;
        if (specClean.length > 0) {
            maxClean = Math.max(...specClean);
            if (maxClean > 1e-5) {
                hasCleanSignal = true;
            }
        }

        if (hasCleanSignal) {
            const threshClean = maxClean * 0.05;
            filteredPhaseClean = phaseClean.map((val, idx) => {
                return (specClean[idx] >= threshClean) ? val : null;
            });

            const threshNoisy = maxClean * 0.05;
            for (let i = 0; i < phaseNoisy.length; i++) {
                const val = phaseNoisy[i];
                if ((specClean[i] && specClean[i] >= threshClean) || (specNoisy[i] >= threshNoisy)) {
                    filteredPhaseNoisySignal.push(val);
                    filteredPhaseNoisyNoise.push(null);
                } else {
                    filteredPhaseNoisySignal.push(null);
                    filteredPhaseNoisyNoise.push(val);
                }
            }
        } else {
            filteredPhaseClean = [];
            filteredPhaseNoisySignal = [];
            filteredPhaseNoisyNoise = [...phaseNoisy];
        }

        const sigType = document.getElementById('sig-type').value;
        const isRandom = (sigType === '高斯白噪声' || sigType === '一阶马尔可夫过程' || sigType === '瑞利分布' || sigType === '窄带');
        const phaseMode = isRandom ? 'markers' : 'lines+markers';

        traces = [];
        if (phaseClean.length > 0 && filteredPhaseClean.some(v => v !== null)) {
            traces.push({
                y: filteredPhaseClean,
                x: freqs,
                name: '纯净相位谱 θs(f)',
                mode: phaseMode,
                line: { width: 1.5, color: '#2980b9' },
                marker: { size: 4, color: '#2980b9' },
                connectgaps: false
            });
        }

        if (filteredPhaseNoisySignal.some(v => v !== null)) {
            traces.push({
                y: filteredPhaseNoisySignal,
                x: freqs,
                name: '观测相位谱-信号 θx(f)',
                mode: phaseMode,
                line: { width: 1.2, color: '#e74c3c' },
                marker: { size: 3.5, color: '#e74c3c' },
                connectgaps: false
            });
        }

        if (filteredPhaseNoisyNoise.length > 0) {
            traces.push({
                y: filteredPhaseNoisyNoise,
                x: freqs,
                name: '观测相位谱-噪声 θx(f)',
                mode: 'markers',
                marker: { size: 2.5, color: 'rgba(231, 76, 60, 0.2)' }
            });
        }
    }

    Plotly.newPlot(plotId, traces, layout, { responsive: true, displayModeBar: false });
}

async function renderGraph() {
    const el = document.getElementById('knowledge-graph');
    if (!el) return;
    
    // 确保初始时即便容器隐藏也能赋予合理的大致尺寸，避免 resize 导致节点从左上角飞入（总是向右飞的错觉）
    if (!graphChart) {
        let initOpts = {};
        if (el.clientWidth === 0) {
            const ws = document.getElementById('main-workspace');
            if (ws && ws.clientWidth > 0) {
                initOpts = { width: ws.clientWidth, height: ws.clientHeight - 80 };
            }
        }
        graphChart = echarts.init(el, null, initOpts);
    }

    try {
        // 使用状态机缓存，避免每次渲染都发起请求
        if (!S.allNodes) {
            const data = await api('/api/knowledge/graph');
            S.allNodes = data.nodes;
            S.allLinks = data.links;
        }

        const activeCardTitle = secondaryCardData ? secondaryCardData.title : "";
        
        // Removed the node initial position offset logic to prevent force layout explosion
        // Identify the primary highlighted node to anchor it in the center (0, 0)
        let primaryActiveNodeName = null;
        if (S.graphNode) {
            primaryActiveNodeName = S.graphNode;
        } else if (S.currentNode) {
            const activeNode = S.allNodes.find(n => n.kp_node_id === S.currentNode);
            if (activeNode) {
                primaryActiveNodeName = activeNode.name;
            }
        } else if (activeCardTitle) {
            primaryActiveNodeName = activeCardTitle;
        }

        // 根据当前的聚焦状态决定节点的高亮样式
        const mappedNodes = S.allNodes.map(n => {
            const isActive = (n.kp_node_id && n.kp_node_id === S.currentNode) || 
                             (S.graphNode && (n.name === S.graphNode || n.name.includes(S.graphNode) || S.graphNode.includes(n.name))) ||
                             (activeCardTitle && (n.name === activeCardTitle || n.name.includes(activeCardTitle) || activeCardTitle.includes(n.name)));
            
            const isPrimary = primaryActiveNodeName && (
                n.name === primaryActiveNodeName || 
                n.name.includes(primaryActiveNodeName) || 
                primaryActiveNodeName.includes(n.name)
            );

            const nodeObj = {
                id: n.id,
                name: n.name,
                symbolSize: isActive ? (n.symbolSize * 1.5) : (n.symbolSize * 1.15),
                
                itemStyle: {
                    color: isActive ? '#C95C16' : n.itemStyle.color,
                    shadowBlur: isActive ? 25 : 8,
                    shadowColor: isActive ? '#C95C16' : 'rgba(0,0,0,0.1)',
                    borderColor: isActive ? '#fff' : 'transparent',
                    borderWidth: isActive ? 3 : 0
                },
                label: {
                    show: isActive || n.category < 2,
                    position: 'right',
                    fontSize: isActive ? 13 : 11,
                    color: isActive ? '#b04f10' : '#2d3748',
                    fontWeight: isActive ? 'bold' : (n.category === 0 ? 'bold' : 'normal')
                },
                node_type: n.node_type,
                chapter: n.chapter,
                section: n.section,
                topics: n.topics,
                kp_node_id: n.kp_node_id
            };

            // Anchor the primary active node in the true center of the container
            if (isPrimary && graphChart) {
                nodeObj.x = graphChart.getWidth() / 2;
                nodeObj.y = graphChart.getHeight() / 2;
                nodeObj.fixed = true;
            }

            return nodeObj;
        });

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
            color: ['#356099', '#4c85cc', '#C95C16', '#E47732'],
              
            legend: { show: false },
            series: [{
                type: 'graph',
                layout: 'force',
                data: mappedNodes,
                links: S.allLinks,
                
                roam: true,
                zoom: 1.1, // Increased zoom from 0.65 to 1.1 to make the graph look larger
                animation: true,
                animationDuration: 1500,
                animationEasing: 'elasticOut', // 果冻效应
                animationDelay: function (idx) {
                    return idx * 5; // 缩短延迟避免太卡
                },
                animationDurationUpdate: 800,
                animationEasingUpdate: 'cubicOut',
                force: {
                    repulsion: 180, // Increased repulsion from 120 to 180 to spread nodes out
                    edgeLength: 65, // Increased edgeLength from 40 to 65 to give nodes more space
                    gravity: 0.12
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
                    } else {
                        S.currentNode = "";
                        S.graphNode = node.name;
                    }
                    renderGraph(); // 立即触发点击高亮
                    if (window.Telemetry) window.Telemetry.onNodeActive(S.currentNode, S.graphNode);
                    sendChat(`请帮我深入剖析核心知识点：【${node.name}】。希望包含它的数学公式定义、物理含义、以及我们在做系统实验或仿真时需要注意的常见误区。`);
                }
            }
        });

        // 绑定悬停与离开事件，用于屏幕感知功能
        graphChart.off('mouseover');
        graphChart.on('mouseover', function(params) {
            if (typeof S === 'undefined' || S.aiMode !== 'clar-ball') return;
            if (params.dataType === 'node' && params.data) {
                const node = params.data;
                const nodeType = node.node_type === 'chapter' ? '章节' : node.node_type === 'section' ? '小节' : '核心知识点';
                let text = `课程图谱节点 - 类别: ${nodeType}，名称: ${node.name}`;
                if (node.chapter) text += `，属于章节: ${node.chapter}`;
                if (node.section) text += `，对应小节: ${node.section}`;
                if (node.topics && node.topics.length > 0) text += `，相关知识要素: ${node.topics.join('、')}`;
                
                const mouseEvent = params.event ? params.event.event : null;
                if (!mouseEvent) return;
                const clientX = mouseEvent.clientX;
                const clientY = mouseEvent.clientY;
                
                const customRect = {
                    left: clientX - 10,
                    top: clientY - 10,
                    width: 20,
                    height: 20
                };
                
                if (window.Telemetry) {
                    window.Telemetry.isTrackingPaused = true;
                    window.Telemetry.triggerCustomSensing(text, customRect);
                }
            }
        });

        graphChart.off('mouseout');
        graphChart.on('mouseout', function(params) {
            if (typeof S === 'undefined' || S.aiMode !== 'clar-ball') return;
            if (params.dataType === 'node') {
                if (window.Telemetry) {
                    window.Telemetry.isTrackingPaused = false;
                    window.Telemetry.clearCustomSensing();
                }
            }
        });

        // Add dblclick to restore zoom/pan (since ECharts doesn't do it natively like Plotly)
        graphChart.getZr().off('dblclick');
        graphChart.getZr().on('dblclick', function() {
            graphChart.setOption({
                legend: { show: false },
            series: [{
                    zoom: 1.1,
                    center: null
                }]
            });
            graphChart.dispatchAction({ type: 'restore' });
        });

        // ✨ 动态微调力导向参数，生成极其平缓和微妙的漂浮/呼吸感抖动动效
        if (!graphChart.driftTimer) {
            let t = 0;
            graphChart.driftTimer = setInterval(() => {
                t += 0.08; // 极其缓慢的自增步长，使波动更柔和
                if (graphChart && S.page === 'knowledge-map') {
                    graphChart.setOption({
                        legend: { show: false },
            series: [{
                            force: {
                                repulsion: 120 + 2 * Math.sin(t), // 微小的斥力呼吸
                                gravity: 0.12 + 0.005 * Math.cos(t) // 轻微的引力波动
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
