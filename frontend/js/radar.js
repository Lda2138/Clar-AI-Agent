// frontend/js/radar.js
// ═══════════════════════════════════════════════
// 随机信号分析 AI 助教 Clar — 雷达追踪与航迹管理
// ═══════════════════════════════════════════════

let radarSimulationActive = false;
let radarPlaybackActive = false;
let radarPlaybackInterval = null;
let radarPlaybackFrame = 1;
let currentRadarStepIndex = 0; // Current active step (0-4) in LaTeX display

let radarPreloaded = false;

async function preloadRadarData() {
    if (radarPreloaded) return;
    try {
        const params = {
            Pf: 0.0001,
            R_ref: 4,
            R_pro: 2,
            drop_high_num: 10,
            threshold_offset: 30.0,
            qs: 0.01,
            gate_dist: 16.0,
            amp_drop_tol: 8.0
        };

        const data = await api('/api/radar/track', {
            method: 'POST',
            body: JSON.stringify(params)
        });

        if (data && !data.error) {
            S.radarData = data;
            S.radarParams = params;
            radarPreloaded = true;
            console.log("Radar default simulation preloaded successfully.");
        }
    } catch (e) {
        console.error("Radar preloading failed:", e);
    }
}

async function initRadarTrackingPage() {
    if (radarPlaybackActive) return;

    if (!S.radarData) {
        await preloadRadarData();
    }
    
    if (S.radarData) {
        // Show metrics and plots container
        document.getElementById('radar-metrics-row').style.display = 'flex';
        document.getElementById('radar-plots-container').style.display = 'flex';
        
        // Render step math calculations immediately
        currentRadarStepIndex = 0;
        renderRadarMathDetails();
        
        // Start playback animation
        startRadarPlayback(S.radarData);
        
        // Trigger window resize to align plots
        setTimeout(() => {
            window.dispatchEvent(new Event('resize'));
        }, 50);
    }
}

async function runRadarSimulation() {
    if (radarSimulationActive) return;
    
    const pfInput = document.getElementById('radar-pf');
    const rRefInput = document.getElementById('radar-r-ref');
    const rProInput = document.getElementById('radar-r-pro');
    const dropHighInput = document.getElementById('radar-drop-high');
    const offsetInput = document.getElementById('radar-offset');
    const qsInput = document.getElementById('radar-qs');
    const gateInput = document.getElementById('radar-gate');
    const ampLimitInput = document.getElementById('radar-amp-limit');

    let pfVal = parseFloat(pfInput.value);
    let rRefVal = parseInt(rRefInput.value);
    let rProVal = parseInt(rProInput.value);
    let dropHighVal = parseInt(dropHighInput.value);
    let offsetVal = parseFloat(offsetInput.value);
    let qsVal = parseFloat(qsInput.value);
    let gateVal = parseFloat(gateInput.value);
    let ampLimitVal = parseFloat(ampLimitInput.value);

    // Basic range validation
    if (isNaN(pfVal) || pfVal <= 0 || pfVal > 0.1) { pfVal = 1e-4; pfInput.value = "0.0001"; }
    if (isNaN(rRefVal) || rRefVal < 1) { rRefVal = 4; rRefInput.value = "4"; }
    if (isNaN(rProVal) || rProVal < 1) { rProVal = 2; rProInput.value = "2"; }
    if (isNaN(dropHighVal) || dropHighVal < 0) { dropHighVal = 10; dropHighInput.value = "10"; }
    if (isNaN(offsetVal) || offsetVal < 0) { offsetVal = 30; offsetInput.value = "30"; }
    if (isNaN(qsVal) || qsVal < 0) { qsVal = 0.01; qsInput.value = "0.01"; }
    if (isNaN(gateVal) || gateVal < 1) { gateVal = 16; gateInput.value = "16"; }
    if (isNaN(ampLimitVal) || ampLimitVal < 1) { ampLimitVal = 8; ampLimitInput.value = "8"; }

    const params = {
        Pf: pfVal,
        R_ref: rRefVal,
        R_pro: rProVal,
        drop_high_num: dropHighVal,
        threshold_offset: offsetVal,
        qs: qsVal,
        gate_dist: gateVal,
        amp_drop_tol: ampLimitVal
    };

    try {
        radarSimulationActive = true;
        stopRadarPlayback(); // Stop any active playback

        // Show loading state in button
        const runBtn = document.querySelector('#page-radar-tracking .btn-apply');
        if (runBtn) {
            runBtn.disabled = true;
            runBtn.innerText = "雷达算法仿真运行中...";
        }

        let data;
        const isDefault = (
            Math.abs(params.Pf - 0.0001) < 1e-9 &&
            params.R_ref === 4 &&
            params.R_pro === 2 &&
            params.drop_high_num === 10 &&
            Math.abs(params.threshold_offset - 30.0) < 1e-9 &&
            Math.abs(params.qs - 0.01) < 1e-9 &&
            Math.abs(params.gate_dist - 16.0) < 1e-9 &&
            Math.abs(params.amp_drop_tol - 8.0) < 1e-9
        );
        
        if (isDefault && radarPreloaded && S.radarData) {
            data = S.radarData;
            console.log("雷达追踪：直接使用客户端已预加载的默认参数仿真数据");
        } else {
            data = await api('/api/radar/track', {
                method: 'POST',
                body: JSON.stringify(params)
            });
        }

        if (data.error) {
            alert("算法运行失败: " + data.error);
            return;
        }

        S.radarData = data;
        S.radarParams = params;

        // Display results block
        document.getElementById('radar-metrics-row').style.display = 'flex';
        document.getElementById('radar-plots-container').style.display = 'flex';

        // Render step-by-step math calculations (first 5 steps) immediately
        currentRadarStepIndex = 0;
        renderRadarMathDetails();

        // Start playback animation (25 seconds, 2 frames per second -> 500ms delay)
        startRadarPlayback(data);

        // Trigger system sync notification inside chat
        const messagesEl = document.getElementById('chat-messages');
        if (messagesEl) {
            messagesEl.insertAdjacentHTML('beforeend', `
                <div class="chat-msg assistant" style="opacity: 0.9; margin: 4px 0;">
                    <div class="bubble" style="background: rgba(53, 96, 153, 0.05); border-left: 3px solid #356099; padding: 10px 14px; font-size: 13px;">
                        🎯 <strong>系统感知同步:</strong> 已完成雷达仿真（CMLD CFAR: Pf=${pfVal}, 剔除数=${dropHighVal}, Offset=${offsetVal}; Kalman: qs=${qsVal}, Gate=${gateVal}）。雷达原始回波与目标航迹已启动 25 秒实时扫描重现。
                    </div>
                </div>
            `);
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }

        // Trigger Resize to fit layout
        window.dispatchEvent(new Event('resize'));

        if (typeof checkProactiveAI === 'function') {
            checkProactiveAI();
        }
    } catch (e) {
        alert("仿真算法异常: " + e.message);
        console.error(e);
    } finally {
        radarSimulationActive = false;
        const runBtn = document.querySelector('#page-radar-tracking .btn-apply');
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.innerText = "运行雷达目标检测跟踪";
        }
    }
}

function stopRadarPlayback() {
    radarPlaybackActive = false;
    if (radarPlaybackInterval) {
        clearTimeout(radarPlaybackInterval);
        radarPlaybackInterval = null;
    }
}

function startRadarPlayback(data) {
    stopRadarPlayback();
    
    radarPlaybackActive = true;
    radarPlaybackFrame = 1;
    
    const playFrame = async () => {
        if (!radarPlaybackActive) return;
        
        // 1. Update frame input
        const frameInput = document.getElementById('radar-echo-frame');
        if (frameInput) frameInput.value = radarPlaybackFrame;
        
        // 2. Update metrics board
        const snapshot = data.frames_history[radarPlaybackFrame - 1];
        if (snapshot) {
            document.getElementById('radar-metric-frames').innerText = `${radarPlaybackFrame} / 50`;
            document.getElementById('radar-metric-fa').innerText = snapshot.stats.false_alarms_count;
            document.getElementById('radar-metric-miss').innerText = snapshot.stats.misses_count;
            document.getElementById('radar-metric-pts').innerText = snapshot.stats.track_points_count;
        }
        
        // 3. Update Left plot (Heatmap)
        await updateRadarEchoPlot(radarPlaybackFrame);
        
        // 4. Update Right plot (Tracks)
        drawRadarTracksPlotForFrame(radarPlaybackFrame);
        
        radarPlaybackFrame++;
        if (radarPlaybackFrame > 50) {
            stopRadarPlayback();
            // Show AI analysis button when completed
            const aiBtn = document.getElementById('btn-radar-ai-analyze');
            if (aiBtn) aiBtn.style.display = 'inline-block';
        } else if (radarPlaybackActive) {
            radarPlaybackInterval = setTimeout(playFrame, 500);
        }
    };
    
    // Play the first frame immediately
    playFrame();
}

async function updateRadarEchoPlot(frameIdxOverride = null) {
    const frameInput = document.getElementById('radar-echo-frame');
    let frameIdx = frameIdxOverride !== null ? frameIdxOverride : parseInt(frameInput.value);
    if (isNaN(frameIdx) || frameIdx < 1 || frameIdx > 50) {
        frameIdx = 1;
    }
    if (frameIdxOverride === null) {
        frameInput.value = frameIdx;
    }

    try {
        const frameData = await api(`/api/radar/frame/${frameIdx}`);
        if (frameData.error) {
            console.error("加载雷达帧数据失败: " + frameData.error);
            return;
        }

        const el = document.getElementById('radar-echo-plot');
        Plotly.purge(el);

        const data2D = frameData.z;
        const layout = {
            height: 290,
            margin: { l: 40, r: 15, t: 15, b: 35 },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            xaxis: {
                title: { text: 'x / 距离单元', font: { size: 10 } },
                gridcolor: 'rgba(0,0,0,0.03)',
                tickfont: { size: 9 },
                zeroline: false,
                showline: false
            },
            yaxis: {
                title: { text: 'y / 距离单元', font: { size: 10 } },
                gridcolor: 'rgba(0,0,0,0.03)',
                tickfont: { size: 9 },
                zeroline: false,
                showline: false
            }
        };

        const trace = {
            z: data2D,
            type: 'heatmap',
            colorscale: 'Viridis',
            showscale: true,
            colorbar: {
                thickness: 10,
                tickfont: { size: 8 }
            }
        };

        Plotly.newPlot(el, [trace], layout, { responsive: true, displayModeBar: false });

        // If not playing, update the tracks plot and board to sync with this frame!
        if (!radarPlaybackActive && S.radarData && S.radarData.frames_history) {
            drawRadarTracksPlotForFrame(frameIdx);
            const snapshot = S.radarData.frames_history[frameIdx - 1];
            if (snapshot) {
                document.getElementById('radar-metric-frames').innerText = `${frameIdx} / 50`;
                document.getElementById('radar-metric-fa').innerText = snapshot.stats.false_alarms_count;
                document.getElementById('radar-metric-miss').innerText = snapshot.stats.misses_count;
                document.getElementById('radar-metric-pts').innerText = snapshot.stats.track_points_count;
            }
        }

    } catch (e) {
        console.error("雷达原始回波热力图绘制失败: " + e.message);
    }
}

function drawRadarTracksPlotForFrame(frameIdx) {
    if (!S.radarData || !S.radarData.frames_history) return;
    const snapshot = S.radarData.frames_history[frameIdx - 1];
    if (!snapshot) return;

    const el = document.getElementById('radar-tracks-plot');
    Plotly.purge(el);

    const traces = [];

    // 1. False Alarms
    if (snapshot.false_alarms && snapshot.false_alarms.length > 0) {
        const faX = snapshot.false_alarms.map(p => p[1]);
        const faY = snapshot.false_alarms.map(p => p[0]);
        traces.push({
            x: faX,
            y: faY,
            mode: 'markers',
            name: '累计虚警点 (灰圆)',
            marker: {
                size: 4,
                color: 'rgba(128,128,128,0.5)',
                line: { width: 0 }
            }
        });
    }

    // 2. Misses
    if (snapshot.misses && snapshot.misses.length > 0) {
        const mX = snapshot.misses.map(p => p[1]);
        const mY = snapshot.misses.map(p => p[0]);
        traces.push({
            x: mX,
            y: mY,
            mode: 'markers',
            name: '累计漏警点 (橙叉)',
            marker: {
                symbol: 'x',
                size: 7,
                color: '#D95319',
                line: { width: 2 }
            }
        });
    }

    // 3. Confirmed Paths
    if (snapshot.confirmed_paths && snapshot.confirmed_paths.length > 0) {
        snapshot.confirmed_paths.forEach((path, idx) => {
            const pX = path.map(p => p[1]);
            const pY = path.map(p => p[0]);
            traces.push({
                x: pX,
                y: pY,
                mode: 'lines+markers',
                name: idx === 0 ? '确认轨迹航迹 (红星)' : undefined,
                showlegend: idx === 0,
                line: {
                    color: '#e74c3c',
                    width: 1.5
                },
                marker: {
                    symbol: 'star',
                    size: 5,
                    color: '#e74c3c'
                }
            });
        });
    }

    const layout = {
        height: 290,
        margin: { l: 40, r: 15, t: 15, b: 35 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        xaxis: {
            title: { text: 'x / m', font: { size: 10 } },
            gridcolor: 'rgba(0,0,0,0.03)',
            tickfont: { size: 9 },
            range: [0, 250],
            zeroline: false,
            showline: false
        },
        yaxis: {
            title: { text: 'y / m', font: { size: 10 } },
            gridcolor: 'rgba(0,0,0,0.03)',
            tickfont: { size: 9 },
            range: [0, 250],
            zeroline: false,
            showline: false
        },
        showlegend: true,
        legend: {
            orientation: 'h',
            y: 1.15,
            x: 0,
            font: { size: 9 }
        }
    };

    Plotly.newPlot(el, traces, layout, { responsive: true, displayModeBar: false });
}

function drawRadarTracksPlot() {
    // Fallback in case called without frame indexing
    if (!S.radarData) return;
    drawRadarTracksPlotForFrame(50);
}

function matrixToLatex(mat, isVector = false) {
    if (!mat) return '';
    if (isVector) {
        // 1D array
        return '\\begin{bmatrix} ' + mat.map(v => v.toFixed(3)).join(' \\\\ ') + ' \\end{bmatrix}';
    }
    // 2D array [row][col]
    return '\\begin{bmatrix} ' + mat.map(row => row.map(v => v.toFixed(3)).join(' & ')).join(' \\\\ ') + ' \\end{bmatrix}';
}

function renderRadarMathDetails() {
    const el = document.getElementById('radar-math-details');
    if (!S.radarData || !S.radarData.step_calculations || S.radarData.step_calculations.length === 0) {
        el.innerHTML = `<div style="color: #64748b; padding: 10px; text-align: center;">未能生成卡尔曼递推演算步骤，可能由于此参数下没有检测到目标或没有进行关联。请尝试减小 Offset 偏置或增大虚警概率 Pf。</div>`;
        return;
    }

    const steps = S.radarData.step_calculations;
    
    // Create step selection bar
    let selectionHtml = `<div class="analysis-tabs" id="radar-math-tabs" style="width: 100%; margin-bottom: 12px; flex-wrap: nowrap; overflow-x: auto; white-space: nowrap; justify-content: flex-start;">`;
    steps.forEach((step, idx) => {
        const activeClass = idx === currentRadarStepIndex ? 'active' : '';
        selectionHtml += `<button class="analysis-tab-btn ${activeClass}" onclick="switchRadarMathStep(${idx})" style="flex-shrink: 0;">第${step.frame}帧 (ID:${step.track_id})</button>`;
    });
    selectionHtml += `</div>`;
    
    let contentContainer = `<div id="radar-math-content"></div>`;
    el.innerHTML = selectionHtml + contentContainer;
    
    updateRadarMathContent();
}

function updateRadarMathContent() {
    const container = document.getElementById('radar-math-content');
    if (!container || !S.radarData || !S.radarData.step_calculations) return;
    
    const steps = S.radarData.step_calculations;
    const step = steps[currentRadarStepIndex];
    if (!step) return;

    // Convert matrices to latex
    const x_pred_latex = matrixToLatex(step.x_pred, true);
    const P_pred_latex = matrixToLatex(step.P_pred);
    const z_meas_latex = matrixToLatex(step.z_meas, true);
    const K_latex = matrixToLatex(step.K);
    const x_est_latex = matrixToLatex(step.x_est, true);
    const P_est_latex = matrixToLatex(step.P_est);

    // State transition matrix F and measurement matrix H formulas
    const F_latex = '\\begin{bmatrix} 1 & 1 & 0 & 0 \\\\ 0 & 1 & 0 & 0 \\\\ 0 & 0 & 1 & 1 \\\\ 0 & 0 & 0 & 1 \\end{bmatrix}';
    const H_latex = '\\begin{bmatrix} 1 & 0 & 0 & 0 \\\\ 0 & 0 & 1 & 0 \\end{bmatrix}';

    let contentHtml = `
        <div style="display: flex; flex-direction: column; gap: 14px; background: rgba(255,255,255,0.4); border-radius: 12px; padding: 16px; border: 1px solid rgba(255,255,255,0.5);">
            <div>
                <strong style="color: #1e293b;">1. 状态预测方程 (State Prediction):</strong>
                <p style="margin: 4px 0 8px 10px;">状态一步预测方程为：$$\\hat{x}_{k|k-1} = F \\hat{x}_{k-1|k-1}$$ 协方差预测方程为：$$P_{k|k-1} = F P_{k-1|k-1} F^T + Q$$</p>
                <div style="overflow-x: auto; margin-left: 10px;">
                    $$\\hat{x}_{k|k-1} = ${F_latex} \\cdot \\hat{x}_{k-1|k-1} = ${x_pred_latex}$$
                    $$P_{k|k-1} = ${P_pred_latex}$$
                </div>
            </div>
            
            <div style="border-top: 1px dashed rgba(0,0,0,0.06); padding-top: 10px;">
                <strong style="color: #1e293b;">2. 量测更新方程 (Measurement & Kalman Gain):</strong>
                <p style="margin: 4px 0 8px 10px;">雷达检测提取的目标距离量测为：$$z_k = ${z_meas_latex}$$ 观测矩阵为：$$H = ${H_latex}$$</p>
                <p style="margin: 4px 0 8px 10px;">计算卡尔曼增益矩阵：$$K_k = P_{k|k-1} H^T (H P_{k|k-1} H^T + R)^{-1}$$</p>
                <div style="overflow-x: auto; margin-left: 10px;">
                    $$K_k = ${K_latex}$$
                </div>
            </div>
            
            <div style="border-top: 1px dashed rgba(0,0,0,0.06); padding-top: 10px;">
                <strong style="color: #1e293b;">3. 状态估计与协方差更新 (State & Covariance Update):</strong>
                <p style="margin: 4px 0 8px 10px;">融合当前帧观测值后的状态后验估计：$$\\hat{x}_{k|k} = \\hat{x}_{k|k-1} + K_k (z_k - H \\hat{x}_{k|k-1})$$</p>
                <p style="margin: 4px 0 8px 10px;">更新后的估计误差协方差矩阵：$$P_{k|k} = (I - K_k H) P_{k|k-1}$$</p>
                <div style="overflow-x: auto; margin-left: 10px;">
                    $$\\hat{x}_{k|k} = ${x_est_latex}$$
                    $$P_{k|k} = ${P_est_latex}$$
                </div>
            </div>
        </div>
    `;

    container.innerHTML = contentHtml;
    
    // Force KaTeX to render all equations
    renderMath(container);
    
    // Update tab indicators for the new tabs
    if (typeof updateTabIndicators === 'function') {
        setTimeout(updateTabIndicators, 50);
    }
}

function switchRadarMathStep(index) {
    currentRadarStepIndex = index;
    
    const tabsContainer = document.getElementById('radar-math-tabs');
    if (tabsContainer) {
        const btns = tabsContainer.querySelectorAll('.analysis-tab-btn');
        btns.forEach((btn, idx) => {
            if (idx === index) btn.classList.add('active');
            else btn.classList.remove('active');
        });
    }
    
    updateRadarMathContent();
}

async function analyzeRadarTracking() {
    if (!S.radarData || !S.radarParams) return;
    const pf = S.radarParams.Pf;
    const r_ref = S.radarParams.R_ref;
    const r_pro = S.radarParams.R_pro;
    const drop_high = S.radarParams.drop_high_num;
    const offset = S.radarParams.threshold_offset;
    const qs = S.radarParams.qs;
    const gate = S.radarParams.gate_dist;
    const amp_limit = S.radarParams.amp_drop_tol;

    const stats = S.radarData.stats;
    const fa_count = stats.false_alarms_count;
    const miss_count = stats.misses_count;
    const pts_count = stats.track_points_count;

    const prompt = `我刚才运行了雷达 CMLD 检测与多目标卡尔曼跟踪仿真。
仿真配置参数为：
- CMLD CFAR 参数：虚警概率 Pf = ${pf}，参考窗 R_ref = ${r_ref}，保护窗 R_pro = ${r_pro}，剔除单元数 D_high = ${drop_high}，门限偏置 Offset = ${offset}
- 卡尔曼跟踪参数：过程噪声强度 qs = ${qs}，关联波门 Gate = ${gate}，量测幅度差值门限 = ${amp_limit} dB

仿真累积统计指标：
- 累积处理帧数：50 帧
- 累积虚警点 (灰圆)：${fa_count} 个
- 累积漏警点 (橙叉)：${miss_count} 个
- 累积真实航迹点 (红星)：${pts_count} 个

请结合《随机信号分析》课程中的雷达信号处理、恒虚警检测(CFAR)及 Kalman 滤波器状态估计与多目标数据关联理论，为我深入且通俗易懂地剖析：
1. 结合 CMLD CFAR 的数学原理，剖析为什么需要偏置 Offset？当参考单元数量受限或被干扰污染时，CMLD 是如何通过剔除最大 ${drop_high} 个单元并动态查表计算乘子来保持检测性能的？
2. 剖析航迹管理中“暂定 (Tentative)”、“确认 (Confirmed)”和“删除 (Deleted)”的三阶段生命周期规则。如何防止虚警信号误判为目标轨迹？又是如何判别目标丢失并及时删除航迹的？
3. 卡尔曼预测（预测状态和协方差矩阵）以及更新（引入量测修正）在应对雷达漏警（即无数据关联）时，为什么能让轨迹平滑外推？
4. 如果我们想降低累计漏警点数（即减少橙叉），我们应该如何联合调整检测 Offset、虚警率 Pf、波门 Gate 等参数？这会带来什么副作用（如虚警的上升）？`;

    // Direct navigate to chat tab is handled by chat routing or state, but click to send
    sendChat(prompt);
}
