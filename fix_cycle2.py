import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace .top-bar .signal-controls CSS to enable space-between
css_pattern = r'(\.top-bar \.signal-controls\s*{.*?flex-wrap:\s*wrap;\s*})'
new_css = '''
.top-bar .signal-controls {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
}
.signal-params-group {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}
.signal-actions-group {
    display: flex;
    align-items: center;
    gap: 12px;
}
'''

html = re.sub(css_pattern, new_css, html, flags=re.DOTALL)

# In the HTML body, wrap the inputs into .signal-params-group and buttons into .signal-actions-group
# I will use string manipulation to find the <button> tags inside .signal-controls and wrap them.

controls_idx = html.find('<div class="signal-controls">')
if controls_idx != -1:
    end_idx = html.find('</header>', controls_idx)
    controls_html = html[controls_idx:end_idx]
    
    # We want to put everything up to the first <button> in .signal-params-group
    # and the buttons in .signal-actions-group
    button_idx = controls_html.find('<button class="btn-apply"')
    if button_idx != -1:
        params_html = controls_html[len('<div class="signal-controls">'):button_idx]
        actions_html = controls_html[button_idx:-len('</div>')].replace('</div>', '')
        
        new_controls_html = f'''<div class="signal-controls">
            <div class="signal-params-group">
                {params_html}
            </div>
            <div class="signal-actions-group">
                {actions_html}
            </div>
        </div>'''
        
        html = html[:controls_idx] + new_controls_html + html[end_idx:]

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Cycle 2 layout updated.")
