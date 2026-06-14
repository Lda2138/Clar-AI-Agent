import os

def generate_tree(dir_path, prefix=''):
    items = sorted(os.listdir(dir_path))
    # Filter out pycache, git, etc.
    items = [i for i in items if i not in ('.git', '__pycache__', '.env', 'venv', 'node_modules') and not i.endswith('.pyc')]
    
    tree_str = ""
    for i, item in enumerate(items):
        path = os.path.join(dir_path, item)
        is_last = (i == len(items) - 1)
        connector = '©¸©¤©¤ ' if is_last else '©À©¤©¤ '
        
        tree_str += prefix + connector + item + '\n'
        
        if os.path.isdir(path):
            extension = '    ' if is_last else '©¦   '
            tree_str += generate_tree(path, prefix + extension)
            
    return tree_str

root = 'c:/Users/Lda001/Desktop/the-agent/agent-by-DZLiu'
print(f"agent-by-DZLiu/\n{generate_tree(root)}")
