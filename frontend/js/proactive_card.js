// frontend/js/proactive_card.js

const proactiveStyles = `
/* Proactive Card Styles */
#proactive-card-container {
    position: fixed;
    bottom: 90px;
    right: 30px;
    z-index: 9998;
    width: 320px;
    perspective: 1000px;
}

.proactive-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(255, 255, 255, 0.4) 100%);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.8);
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 10px 30px rgba(31, 38, 135, 0.15), inset 0 1px 2px rgba(255, 255, 255, 0.9);
    transform-origin: bottom right;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    opacity: 0;
}

.proactive-card.slide-in {
    animation: card-slide-in 0.65s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.proactive-card.slide-out {
    animation: card-slide-out 0.5s cubic-bezier(0.25, 0.8, 0.25, 1) forwards;
}

@keyframes card-slide-in {
    0% { 
        opacity: 0; 
        transform: translateY(40px) scale(0.9) rotateY(15deg) rotateX(10deg); 
        filter: blur(6px);
    }
    100% { 
        opacity: 1; 
        transform: translateY(0) scale(1) rotateY(0deg) rotateX(0deg); 
        filter: blur(0);
    }
}
@keyframes card-slide-out {
    0% { 
        opacity: 1; 
        transform: translateY(0) scale(1) rotateY(0deg) rotateX(0deg); 
        filter: blur(0);
    }
    100% { 
        opacity: 0; 
        transform: translateY(30px) scale(0.92) rotateY(-5deg) rotateX(-5deg); 
        filter: blur(4px);
    }
}

.pc-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
}
.pc-icon {
    font-size: 16px;
}
.pc-title {
    font-size: 14px;
    font-weight: 700;
    color: #2a4e7c;
    flex: 1;
    margin-left: 8px;
}
.pc-close {
    background: none;
    border: none;
    font-size: 18px;
    color: #64748b;
    cursor: pointer;
    line-height: 1;
}
.pc-close:hover {
    color: #0f172a;
}
.pc-content {
    font-size: 13px;
    color: #1e293b;
    line-height: 1.5;
    margin-bottom: 14px;
}
.pc-insight {
    font-weight: 600;
    margin-bottom: 6px;
}
.pc-precomp {
    color: #475569;
}
.pc-footer {
    display: flex;
    justify-content: flex-end;
}
.pc-action-btn {
    background: linear-gradient(135deg, #4c85cc, #356099);
    color: white;
    border: 1px solid rgba(255,255,255,0.3);
    padding: 8px 14px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 10px rgba(53, 96, 153, 0.2);
    transition: all 0.3s ease;
}
.pc-action-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 14px rgba(53, 96, 153, 0.3);
}
.pc-action-btn:active {
    transform: translateY(0);
}
`;

const styleSheet = document.createElement("style");
styleSheet.type = "text/css";
styleSheet.innerText = proactiveStyles;
document.head.appendChild(styleSheet);

class ClarSpriteController {
    constructor() {
        this.el = document.getElementById('ai-mode-sprite-toggle');
        this.state = 'listening';
    }
    
    updateVisibility() {
        // Visibility is dynamically handled by CSS state-classic and state-clar-ball transitions
    }
    
    setState(newState) {
        if (!this.el) return;
        this.el.classList.remove('state-listening', 'state-thinking', 'state-action');
        this.state = newState;
        this.el.classList.add(`state-${this.state}`);
        
        if (newState === 'action') {
            this.el.style.transform = 'scale(1.2)';
            setTimeout(() => {
                this.el.style.transform = '';
            }, 300);
        }
    }
}

class ProactiveCardController {
    constructor() {
        this.container = document.createElement('div');
        this.container.id = 'proactive-card-container';
        document.body.appendChild(this.container);
    }
    
    show(data) {
        if (!this.container) return;
        
        const { insight, pre_computation_text, action_type, action_payload, action_label } = data;
        
        this.container.innerHTML = `
            <div class="proactive-card slide-in">
                <div class="pc-header">
                    <span class="pc-icon">✨</span>
                    <span class="pc-title">Clar 洞察</span>
                    <button class="pc-close" onclick="ProactiveCard.close()">×</button>
                </div>
                <div class="pc-content">
                    <div class="pc-insight">${insight}</div>
                    <div class="pc-precomp">${pre_computation_text}</div>
                </div>
                <div class="pc-footer">
                    <button class="pc-action-btn" onclick="ProactiveCard.executeAction('${action_type}', '${encodeURIComponent(JSON.stringify(action_payload))}')">
                        ${action_label}
                    </button>
                </div>
            </div>
        `;
    }
    
    close() {
        if (!this.container) return;
        const card = this.container.querySelector('.proactive-card');
        if (card) {
            card.classList.remove('slide-in');
            card.classList.add('slide-out');
            setTimeout(() => {
                this.container.innerHTML = '';
            }, 400);
        }
    }
    
    executeAction(type, payloadStr) {
        const payload = JSON.parse(decodeURIComponent(payloadStr));
        this.close();
        
        if (type === 'run_wiener_filter') {
            if (typeof navigate === 'function') navigate('toolbox');
            const filterTypeEl = document.getElementById('filter-type');
            if (filterTypeEl) filterTypeEl.value = 'wiener';
            // Wait for navigation animation
            setTimeout(() => {
                if (typeof applyFilter === 'function') applyFilter('wiener');
            }, 500);
        } else if (type === 'navigate_to_signal_lab') {
            if (typeof navigate === 'function') navigate('signal-lab');
                } else if (type === 'apply_kalman_params') {
            if (payload.q !== undefined) {
                const el = document.getElementById('kalman-q');
                if (el) el.value = payload.q;
            }
            if (payload.r !== undefined) {
                const el = document.getElementById('kalman-r');
                if (el) el.value = payload.r;
            }
            if (payload.v0 !== undefined) {
                const el = document.getElementById('kalman-v0');
                if (el) el.value = payload.v0;
            }
            if (typeof runKalmanSimulation === 'function') runKalmanSimulation();
        } else if (type === 'expand_ai_panel') {
            if (typeof toggleAiMode === 'function') {
                toggleAiMode('classic');
            }
        }
    }
}

function initProactiveUI() {
    if (!window.ClarSprite) {
        window.ClarSprite = new ClarSpriteController();
    }
    if (!window.ProactiveCard) {
        window.ProactiveCard = new ProactiveCardController();
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initProactiveUI);
} else {
    initProactiveUI();
}
