with open('frontend/js/charts.js', 'r', encoding='utf-8') as f:
    content = f.read()
    if "['章节', '小节', '核心知识点']" in content:
        print("Legend is STILL in charts.js")
    else:
        print("Legend is definitely removed from charts.js")
