with open('frontend/js/charts.js', 'r', encoding='utf-8') as f:
    content = f.read()
    
idx = content.find('series: [{')
if idx != -1:
    print(content[max(0, idx-500):idx+500])
