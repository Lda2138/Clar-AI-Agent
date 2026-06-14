import os

files_to_update = {
    'frontend/index.html': [],
    'frontend/js/state.js': [],
    'frontend/js/ui.js': [],
    'frontend/js/chat.js': [],
    'frontend/js/radar.js': [],
    'frontend/js/telemetry.js': [],
    'frontend/js/proactive_card.js': []
}

# 1. Update index.html
with open('frontend/index.html', 'r', encoding='utf-8') as f:
    idx_content = f.read()

idx_content = idx_content.replace(
    '<script src="js/state.js?v=2.2.0"></script>',
    '<script src="js/api_service.js?v=2.2.0"></script>\n  <script src="js/state.js?v=2.2.0"></script>'
)

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(idx_content)


# 2. Update state.js (Remove api function and constants)
with open('frontend/js/state.js', 'r', encoding='utf-8') as f:
    state_content = f.read()

api_func_block = '''const API_HEADERS = { 
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true'
};'''
state_content = state_content.replace(api_func_block, '')

api_func_block2 = '''const API_BASE = (
    window.location.protocol === 'file:' || 
    ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && window.location.port !== '8001')
) 
    ? 'http://127.0.0.1:8001' 
    : '';

async function api(url, opts = {}) {
    const res = await fetch(API_BASE + url, { headers: API_HEADERS, ...opts });
    if (!res.ok) {
        console.error(API error:   for );
        return null;
    }
    try {
        return await res.json();
    } catch (e) {
        console.error(API JSON parse error for :, e);
        return null;
    }
}'''
state_content = state_content.replace(api_func_block2, '')

with open('frontend/js/state.js', 'w', encoding='utf-8') as f:
    f.write(state_content)


# 3. Update ui.js (Use Api instead of api('/api/...'))
with open('frontend/js/ui.js', 'r', encoding='utf-8') as f:
    ui_content = f.read()

ui_content = ui_content.replace(
    "const data = await api('/api/signal/generate', { method: 'POST', body: JSON.stringify(params) });",
    "const data = await Api.generateSignal(params);"
)
ui_content = ui_content.replace(
    "const data = await api('/api/signal/filter', { method: 'POST', body: JSON.stringify(params) });",
    "const data = await Api.filterSignal(params);"
)
ui_content = ui_content.replace(
    "const data = await api('/api/signal/kalman', { method: 'POST', body: JSON.stringify(params) });",
    "const data = await Api.runKalman(params);"
)

with open('frontend/js/ui.js', 'w', encoding='utf-8') as f:
    f.write(ui_content)


# 4. Update radar.js (Use Api instead of api('/api/...'))
with open('frontend/js/radar.js', 'r', encoding='utf-8') as f:
    radar_content = f.read()

radar_content = radar_content.replace(
    "const data = await api('/api/radar/tracking', { method: 'POST', body: JSON.stringify(params) });",
    "const data = await Api.runRadarTracking(params);"
)

with open('frontend/js/radar.js', 'w', encoding='utf-8') as f:
    f.write(radar_content)


# 5. Update proactive_card.js
with open('frontend/js/proactive_card.js', 'r', encoding='utf-8') as f:
    proac_content = f.read()

proac_content = proac_content.replace(
    "const data = await api('/api/knowledge/graph');",
    "const data = await Api.getKnowledgeGraph();"
)
proac_content = proac_content.replace(
    "const data = await api('/api/knowledge/explain', { method: 'POST', body: JSON.stringify(payload) });",
    "const data = await Api.explainNode(payload);"
)

with open('frontend/js/proactive_card.js', 'w', encoding='utf-8') as f:
    f.write(proac_content)

print("Frontend Decoupling Complete")
