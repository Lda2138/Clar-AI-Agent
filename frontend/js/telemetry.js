// frontend/js/telemetry.js
class TelemetryTracker {
    constructor() {
        this.context = {
            page: typeof S !== 'undefined' ? S.page : 'signal-lab',
            active_node_id: typeof S !== 'undefined' ? S.currentNode : '',
            active_node_name: (typeof S !== 'undefined' && S.graphNode) ? S.graphNode.name : '',
            dwell_time: 0,
            kalman_runs: 0,
            kalman_time_window: 0,
            last_kalman_time: 0
        };
        
        this.idleTimer = null;
        this.debounceTimer = null;
        this.lastDwellReset = Date.now();
        
        this.hoverTimer = null;
        this.hoveredEl = null;
        this.tooltipEl = null;
        this.clearTimer = null;
        this.isTrackingPaused = false;
        
        // Start idle tracking after a short delay to ensure S is initialized
        setTimeout(() => {
            this.startIdleTracking();
            this.initMouseTracking();
        }, 1000);
    }

    startIdleTracking() {
        if (this.idleTimer) clearInterval(this.idleTimer);
        this.idleTimer = setInterval(() => {
            if (typeof S === 'undefined') return;
            this.context.dwell_time = Math.floor((Date.now() - this.lastDwellReset) / 1000);
            
            // Trigger check if dwelling for more than 15 seconds
            if (this.context.dwell_time > 15 && this.context.dwell_time % 10 === 0) {
                this.sendTelemetry();
            }
        }, 1000);
    }

    resetDwellTime() {
        this.lastDwellReset = Date.now();
        this.context.dwell_time = 0;
    }

    // Called on page navigation
    onPageChange(newPage) {
        this.context.page = newPage;
        this.resetDwellTime();
        this.triggerEvent();
    }

    // Called on knowledge node click
    onNodeActive(nodeId, nodeName) {
        this.context.active_node_id = nodeId;
        this.context.active_node_name = nodeName;
        this.resetDwellTime();
        this.triggerEvent();
    }

    // Called on parameter tweaking / running kalman
    onKalmanRun() {
        const now = Date.now();
        if (this.context.last_kalman_time === 0) {
            this.context.kalman_time_window = 0;
        } else {
            this.context.kalman_time_window += (now - this.context.last_kalman_time) / 1000;
        }
        
        // Reset window if it has been too long since last run (> 60s)
        if (now - this.context.last_kalman_time > 60000) {
            this.context.kalman_runs = 1;
            this.context.kalman_time_window = 0;
        } else {
            this.context.kalman_runs += 1;
        }
        
        this.context.last_kalman_time = now;
        this.resetDwellTime();
        this.triggerEvent(1000); // Debounce kalman events a bit longer
    }

    triggerEvent(delay = 500) {
        if (typeof S === 'undefined') return;
        
        if (this.debounceTimer) clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.sendTelemetry();
        }, delay);
    }

    async sendTelemetry() {
        if (typeof S === 'undefined') return;
        
        if (window.ClarSprite) {
            window.ClarSprite.setState('thinking');
        }

        try {
            const payload = {
                telemetry: this.context,
                signal: {
                    signal_generated: !!(typeof S !== 'undefined' && S.signalData),
                    kalman_v0: (typeof S !== 'undefined' && S.kalmanParams) ? S.kalmanParams.v0 : 1.0
                }
            };
            
            const res = await fetch('/api/telemetry', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            if (res.status === 200) {
                const data = await res.json();
                if (data && data.action_type) {
                    if (window.ClarSprite) window.ClarSprite.setState('action');
                    if (window.ProactiveCard) {
                        window.ProactiveCard.show(data);
                    }
                    
                    // Reset contexts based on action
                    if (data.action_type === 'apply_kalman_params') {
                        this.context.kalman_runs = 0;
                        this.context.kalman_time_window = 0;
                    } else if (data.action_type === 'run_wiener_filter') {
                        this.resetDwellTime(); // prevent immediate re-trigger
                    }
                    
                    setTimeout(() => {
                        if (window.ClarSprite) window.ClarSprite.setState('listening');
                    }, 1000);
                    return;
                }
            }
            if (window.ClarSprite) window.ClarSprite.setState('listening');
        } catch (e) {
            console.error('Telemetry send failed', e);
            if (window.ClarSprite) window.ClarSprite.setState('listening');
        }
    }

    resolveSensingTarget(el) {
        if (!el) return null;
        
        // 1. Check if the element or its parent has explicit data-ai-tooltip
        let tooltipEl = el.closest('[data-ai-tooltip]');
        if (tooltipEl) {
            let text = tooltipEl.getAttribute('data-ai-tooltip');
            
            // Dynamic enhancement for charts if hovering over chart cards
            if (tooltipEl.id === 'time-card' || tooltipEl.querySelector('#waveform-plot')) {
                const timeTab = document.getElementById('time-analysis-type')?.value || 'waveform';
                const sigType = document.getElementById('sig-type')?.value || '正弦+白噪声';
                const tabNames = {
                    'waveform': '时域波形 X(t)',
                    'autocorr': '自相关函数 Rx(τ)',
                    'crosscorr': '互相关函数 Rsx(τ)',
                    'pdf': '幅值概率密度 PDF'
                };
                text = `时域分析图表 - 当前正在查看 ${sigType} 的 ${tabNames[timeTab] || '时域波形'}`;
            } else if (tooltipEl.id === 'freq-card' || tooltipEl.querySelector('#spectrum-plot')) {
                const freqTab = document.getElementById('freq-analysis-type')?.value || 'amplitude';
                const sigType = document.getElementById('sig-type')?.value || '正弦+白噪声';
                const tabNames = {
                    'amplitude': '幅度谱 |X(f)|',
                    'psd': '功率谱密度 PSD',
                    'phase': '相位谱 θ(f)'
                };
                text = `频域分析图表 - 当前正在查看 ${sigType} 的 ${tabNames[freqTab] || '幅度谱'}`;
            } else if (tooltipEl.id === 'filter-result' || tooltipEl.querySelector('#filter-plot')) {
                const filterType = (S.filterParams && S.filterParams.filter_type) ? S.filterParams.filter_type : 'moving_average';
                const filterNames = {
                    'moving_average': '滑动平均滤波器',
                    'rc_lowpass': '一阶RC低通滤波器',
                    'wiener': '维纳最佳均方估计滤波器'
                };
                text = `滤波器输出图表 - 展示通过${filterNames[filterType] || '线性变换'}处理后的输出波形与能量分布`;
            } else if (tooltipEl.querySelector('#kalman-pos-plot')) {
                text = '卡尔曼状态估计结果：位置跟踪估计曲线 (真实值、观测值、状态估计值对比)';
            } else if (tooltipEl.querySelector('#kalman-vel-plot')) {
                text = '卡尔曼状态估计结果：速度估计曲线 (真实速度与状态估计速度对比)';
            } else if (tooltipEl.querySelector('#kalman-cov-plot')) {
                text = '卡尔曼状态估计结果：误差协方差 P11 与卡尔曼增益 K1 收敛曲线';
            } else if (tooltipEl.querySelector('#radar-echo-plot')) {
                text = '三维雷达原始回波点云能量图 (X-Y 平面二维投影与强度显示)';
            } else if (tooltipEl.querySelector('#radar-tracks-plot')) {
                text = '多目标跟踪与航迹管理结果图 (估计航迹、虚警点与漏警点空间统计分布)';
            }
            
            return { element: tooltipEl, text: text };
        }
        
        // 2. Fallback: Dynamic metadata generation for any text, card, button, heading, input, module
        let current = el;
        while (current && current !== document.body) {
            // Check bottom bar navigation tabs
            if (current.classList.contains('tab-item')) {
                const tabText = current.innerText.trim();
                return { element: current, text: `页面导航菜单 - 点击切换至「${tabText}」模块` };
            }
            // Check analysis sub-tabs inside cards
            if (current.classList.contains('analysis-tab-btn')) {
                const tabText = current.innerText.trim();
                const parentTitle = current.closest('.card')?.querySelector('.card-title')?.innerText.trim() || '分析';
                return { element: current, text: `图表分析子选项卡 - 查看「${parentTitle}」下的「${tabText}」分量图` };
            }
            // Check custom select options or trigger
            if (current.classList.contains('custom-select-trigger') || current.closest('#sig-type-wrapper')) {
                const selectVal = document.getElementById('sig-type')?.value || '正弦+白噪声';
                return { element: current, text: `信号源选择下拉菜单 - 当前选定拟真信号类型：${selectVal}` };
            }
            // Check generic buttons
            if (current.tagName === 'BUTTON') {
                const btnText = current.innerText.trim().replace(/\s+/g, ' ');
                if (btnText) {
                    return { element: current, text: `操作按钮 - 点击执行「${btnText}」相关物理计算或仿真` };
                }
            }
            // Check input fields
            if (current.tagName === 'INPUT') {
                const inputId = current.id || '';
                const placeholder = current.placeholder || '';
                const val = current.value || '';
                let labelText = '';
                const parent = current.parentElement;
                if (parent && parent.querySelector('label')) {
                    labelText = parent.querySelector('label').innerText.trim();
                } else if (current.labels && current.labels.length > 0) {
                    labelText = current.labels[0].innerText.trim();
                }
                const labelDesc = labelText ? `参数「${labelText}」` : `参数项 ${inputId}`;
                return { element: current, text: `系统配置输入框 - ${labelDesc}，当前配置数值：${val}` };
            }
            // Check label tags
            if (current.tagName === 'LABEL') {
                const labelText = current.innerText.trim();
                const input = current.parentElement?.querySelector('input');
                const inputVal = input ? `，当前配置值：${input.value}` : '';
                return { element: current, text: `参数配置标签 - 「${labelText}」${inputVal}` };
            }
            // Check custom select options
            if (current.classList.contains('custom-option')) {
                const optionText = current.innerText.trim();
                const isActive = current.classList.contains('active') ? ' (当前选中)' : '';
                return { element: current, text: `下拉菜单选项 - 「${optionText}」${isActive}` };
            }
            // Check headings
            if (/^H[1-6]$/.test(current.tagName) || current.classList.contains('card-title')) {
                const text = current.innerText.trim().replace(/\s+/g, ' ');
                if (text) {
                    return { element: current, text: `文本标题 - 「${text}」` };
                }
            }
            // Check card/module text descriptions
            if (current.classList.contains('card') || current.classList.contains('metric')) {
                const text = current.innerText.trim().replace(/\s+/g, ' ');
                if (text && text.length < 150) {
                    return { element: current, text: `指标卡片 - ${text}` };
                }
            }
            // Check description subtitle paragraph
            if (current.classList.contains('subtitle')) {
                const text = current.innerText.trim().replace(/\s+/g, ' ');
                if (text && text.length < 200) {
                    return { element: current, text: `页面功能引导说明 - ${text}` };
                }
            }
            
            current = current.parentElement;
        }
        
        return null;
    }

    initMouseTracking() {
        document.addEventListener('mousemove', (e) => {
            if (typeof S !== 'undefined') {
                S.mouseX = e.clientX;
                S.mouseY = e.clientY;
            }
        });

        document.addEventListener('mouseover', (e) => {
            if (typeof S === 'undefined' || S.aiMode !== 'clar-ball') return;
            if (this.isTrackingPaused) return;
            
            const resolved = this.resolveSensingTarget(e.target);
            if (!resolved) return;
            
            const { element, text } = resolved;
            
            if (this.hoveredEl === element) {
                // Re-entered the SAME element (e.g. after a Plotly redraw)
                if (this.clearTimer) {
                    clearTimeout(this.clearTimer);
                    this.clearTimer = null;
                }
                
                // If it's not currently sensing, restart the hover timer
                const toggle = document.getElementById('ai-mode-sprite-toggle');
                const isSensing = toggle && toggle.style.left && toggle.style.left !== 'auto';
                if (!isSensing && !this.hoverTimer) {
                    this.hoverTimer = setTimeout(() => {
                        this.triggerSensing(element, text);
                    }, 1500);
                }
                return;
            }
            
            // If there is a pending clear timer, or we entered a new element, reset the old sensation first
            if (this.clearTimer) {
                clearTimeout(this.clearTimer);
                this.clearTimer = null;
                this.clearSensing();
            } else if (this.hoveredEl && this.hoveredEl !== element) {
                this.clearSensing();
            }
            
            // Clear any existing hover timer
            if (this.hoverTimer) clearTimeout(this.hoverTimer);
            this.hoveredEl = element;
            
            // Set hover timer for 1.5 seconds
            this.hoverTimer = setTimeout(() => {
                this.triggerSensing(element, text);
            }, 1500);
        });
        
        document.addEventListener('mouseout', (e) => {
            if (typeof S === 'undefined' || S.aiMode !== 'clar-ball') return;
            if (this.isTrackingPaused) return;
            
            // Prevent clearing if the mouse just moved onto the sprite ball
            if (e.relatedTarget && e.relatedTarget.closest && e.relatedTarget.closest('#ai-mode-sprite-toggle')) {
                return;
            }
            
            const resolved = this.resolveSensingTarget(e.target);
            if (!resolved) return;
            
            const { element } = resolved;
            
            // If leaving the currently hovered element
            if (this.hoveredEl === element) {
                if (this.hoverTimer) clearTimeout(this.hoverTimer);
                this.hoverTimer = null;
                // DO NOT set this.hoveredEl = null here, so that mouseover can detect re-entry (e.g. Plotly redraws)
                
                // Instead of clearing sensing instantly, set a grace period
                // to allow the user to move the mouse and click the Clar-ball.
                if (this.clearTimer) clearTimeout(this.clearTimer);
                this.clearTimer = setTimeout(() => {
                    this.clearSensing();
                    this.hoveredEl = null; // Clear it when grace period expires
                    this.clearTimer = null;
                }, 800);
            }
        });
    }

    triggerSensing(target, text) {
        if (!target || !text) return;
        
        // 1. Update S.hoveredElement context for click processing
        S.hoveredElement = {
            description: text,
            id: target.id || '',
            tagName: target.tagName,
            class: target.className
        };

        const toggle = document.getElementById('ai-mode-sprite-toggle');
        if (toggle && S.aiMode === 'clar-ball') {
            if (!toggle.style.left) {
                const rect = toggle.getBoundingClientRect();
                toggle.style.left = rect.left + 'px';
                toggle.style.top = rect.top + 'px';
                toggle.style.right = 'auto';
                void toggle.offsetWidth; // Force reflow for smooth transition
            }
            toggle.style.left = (S.mouseX - 22) + 'px';
            toggle.style.top = (S.mouseY - 22) + 'px';
        }
        
        // 2. Set Clar-ball to thinking state (purple breathing)
        if (window.ClarSprite) {
            window.ClarSprite.setState('thinking');
        }
        
        // 3. Create or update floating tooltip next to target
        this.showTooltip(target, text);
    }

    triggerCustomSensing(text, rect) {
        if (this.clearTimer) {
            clearTimeout(this.clearTimer);
            this.clearTimer = null;
        }
        
        S.hoveredElement = {
            description: text,
            id: 'echarts-knowledge-node',
            tagName: 'canvas-node',
            class: ''
        };
        
        const toggle = document.getElementById('ai-mode-sprite-toggle');
        if (toggle && S.aiMode === 'clar-ball') {
            if (!toggle.style.left) {
                const rect = toggle.getBoundingClientRect();
                toggle.style.left = rect.left + 'px';
                toggle.style.top = rect.top + 'px';
                toggle.style.right = 'auto';
                void toggle.offsetWidth;
            }
            toggle.style.left = (S.mouseX - 22) + 'px';
            toggle.style.top = (S.mouseY - 22) + 'px';
        }
        
        if (window.ClarSprite) {
            window.ClarSprite.setState('thinking');
        }
        
        this.showTooltip(rect, text);
    }

    clearCustomSensing() {
        if (this.hoverTimer) {
            clearTimeout(this.hoverTimer);
            this.hoverTimer = null;
        }
        this.hoveredEl = null;
        
        // Start the grace period before clearing sensing state
        if (this.clearTimer) clearTimeout(this.clearTimer);
        this.clearTimer = setTimeout(() => {
            this.clearSensing();
            this.clearTimer = null;
        }, 800);
    }
    
    clearSensing() {
        if (this.hoverTimer) {
            clearTimeout(this.hoverTimer);
            this.hoverTimer = null;
        }
        if (this.clearTimer) {
            clearTimeout(this.clearTimer);
            this.clearTimer = null;
        }
        this.hoveredEl = null;
        
        S.hoveredElement = null;
        
        const toggle = document.getElementById('ai-mode-sprite-toggle');
        if (toggle && toggle.style.left) {
            const targetLeft = window.innerWidth - 76; // right 32 + width 44
            const targetTop = window.innerHeight - 70;
            toggle.style.left = targetLeft + 'px';
            toggle.style.top = targetTop + 'px';
            
            setTimeout(() => {
                if (!S.hoveredElement) {
                    toggle.style.removeProperty('left');
                    toggle.style.removeProperty('top');
                    toggle.style.removeProperty('right');
                }
            }, 800);
        } else if (toggle) {
            toggle.style.removeProperty('left');
            toggle.style.removeProperty('top');
            toggle.style.removeProperty('right');
        }
        if (window.ClarSprite && window.ClarSprite.state === 'thinking') {
            window.ClarSprite.setState('listening');
        }
        this.hideTooltip();
    }

    showTooltip(target, text) {
        if (!this.tooltipEl) {
            this.tooltipEl = document.createElement('div');
            this.tooltipEl.className = 'sensing-tooltip';
            document.body.appendChild(this.tooltipEl);
        }
        
        this.tooltipEl.innerText = `[Sensing: ${text}]`;
        
        let rect;
        if (target && typeof target.getBoundingClientRect === 'function') {
            rect = target.getBoundingClientRect();
        } else if (target && target.left !== undefined) {
            rect = target; // Custom coordinate object
        } else {
            rect = { left: 0, top: 0, width: 0, height: 0, bottom: 0, right: 0 };
        }
        
        // Set coordinates based on bounding rect
        const tooltipWidth = this.tooltipEl.offsetWidth || 180;
        const tooltipHeight = this.tooltipEl.offsetHeight || 30;
        
        let left = rect.left + (rect.width - tooltipWidth) / 2;
        let top = rect.top - tooltipHeight - 8;
        
        // Boundaries
        if (left < 10) left = 10;
        if (left + tooltipWidth > window.innerWidth - 10) {
            left = window.innerWidth - tooltipWidth - 10;
        }
        if (top < 10) {
            top = (rect.bottom !== undefined ? rect.bottom : rect.top + rect.height) + 8;
        }
        
        this.tooltipEl.style.left = `${left}px`;
        this.tooltipEl.style.top = `${top}px`;
        
        // Force reflow and show
        void this.tooltipEl.offsetWidth;
        this.tooltipEl.classList.add('show');
    }
    
    hideTooltip() {
        if (this.tooltipEl) {
            this.tooltipEl.classList.remove('show');
        }
    }
}

window.Telemetry = new TelemetryTracker();
