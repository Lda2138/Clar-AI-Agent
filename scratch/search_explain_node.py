import os

search_phrase = "explainNode"
for root, dirs, files in os.walk("c:/Users/Lda001/Desktop/the-agent/agent-by-DZLiu"):
    for file in files:
        if file.endswith(('.js', '.html', '.py')):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if search_phrase in content:
                        print(f"Found in {path}")
            except Exception:
                pass
