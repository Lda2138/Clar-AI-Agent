import re

with open('frontend/js/ui.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Update updateNavIndicator
old_func = '''function updateNavIndicator(pageId) {
    const activeTab = document.querySelector(.nav-tabs .tab-item[data-page=""]);
    const indicator = document.getElementById('nav-indicator');
    if (activeTab && indicator) {
        indicator.style.opacity = '1';
        indicator.style.transform = 	ranslateX(px);
        indicator.style.width = ${activeTab.offsetWidth}px;
    }
}'''
new_func = '''function updateNavIndicator(pageId) {
    const activeTab = document.querySelector(.nav-tabs .tab-item[data-page=""]);
    const indicator = document.getElementById('nav-indicator');
    if (activeTab && indicator) {
        indicator.style.opacity = '1';
        indicator.style.transform = 	ranslateY(px);
        indicator.style.height = ${activeTab.offsetHeight}px;
    }
}'''
js = js.replace(old_func, new_func)

# Update resize observer
old_resize = '''window.addEventListener('resize', () => {
    const activeTab = document.querySelector('.nav-tabs .tab-item.active');
    const indicator = document.getElementById('nav-indicator');
    if (activeTab && indicator) {
        indicator.style.transform = 	ranslateX(px);
        indicator.style.width = ${activeTab.offsetWidth}px;
    }
});'''
new_resize = '''window.addEventListener('resize', () => {
    const activeTab = document.querySelector('.nav-tabs .tab-item.active');
    const indicator = document.getElementById('nav-indicator');
    if (activeTab && indicator) {
        indicator.style.transform = 	ranslateY(px);
        indicator.style.height = ${activeTab.offsetHeight}px;
    }
});'''
js = js.replace(old_resize, new_resize)

with open('frontend/js/ui.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("ui.js updated for vertical indicator.")
