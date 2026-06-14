import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add CSS polish
new_css = '''
/* Cycle 7-9: Typography & Uniformity */
.card, .kc-card {
    padding: 24px;
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.45) 0%, rgba(255, 255, 255, 0.25) 100%) padding-box,
                linear-gradient(135deg, rgba(255, 255, 255, 0.6) 0%, rgba(255, 255, 255, 0.05) 100%) border-box;
    border: 1px solid transparent;
    box-shadow: 0 8px 32px rgba(15, 23, 42, 0.03), inset 0 1px 1px rgba(255, 255, 255, 0.7);
}
h2 {
    font-weight: 700;
    font-size: 22px;
    color: #0f172a;
    letter-spacing: -0.5px;
    margin-bottom: 8px;
}
.subtitle {
    font-size: 14px;
    color: #475569;
    line-height: 1.6;
    margin-bottom: 24px;
}
/* Ensure headers inside cards have the orange accent */
.card h3, .kc-card h4 {
    position: relative;
    padding-left: 12px;
}
.card h3::before, .kc-card h4::before {
    content: '';
    position: absolute;
    left: 0;
    top: 15%;
    height: 70%;
    width: 4px;
    background: #C95C16;
    border-radius: 4px;
}
/* Optimize backdrop-filter performance by limiting it to necessary elements */
.ai-header::before {
    will-change: transform;
}

/* Remove bottom-bar css (Clean up) */
#bottom-bar { display: none !important; }
'''

html = html.replace('</style>', new_css + '\n</style>')

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Cycles 6-10 Polish applied.")
