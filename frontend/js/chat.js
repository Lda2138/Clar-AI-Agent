// frontend/js/chat.js
// ═══════════════════════════════════════════════
// 随机信号分析 AI 助教 Clar — 对话系统与内容解析
// ═══════════════════════════════════════════════

let _msgIdCounter = 0;

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
    let html = typeof marked !== 'undefined' ? marked.parse(text) : text;
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
function renderAndAttach(element, markdownText, quickQuestions = [], targetPage = null, contextSnapshot = null) {
    element.innerHTML = renderMarkdown(markdownText);
    renderMath(element);

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
            btn.onclick = () => quickAsk(q, targetPage, contextSnapshot);
            qContainer.appendChild(btn);
        });
        element.appendChild(qContainer);
        // 对插入的按钮触发二次 Math 渲染保证公式解析
        renderMath(qContainer);
    }
}

function quickAsk(text, targetPage = null, contextSnapshot = null) {
    const input = document.getElementById('chatFloatInput');
    if (input) input.value = '';
    
    const textLower = text.toLowerCase();
    let navigated = false;
    
    // 如果当前已经在知识图谱页面，点击右侧气泡追问时默认保持在当前页面，不要因为问句中的关键字跳走
    if (S.page === 'knowledge-map') {
        navigated = true;
    }
    
    // 1. 优先根据问句中的核心关键词导航至最匹配的页面
    if (!navigated && (textLower.includes("雷达") || textLower.includes("追踪") || textLower.includes("跟踪") || textLower.includes("cmld") || textLower.includes("cfar") || textLower.includes("恒虚警") || textLower.includes("观测帧") || textLower.includes("虚警") || textLower.includes("漏警") || textLower.includes("航迹") || textLower.includes("量测"))) {
        navigate('radar-tracking');
        navigated = true;
    } else if (!navigated && (textLower.includes("滤波") || textLower.includes("一阶") || textLower.includes("低通") || textLower.includes("滑动平均") || textLower.includes("lti") || textLower.includes("系统") || textLower.includes("冲击") || textLower.includes("卷积") || textLower.includes("卡尔曼") || textLower.includes("kalman") || textLower.includes("状态空间") || textLower.includes("协方差") || textLower.includes("增益") || textLower.includes("维纳") || textLower.includes("wiener") || textLower.includes("估计") || textLower.includes("估值") || textLower.includes("状态") || textLower.includes("递归") || textLower.includes("预测") || textLower.includes("更新") || textLower.includes("收敛") || textLower.includes("过程噪声") || textLower.includes("测量噪声"))) {
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
    
    sendChat(text, contextSnapshot);
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
    const slotEl = document.getElementById('knowledge-slot');
    if (slotEl) {
        slotEl.classList.add('active');
        const aiPanel = document.getElementById('ai-panel');
        if (aiPanel) aiPanel.classList.remove('expanded');
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
        kalman_k2_final: null,
        
        radar_run: !!S.radarData,
        radar_pf: (S.radarParams && S.radarParams.Pf !== undefined) ? S.radarParams.Pf : null,
        radar_r_ref: (S.radarParams && S.radarParams.R_ref !== undefined) ? S.radarParams.R_ref : null,
        radar_r_pro: (S.radarParams && S.radarParams.R_pro !== undefined) ? S.radarParams.R_pro : null,
        radar_drop_high: (S.radarParams && S.radarParams.drop_high_num !== undefined) ? S.radarParams.drop_high_num : null,
        radar_offset: (S.radarParams && S.radarParams.threshold_offset !== undefined) ? S.radarParams.threshold_offset : null,
        radar_qs: (S.radarParams && S.radarParams.qs !== undefined) ? S.radarParams.qs : null,
        radar_gate: (S.radarParams && S.radarParams.gate_dist !== undefined) ? S.radarParams.gate_dist : null,
        radar_amp_limit: (S.radarParams && S.radarParams.amp_drop_tol !== undefined) ? S.radarParams.amp_drop_tol : null,
        radar_fa_count: (S.radarData && S.radarData.stats) ? S.radarData.stats.false_alarms_count : null,
        radar_miss_count: (S.radarData && S.radarData.stats) ? S.radarData.stats.misses_count : null,
        radar_pts_count: (S.radarData && S.radarData.stats) ? S.radarData.stats.track_points_count : null
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

function lockChat() {
    document.body.classList.add('chat-locked');
    const input = document.getElementById('chatFloatInput');
    const sendBtn = document.querySelector('.send-btn');
    const chatInputWrap = document.querySelector('.chat-input-wrap');
    if (input) input.disabled = true;
    if (sendBtn) sendBtn.disabled = true;
    if (chatInputWrap) chatInputWrap.classList.add('locked');
}

// Keep track of AbortControllers for active queries so they can be recalled/cancelled
if (!S.activeControllers) {
    S.activeControllers = {};
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

function recallMessage(userMsgId, loadingId, encodedText) {
    const controller = S.activeControllers[userMsgId];
    if (controller) {
        controller.abort();
        delete S.activeControllers[userMsgId];
    }
    const userEl = document.getElementById(userMsgId);
    const loadingEl = document.getElementById(loadingId);
    if (userEl) userEl.remove();
    if (loadingEl) loadingEl.remove();
    const input = document.getElementById('chatFloatInput');
    if (input) {
        input.value = decodeURIComponent(encodedText);
        input.style.height = '56px';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        input.focus();
    }
    if (S.chatHistory && S.chatHistory.length > 0) {
        const lastMsg = S.chatHistory[S.chatHistory.length - 1];
        if (lastMsg && lastMsg.role === 'user') {
            S.chatHistory.pop();
        }
    }
    unlockChat();
}



async function sendChat(overrideText = null, contextSnapshot = null) {
    if (stagnationTimer) {
        clearTimeout(stagnationTimer);
        stagnationTimer = null;
    }

    // Ensure AI panel is visible if hidden in clar-ball mode
    const aiPanel = document.getElementById('ai-panel');
    if (aiPanel && aiPanel.classList.contains('collapsed-clar-ball')) {
        aiPanel.classList.remove('collapsed-clar-ball');
        aiPanel.classList.remove('expanded'); // ensure narrow state
    }

    if (document.body.classList.contains('chat-locked')) return;
    const input = document.getElementById('chatFloatInput');
    const textToSend = overrideText || input.value.trim();
    if (!textToSend) return;
    input.value = '';
    input.style.height = '56px'; // Reset textarea height on send

    const messagesEl = document.getElementById('chat-messages');
    const originPage = S.page; // 记录提问时的页面来源

    // 对用户消息也执行安全防破译的渲染
    const safeText = textToSend.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const userMsgHtml = renderMarkdown(safeText);

    // ✨ 彻底移除飞行动画，改用无缝插入
    const msgTs = Date.now() + '-' + (++_msgIdCounter);
    const userMsgId = 'msg-' + msgTs + '-U';
    const loadingId = 'msg-' + msgTs + '-A';

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

    // ✨ 核心修复：如果是点击历史气泡追问，则恢复当时的历史上下文和知识点状态，实现多分支语境精准定位
    if (contextSnapshot) {
        S.chatHistory = [...contextSnapshot.history];
        if (contextSnapshot.currentNode !== undefined) S.currentNode = contextSnapshot.currentNode;
        if (contextSnapshot.graphNode !== undefined) S.graphNode = contextSnapshot.graphNode;
    }

    const payload = { 
        prompt: textToSend, 
        signal_context: buildSignalContext(),
        current_node_id: S.currentNode || "",
        graph_node_name: S.graphNode || "",
        history: S.chatHistory.slice(-10)
    };
    
    S.chatHistory.push({ role: "user", content: textToSend });

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

        if (!resp.ok) {
            const errorText = await resp.text().catch(() => 'Unknown error');
            throw new Error(`Server error ${resp.status}: ${errorText}`);
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

                    if (msg.type === 'status') {
                        if (!replyText && bubbleEl) {
                            bubbleEl.innerHTML = `<div style="color: var(--primary); font-size: 0.9em; opacity: 0.8; margin-bottom: 4px;">${msg.content}</div>`;
                            if (messagesEl) {
                                messagesEl.scrollTop = messagesEl.scrollHeight;
                            }
                        }
                    } else if (msg.type === 'text') {
                        replyText += msg.content;
                        if (bubbleEl) {
                            const isAtBottom = messagesEl.scrollHeight - messagesEl.scrollTop - messagesEl.clientHeight < 120;
                            // Clean node references and render Markdown + math dynamically in the stream!
                            const cleanText = replyText.replace(/\[NODE:\s*\w+\]/g, '').trim();
                            bubbleEl.innerHTML = renderMarkdown(cleanText);
                            renderMath(bubbleEl);
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
            S.graphNode = null;
        }

        if (bubbleEl) {
            let safeReply = (data.reply || replyText || '').replace(/~~/g, '');
            const targetPage = (data.suggested_page && data.suggested_page !== 'none') ? data.suggested_page : originPage;
            const isAtBottom = messagesEl.scrollHeight - messagesEl.scrollTop - messagesEl.clientHeight < 120;
            
            // ✨ 核心修复：捕获当前时刻的上下文快照（包含当前这次的问答），将其绑定到本次回答生成的快捷追问按钮中
            const currentContext = {
                history: S.chatHistory.concat({ role: "assistant", content: safeReply }),
                currentNode: S.currentNode,
                graphNode: S.graphNode
            };
            
            renderAndAttach(bubbleEl, safeReply, data.quick_questions, targetPage, currentContext);
            if (messagesEl && isAtBottom) {
                scrollToMessage(bubbleEl, messagesEl);
            }
            if (safeReply) {
                S.chatHistory.push({ role: "assistant", content: safeReply });
            }
        }

        // ✨ AI direct signal generation execution
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

            // Always transition to signal lab on explicit generation
            navigate('signal-lab');
            
            // Trigger generation
            generateSignal(true, false);
        } else if (data.run_toolbox) {
            const tb = data.run_toolbox;
            if (tb.operation === 'moving_average') {
                if (tb.params && tb.params.window_size !== undefined && tb.params.window_size !== null) {
                    const el = document.getElementById('filter-window-size');
                    if (el) el.value = tb.params.window_size;
                }
                navigate('toolbox');
                applyFilter('moving_average', false);
            } else if (tb.operation === 'rc_lowpass') {
                if (tb.params && tb.params.cutoff_freq !== undefined && tb.params.cutoff_freq !== null) {
                    const el = document.getElementById('filter-cutoff');
                    if (el) el.value = tb.params.cutoff_freq;
                }
                navigate('toolbox');
                applyFilter('rc_lowpass', false);
            } else if (tb.operation === 'wiener') {
                navigate('toolbox');
                applyFilter('wiener', false);
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
                navigate('toolbox');
                runKalmanSimulation(false);
            }
        } else {
            // ✨ 根据大模型自主意图跳转页面（若起始页面为知识图谱，则保持在图谱页，避免图谱被重刷）
            if (data.suggested_page && data.suggested_page !== 'none' && PAGE_NAMES[data.suggested_page]) {
                if (originPage !== 'knowledge-map') {
                    let shouldNavigate = true;
                    // 如果建议跳转到工具箱，但并没有实际运行工具箱里的算法，则仅在用户明确表达了跳转/打开意图时才跳转，避免概念问答时强行切走页面
                    if (data.suggested_page === 'toolbox') {
                        const promptLower = textToSend.toLowerCase();
                        const userWantsSwitch = promptLower.includes('工具箱') || 
                                              promptLower.includes('toolbox') || 
                                              promptLower.includes('切换') || 
                                              promptLower.includes('跳转') || 
                                              promptLower.includes('打开') || 
                                              promptLower.includes('进入');
                        if (!userWantsSwitch) {
                            shouldNavigate = false;
                        }
                    }
                    if (shouldNavigate) {
                        navigate(data.suggested_page);
                    }
                }
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

function toggleAiMode(targetMode = null) {
    const toggle = document.getElementById('ai-mode-sprite-toggle');
    const aiPanel = document.getElementById('ai-panel');
    const bottomBar = document.getElementById('bottom-bar');
    
    const nextMode = targetMode || (S.aiMode === 'classic' ? 'clar-ball' : 'classic');
    if (nextMode === S.aiMode) return;
    
    if (nextMode === 'clar-ball') {
        S.aiMode = 'clar-ball';
        
        // 1. Update toggle classes (jumps and morphs)
        if (toggle) {
            toggle.classList.remove('state-classic');
            toggle.classList.add('state-clar-ball');
            toggle.classList.remove('state-thinking', 'state-action');
            toggle.classList.add('state-listening');
        }
        
        // 2. Shrink AI Panel
        if (aiPanel) {
            aiPanel.classList.add('collapsed-clar-ball');
        }
        
        // 3. Move bottom bar out of the way
        if (bottomBar) {
            bottomBar.classList.add('bottom-bar-avoid');
        }
        
        appendSystemMessage("Clar-ball (主动式智能体模式) 已开启。该模式正在重构升级中，小精灵已就位。");
        if (stagnationTimer) {
            clearTimeout(stagnationTimer);
            stagnationTimer = null;
        }
        if (window.Telemetry && window.Telemetry.idleTimer) clearInterval(window.Telemetry.idleTimer);
    } else {
        S.aiMode = 'classic';
        
        // 1. Update toggle classes (flies back)
        if (toggle) {
            toggle.classList.remove('state-clar-ball');
            toggle.classList.add('state-classic');
            toggle.classList.remove('state-listening', 'state-thinking', 'state-action');
        }
        
        // 2. Expand AI Panel
        if (aiPanel) {
            aiPanel.classList.remove('collapsed-clar-ball');
        }
        
        // 3. Reset bottom bar margin
        if (bottomBar) {
            bottomBar.classList.remove('bottom-bar-avoid');
        }
        
        appendSystemMessage("Classic (经典智能问答模式) 已恢复。我将在你探索和进行仿真实验时提供主动提示卡片。");
        resetStagnationTimer();
        if (window.Telemetry) {
            window.Telemetry.resetDwellTime();
            window.Telemetry.startIdleTracking();
        }
    }
    
    // Trigger window resize to recalculate container bounds and Plotly sizes
    setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
    }, 500);
}

function appendSystemMessage(text) {
    const messagesEl = document.getElementById('chat-messages');
    if (!messagesEl) return;
    messagesEl.insertAdjacentHTML('beforeend', `
        <div class="chat-msg assistant system-notification" style="margin-top: 10px; margin-bottom: 10px;">
            <div class="bubble" style="background: rgba(53, 96, 153, 0.05); border-left: 3px solid #356099; color: #2a4e7c; font-size: 13px; padding: 8px 12px; border-radius: 8px; max-width: 85%;">
                💡 <strong>系统提示：</strong>${text}
            </div>
        </div>
    `);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

let isCheckingProactive = false;
let stagnationTimer = null;

function resetStagnationTimer() {
    if (stagnationTimer) {
        clearTimeout(stagnationTimer);
        stagnationTimer = null;
    }
    if (S.page === 'knowledge-map' && S.aiMode === 'classic') {
        stagnationTimer = setTimeout(() => {
            checkProactiveAI(true);
        }, 90000);
    }
}

async function checkProactiveAI(isStagnation = false) {
    if (isCheckingProactive) return;
    
    // Build context
    const context = buildSignalContext();
    if (isStagnation) {
        context.stagnation = true;
        context.idle_time = 90;
        context.current_page = "knowledge-map";
        context.current_node_id = S.currentNode || "KP_CH3_03";
        context.graph_node_name = S.graphNode || "平稳随机过程的线性变换";
    }

    const payload = {
        prompt: "",
        message: "",
        signal_context: context,
        current_node_id: S.currentNode || "",
        graph_node_name: S.graphNode || "",
        history: S.chatHistory.slice(-10)
    };

    try {
        isCheckingProactive = true;
        const resp = await fetch(API_BASE + '/api/chat/proactive', {
            method: 'POST',
            headers: API_HEADERS,
            body: JSON.stringify(payload)
        });

        if (!resp.ok) {
            console.error("Proactive AI check failed:", resp.status);
            return;
        }

        const contentType = resp.headers.get("content-type") || "";
        if (contentType.includes("application/json")) {
            const json = await resp.json();
            if (json.code === 204) {
                if (isStagnation) {
                    resetStagnationTimer();
                }
                return;
            }
        }

        if (stagnationTimer) {
            clearTimeout(stagnationTimer);
            stagnationTimer = null;
        }

        const msgTs = Date.now() + '-' + (++_msgIdCounter);
        const bubbleId = 'proactive-' + msgTs + '-A';
        const messagesEl = document.getElementById('chat-messages');
        if (!messagesEl) return;

        messagesEl.insertAdjacentHTML('beforeend', `
            <div class="chat-msg assistant proactive" id="${bubbleId}">
                <div class="bubble">
                    <div class="proactive-badge">💡 主动建议</div>
                    <div class="typing-dots"><span></span><span></span><span></span></div>
                </div>
            </div>
        `);
        messagesEl.scrollTop = messagesEl.scrollHeight;

        // If in clar-ball mode, trigger active state and show Proactive Card
        if (S.aiMode === 'clar-ball') {
            if (window.ClarSprite) window.ClarSprite.setState('action');
            if (window.ProactiveCard) {
                let insightMsg = "检测到当前仿真参数配置可能存在偏差。";
                if (S.page === 'signal-lab') {
                    insightMsg = "检测到信号参数配置可能引发混叠风险（采样定理冲突）。";
                } else if (S.page === 'toolbox') {
                    insightMsg = "检测到滤波器/卡尔曼参数可能导致信号失真或不收敛。";
                } else if (S.page === 'radar-tracking') {
                    insightMsg = "检测到雷达门限或CFAR配置不佳，可能丢失估计航迹。";
                }
                window.ProactiveCard.show({
                    insight: insightMsg,
                    pre_computation_text: "我已在后台基于您当前的信号，生成了详细的物理分析与诊断。建议您点击下方按钮展开侧边栏查看详细推导。",
                    action_type: "expand_ai_panel",
                    action_payload: {},
                    action_label: "查看 Clar 深度诊断"
                });
            }
        }

        const bubbleEl = document.getElementById(bubbleId).querySelector('.bubble');
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
            buffer = lines.pop();

            for (const line of lines) {
                const cleanLine = line.trim();
                if (!cleanLine.startsWith('data:')) continue;

                try {
                    const jsonStr = cleanLine.substring(5).trim();
                    const msg = JSON.parse(jsonStr);

                    if (msg.type === 'text') {
                        replyText += msg.content;
                        if (bubbleEl) {
                            let contentEl = bubbleEl.querySelector('.proactive-content');
                            if (!contentEl) {
                                contentEl = document.createElement('div');
                                contentEl.className = 'proactive-content';
                                bubbleEl.innerHTML = `<div class="proactive-badge">💡 主动建议</div>`;
                                bubbleEl.appendChild(contentEl);
                            }
                            const cleanText = replyText.replace(/\[NODE:\s*\w+\]/g, '').trim();
                            contentEl.innerHTML = renderMarkdown(cleanText);
                            renderMath(contentEl);
                            messagesEl.scrollTop = messagesEl.scrollHeight;
                        }
                    } else if (msg.type === 'metadata') {
                        data = msg;
                    }
                } catch (e) {
                    console.error("Error parsing stream chunk:", e);
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

        if (data) {
            let safeReply = (data.reply || replyText || '').replace(/~~/g, '');
            if (bubbleEl) {
                let contentEl = bubbleEl.querySelector('.proactive-content');
                if (!contentEl) {
                    contentEl = document.createElement('div');
                    contentEl.className = 'proactive-content';
                    bubbleEl.innerHTML = `<div class="proactive-badge">💡 主动建议</div>`;
                    bubbleEl.appendChild(contentEl);
                }
                
                const currentContext = {
                    history: S.chatHistory.concat({ role: "assistant", content: safeReply }),
                    currentNode: S.currentNode,
                    graphNode: S.graphNode
                };
                
                renderAndAttach(contentEl, safeReply, data.quick_questions, null, currentContext);
                messagesEl.scrollTop = messagesEl.scrollHeight;
                
                S.chatHistory.push({ role: "assistant", content: safeReply });
            }

            if (data.node_id) {
                S.currentNode = data.node_id;
                S.graphNode = null;
            }

            if (data.new_card) {
                updateKnowledgeCards(data);
            }
            if (S.page === 'knowledge-map') {
                renderGraph();
            }
        }

    } catch (e) {
        console.error("Proactive AI request error:", e);
        const errEl = document.getElementById(bubbleId);
        if (errEl) {
            errEl.remove();
        }
    } finally {
        isCheckingProactive = false;
        if (S.aiMode === 'clar-ball' && window.ClarSprite) {
            setTimeout(() => {
                if (window.ClarSprite.state === 'action') {
                    window.ClarSprite.setState('listening');
                }
            }, 5000);
        }
    }
}

// Programmatic click and double click listener initialization
let clickTimeout = null;
function initToggleListener() {
    const toggle = document.getElementById('ai-mode-sprite-toggle');
    if (toggle) {
        // Handle screen sensing hover intent trigger when clicked in clar-ball mode
        toggle.addEventListener('click', (e) => {
            if (typeof S === 'undefined' || S.aiMode !== 'clar-ball') return;
            
            e.preventDefault();
            e.stopPropagation();
            
            if (clickTimeout) {
                clearTimeout(clickTimeout);
                clickTimeout = null;
                return;
            }
            
            clickTimeout = setTimeout(() => {
                clickTimeout = null;
                if (S.hoveredElement && S.hoveredElement.description) {
                    const desc = S.hoveredElement.description;
                    const prompt = `我刚才在屏幕上把鼠标悬停在了「${desc}」区域。请作为 Clar 助教，根据你从屏幕感知到的当前上下文（当前页面：${PAGE_NAMES[S.page] || S.page}，已同步相关物理与特征参数），猜测我的学习意图，并为我详细剖析和讲解这一部分的核心理论内涵、数学公式、物理含义以及在实际仿真实验中的常见误区。请回答完毕后，如果有明确可以自动执行的参数优化（如调整频率、采样率、滤波器参数等），请通过 JSON 格式输出 action_type 和对应的参数，以便前端自动执行。`;
                    
                    // Show the AI panel to display the answer without exiting clar-ball mode
                    const panel = document.getElementById('ai-panel');
                    if (panel) {
                        panel.classList.remove('collapsed-clar-ball'); // Important to make it visible
                        panel.classList.remove('expanded'); // Default to narrow chat panel per user preference
                    }
                    
                    // Do NOT clear sensing coordinates yet, so the ball stays near the mouse!
                    // Change state to action or thinking to reflect it's processing
                    if (window.ClarSprite) {
                        window.ClarSprite.setState('action');
                    }
                    if (window.Telemetry && window.Telemetry.tooltipEl) {
                        window.Telemetry.hideTooltip(); // Hide tooltip text, keep ball
                    }
                    
                    // Trigger proactive action evaluation in the background
                    if (window.Telemetry) {
                        if (window.Telemetry.clearTimer) {
                            clearTimeout(window.Telemetry.clearTimer);
                            window.Telemetry.clearTimer = null;
                        }
                        setTimeout(() => window.Telemetry.sendTelemetry(), 800);
                    }
                    
                    // Send the chat query
                    sendChat(prompt);
                }
            }, 250);
        });

        // Double check listener binding for mode toggle
        toggle.addEventListener('dblclick', (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (clickTimeout) {
                clearTimeout(clickTimeout);
                clickTimeout = null;
            }
            
            // If in clar-ball mode and currently sensing or showing answer, double click cancels sensing & closes panel
            if (typeof S !== 'undefined' && S.aiMode === 'clar-ball' && window.Telemetry && (window.Telemetry.hoveredEl || window.ClarSprite.state === 'action')) {
                // Return ball to original position
                window.Telemetry.clearSensing();
                // Close AI panel by putting back the collapse class
                const panel = document.getElementById('ai-panel');
                if (panel) {
                    panel.classList.remove('expanded');
                    panel.classList.add('collapsed-clar-ball');
                }
            } else {
                toggleAiMode();
            }
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initToggleListener);
} else {
    initToggleListener();
}


