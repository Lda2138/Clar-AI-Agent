import os

file_path = 'frontend/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# I will replace all occurrences of this repeated block with a single clean one.
# Find the start of the chat bubbles section.
start_idx = content.find('.chat-msg {')
end_idx = content.find('.proactive-badge {')

if start_idx != -1 and end_idx != -1:
    chat_css = '''
  .chat-msg {
      display: flex; gap: 12px;
      margin-bottom: 24px;
      opacity: 0; transform: translateY(10px);
      animation: msgFadeIn 0.5s forwards cubic-bezier(0.16, 1, 0.3, 1);
  }
  @keyframes msgFadeIn { to { opacity: 1; transform: translateY(0); } }
  
  .chat-avatar {
      width: 36px; height: 36px; border-radius: 12px; display: flex; align-items: center; justify-content: center;
      flex-shrink: 0; font-size: 18px;
      background: rgba(255, 255, 255, 0.5);
      box-shadow: 0 4px 12px rgba(0,0,0,0.05), inset 0 1px 1px rgba(255,255,255,0.8);
      border: 1px solid rgba(255,255,255,0.4);
  }
  .chat-msg.user .chat-avatar { background: linear-gradient(135deg, rgba(201, 92, 22, 0.2), rgba(201, 92, 22, 0.05)); border: 1px solid rgba(201, 92, 22, 0.3); }
  .chat-msg.assistant .chat-avatar, .chat-msg.proactive .chat-avatar { background: linear-gradient(135deg, rgba(53, 96, 153, 0.15), rgba(53, 96, 153, 0.05)); border: 1px solid rgba(53, 96, 153, 0.3); }
  
  .bubble {
      padding: 14px 18px; border-radius: 16px; font-size: 14.5px; line-height: 1.65; max-width: 85%;
      box-shadow: 0 4px 15px rgba(0,0,0,0.03); letter-spacing: 0.2px; word-wrap: break-word;
      transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
  }
  
  .bubble code {
      background: rgba(0, 0, 0, 0.05); padding: 2px 6px; border-radius: 6px; font-size: 0.9em; font-family: 'Consolas', monospace;
  }
  .bubble pre {
      background: rgba(15, 23, 42, 0.04); padding: 12px; border-radius: 12px; overflow-x: auto; font-size: 0.9em; font-family: 'Consolas', monospace; border: 1px solid rgba(15, 23, 42, 0.05);
  }
  .bubble table {
      width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 0.95em;
  }
  .bubble th, .bubble td {
      border: 1px solid rgba(15, 23, 42, 0.1); padding: 8px 12px; text-align: left;
  }
  .bubble th {
      background: rgba(15, 23, 42, 0.03); font-weight: 600; color: #334155;
  }
  
  .chat-msg.user { flex-direction: row-reverse; }
  .chat-msg.user .bubble {
      background: linear-gradient(135deg, #4c85cc, #356099); color: white;
      border-bottom-right-radius: 4px; box-shadow: 0 4px 12px rgba(53, 96, 153, 0.25);
  }
  
  .chat-msg.assistant .bubble, .chat-msg.proactive .bubble {
      background: rgba(255, 255, 255, 0.7); color: #1e293b;
      border: 1px solid rgba(255, 255, 255, 0.8); border-bottom-left-radius: 4px;
      backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  }
  .chat-msg.proactive .bubble { border-left: 3px solid #C95C16; background: rgba(201, 92, 22, 0.05); }
  
  .chat-msg.user:hover .bubble { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(53, 96, 153, 0.35); }
  .chat-msg.assistant:hover .bubble, .chat-msg.proactive:hover .bubble { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(0,0,0,0.06); }
'''
    new_content = content[:start_idx] + chat_css + "\n  " + content[end_idx:]
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Fixed duplication!")
else:
    print("Could not find start or end index.")
