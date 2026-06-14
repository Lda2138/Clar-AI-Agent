import os

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

replacements_html = [
    ('font-family: \'Plus Jakarta Sans\', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;', 'font-family: \'Times New Roman\', SimSun, \'宋体\', serif;'),
    ('💡 让 Clar 分析当前信号', 'AI 分析当前信号'),
    ('💡 让 Clar 分析滤波结果', 'AI 分析滤波结果'),
    ('💡 让 Clar 分析卡尔曼仿真', 'AI 分析卡尔曼仿真'),
    ('💡 让 Clar 分析跟踪结果', 'AI 分析跟踪结果'),
    ('⚡ 雷达目标卡尔曼滤波数学递推与状态演算', '雷达目标卡尔曼滤波数学递推与状态演算'),
    ('📥 导出对话', '导出对话'),
    ('🎲 抛洒系综', '蒙特卡洛系综'),
    ('🎵 试听信号', '试听音频'),
    ('📥 导出 CSV', '导出 CSV'),
    # Fix buttons gradients
    ('background: linear-gradient(135deg, #C95C16, #b04f10); box-shadow: 0 4px 12px rgba(201, 92, 22,0.3);', 'background: #fff; color: #1e293b; border: 1px solid #cbd5e1; box-shadow: 0 2px 4px rgba(0,0,0,0.02);'),
    ('background: linear-gradient(135deg, #9b59b6, #8e44ad); box-shadow: 0 4px 14px rgba(155, 89, 182, 0.3);', 'background: #fff; color: #1e293b; border: 1px solid #cbd5e1; box-shadow: 0 2px 4px rgba(0,0,0,0.02);'),
    ('class="btn-apply" id="btn-filter-ai-analyze" style="padding: 4px 10px; font-size: 11px; border-radius: 8px; background: linear-gradient(135deg, #C95C16, #b04f10); box-shadow: 0 2px 8px rgba(201, 92, 22,0.2);"', 'class="btn-apply" id="btn-filter-ai-analyze" style="padding: 4px 10px; font-size: 11px; border-radius: 8px; background: #fff; color: #1e293b; border: 1px solid #cbd5e1;"'),
    ('class="btn-apply" id="btn-kalman-ai-analyze" style="display: none; padding: 4px 10px; font-size: 11px; border-radius: 8px; background: linear-gradient(135deg, #C95C16, #b04f10); box-shadow: 0 2px 8px rgba(201, 92, 22,0.2);"', 'class="btn-apply" id="btn-kalman-ai-analyze" style="display: none; padding: 4px 10px; font-size: 11px; border-radius: 8px; background: #fff; color: #1e293b; border: 1px solid #cbd5e1;"'),
    # Remove AI mode sprite toggle completely to fix layout overlap
    ('<div id="ai-mode-sprite-toggle" class="ai-mode-sprite-toggle state-classic" title="双击切换 AI 模式 (Classic / Clar-ball)">\n    <div class="sprite-core"></div>\n</div>', '<!-- Removed AI Mode Sprite to clean up layout -->')
]

replace_in_file('frontend/index.html', replacements_html)

replacements_ui = [
    ('👨‍🎓 学生', '学生'),
    ('🤖 Clar 助教', '系统助教')
]
replace_in_file('frontend/js/ui.js', replacements_ui)

replace_in_file('frontend/js/chat.js', replacements_ui)

print("Replacements done.")
