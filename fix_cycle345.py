import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add hover states to buttons and fix scrolling
new_css = '''
/* Cycle 3-5 Polish */
.page {
    overflow-y: auto; /* enable scrolling inside pages */
}
.page::-webkit-scrollbar {
    width: 6px;
}
.page::-webkit-scrollbar-thumb {
    background: rgba(15, 23, 42, 0.1);
    border-radius: 3px;
}
.btn-apply:hover, .btn-audio:hover, .btn-export:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 6px 16px rgba(0,0,0,0.06);
}
.ctrl-item input, .ctrl-item select {
    transition: all 0.2s ease;
}
.ctrl-item input:focus, .ctrl-item select:focus {
    transform: scale(1.02);
}
.sidebar .tab-item:hover {
    background: rgba(201, 92, 22, 0.08);
    transform: scale(1.05);
}
/* Ensure charts take remaining space */
#filter-plot, #time-plot, #freq-plot, #radar-plot, #kalman-plot {
    min-height: 250px;
}
'''
html = html.replace('</style>', new_css + '\n</style>')

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Cycles 3, 4, 5 CSS Polish applied.")
