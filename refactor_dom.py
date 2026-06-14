import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract footer
footer_match = re.search(r'(<footer id="bottom-bar">.*?</footer>)', html, re.DOTALL)
if not footer_match:
    print("Footer not found")
    exit(1)

footer_html = footer_match.group(1)

nav_tabs_match = re.search(r'(<div class="nav-tabs" id="main-nav-tabs">.*?</div>)\s*<div class="signal-controls">', footer_html, re.DOTALL)
signal_controls_match = re.search(r'(<div class="signal-controls">.*?)</footer>', footer_html, re.DOTALL)

nav_tabs = nav_tabs_match.group(1)
signal_controls = signal_controls_match.group(1).strip()

# New Layout Strings
sidebar_html = f'''
    <aside class="sidebar">
        <div class="sidebar-logo">
            <span style="color: #C95C16; font-weight: bold; font-size: 24px;">C</span>lar
        </div>
        {nav_tabs}
    </aside>
'''

topbar_html = f'''
    <header class="top-bar">
        {signal_controls}
    </header>
'''

# We need to wrap #main-row in .app-layout and .main-column
# Find <div id="main-row">
main_row_idx = html.find('<div id="main-row">')

# We need to find the end of #main-row. It ends right before <footer id="bottom-bar">
# Let's replace the whole block from main-row to footer.
pattern = r'(<div id="main-row">.*?)\s*<footer id="bottom-bar">.*?</footer>'

replacement = f'''<div class="app-layout">
{sidebar_html}
    <div class="main-column">
{topbar_html}
        \\1
    </div>
</div>
'''

new_html = re.sub(pattern, replacement, html, flags=re.DOTALL)

# Add CSS for new layout
css_to_add = '''
/* App Layout */
.app-layout {
    display: flex;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
    background: #f8fafc;
}

.sidebar {
    width: 80px;
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px 0;
    z-index: 100;
}

.sidebar-logo {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 40px;
    color: #0f172a;
}

.sidebar .nav-tabs {
    display: flex;
    flex-direction: column;
    gap: 20px;
    width: 100%;
    align-items: center;
    background: transparent;
    border: none;
    padding: 0;
}

.sidebar .nav-indicator {
    width: 4px;
    height: 40px;
    background: #C95C16;
    border-radius: 0 4px 4px 0;
    left: 0;
    top: 0;
    position: absolute;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.sidebar .tab-item {
    padding: 10px;
    width: 60px;
    height: 60px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    white-space: pre-wrap; /* allow wrapping for narrow sidebar */
    font-size: 12px;
    position: relative;
    color: #64748b;
}

.sidebar .tab-item.active {
    color: #C95C16;
    background: rgba(201, 92, 22, 0.05);
}

.main-column {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    height: 100%;
}

.top-bar {
    height: 70px;
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    align-items: center;
    padding: 0 24px;
    z-index: 90;
    box-shadow: 0 2px 10px rgba(0,0,0,0.02);
}

.top-bar .signal-controls {
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
    flex-wrap: wrap;
}

/* Override #main-row for new layout */
#main-row {
    flex: 1;
    margin-bottom: 0;
    padding: 24px;
    height: calc(100vh - 70px);
}

body {
    padding: 0; /* Remove body padding */
}
'''

new_html = new_html.replace('</style>', css_to_add + '\n</style>')

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print("Layout refactored.")
