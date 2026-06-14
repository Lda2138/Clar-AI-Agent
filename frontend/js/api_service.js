// frontend/js/api_service.js
// ═══════════════════════════════════════════════
// 随机信号分析 AI 助教 Clar — 核心 API 通信服务
// ═══════════════════════════════════════════════

class ApiService {
    constructor() {
        this.API_BASE = (
            window.location.protocol === 'file:' || 
            ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && window.location.port !== '8001')
        ) ? 'http://127.0.0.1:8001' : '';
        
        this.HEADERS = { 
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': 'true'
        };
    }

    async _request(endpoint, options = {}) {
        const url = `${this.API_BASE}${endpoint}`;
        try {
            const res = await fetch(url, { headers: this.HEADERS, ...options });
            if (!res.ok) {
                console.error(`API error: ${res.status} ${res.statusText} for ${url}`);
                return { error: `请求失败: HTTP ${res.status}` };
            }
            return await res.json();
        } catch (e) {
            console.error(`API Fetch/JSON parse error for ${url}:`, e);
            return { error: `网络错误或解析失败: ${e.message}` };
        }
    }

    // --- Signal Core ---
    
    async generateEnsemble(params, ensembleN = 15) {
        const payload = { ...params, ensemble_n: ensembleN };
        return await this._request('/api/signal/ensemble', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    async generateSignal(params) {
        return this._request('/api/signal/generate', { method: 'POST', body: JSON.stringify(params) });
    }

    async filterSignal(params) {
        return this._request('/api/signal/filter', { method: 'POST', body: JSON.stringify(params) });
    }

    async runKalman(params) {
        return this._request('/api/signal/kalman', { method: 'POST', body: JSON.stringify(params) });
    }

    // --- Radar & CFAR ---
    async runRadarTracking(params) {
        return this._request('/api/radar/tracking', { method: 'POST', body: JSON.stringify(params) });
    }

    // --- Chat & AI ---
    async sendChat(payload) {
        return this._request('/api/chat', { method: 'POST', body: JSON.stringify(payload) });
    }

    async sendProactiveChat(payload) {
        return this._request('/api/chat/proactive', { method: 'POST', body: JSON.stringify(payload) });
    }

    // --- Telemetry & Logs ---
    async sendTelemetry(payload) {
        return this._request('/api/telemetry', { method: 'POST', body: JSON.stringify(payload) });
    }

    async sendLog(message, source = 'client', error = null) {
        const payload = {
            message: String(message),
            source: String(source),
            error: error ? String(error) : null
        };
        return this._request('/api/log', { method: 'POST', body: JSON.stringify(payload) });
    }

    // --- Knowledge Graph ---
    async getKnowledgeGraph() {
        return this._request('/api/knowledge/graph');
    }

    async explainNode(payload) {
        return this._request('/api/knowledge/explain', { method: 'POST', body: JSON.stringify(payload) });
    }
}

// 导出单例实例供全局使用
const Api = new ApiService();
