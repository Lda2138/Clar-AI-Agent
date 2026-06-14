import os

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Restore orange background for AI analyze buttons
ai_btn_white = "background: #fff; color: #1e293b; border: 1px solid #cbd5e1;"
ai_btn_orange = "background: linear-gradient(135deg, #f59e0b, #d97706); color: #fff; border: 1px solid rgba(255, 255, 255, 0.25);"
content = content.replace(
    'id="btn-ai-analyze" style="display: none; ' + ai_btn_white,
    'id="btn-ai-analyze" style="display: none; ' + ai_btn_orange
)
content = content.replace(
    'id="btn-filter-ai-analyze" style="padding: 4px 10px; font-size: 11px; border-radius: 8px; ' + ai_btn_white,
    'id="btn-filter-ai-analyze" style="padding: 4px 10px; font-size: 11px; border-radius: 8px; ' + ai_btn_orange
)
content = content.replace(
    'id="btn-kalman-ai-analyze" style="display: none; padding: 4px 10px; font-size: 11px; border-radius: 8px; ' + ai_btn_white,
    'id="btn-kalman-ai-analyze" style="display: none; padding: 4px 10px; font-size: 11px; border-radius: 8px; ' + ai_btn_orange
)
content = content.replace(
    'id="btn-radar-ai-analyze" style="display: none; ' + ai_btn_white,
    'id="btn-radar-ai-analyze" style="display: none; ' + ai_btn_orange
)

# 2. Fix squished buttons
content = content.replace(
    '.btn-apply {',
    '.btn-apply {\n      white-space: nowrap;'
)
content = content.replace(
    '.btn-audio {',
    '.btn-audio {\n      white-space: nowrap;'
)
content = content.replace(
    '.btn-export {',
    '.btn-export {\n      white-space: nowrap;'
)
content = content.replace(
    '.tab-item {',
    '.tab-item {\n      white-space: nowrap;'
)

# 3. Fix main content padding to prevent bottom bar overlap
content = content.replace(
    '.main-content {',
    '.main-content {\n      padding-bottom: 80px; /* Prevent overlap with bottom bar */'
)

# 4. Fix clar-ball overlapping with export button
content = content.replace(
    'right: 120px;',
    'right: 80px;\n      top: 14px; /* Align nicely with the header */'
)

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Aesthetics and layout fixed.")
