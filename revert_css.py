import os

old_css = '''
  .chat-msg {
      display: flex; gap: 10px;
      animation: msgIn 0.35s cubic-bezier(0.25, 1, 0.5, 1);
      width: 100%;
      max-width: 100%;
      min-width: 0;
      position: relative;
      transition: opacity 0.3s, transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  }
  @keyframes msgIn { from { opacity: 0; transform: translateY(16px) scale(0.98); } to { opacity: 1; transform: translateY(0) scale(1); } }
  .chat-msg:hover {
      transform: translateY(-2px);
      z-index: 10;
  }
  .chat-msg.user {
      flex-direction: row-reverse;
      gap: 0;
  }
  
  .avatar { display: none; }
  
  /* ???¦Ì? */
  .bubble {
      flex: 1; min-width: 0; max-width: 100%; padding: 12px 18px; border-radius: 16px; font-size: 14px; line-height: 1.65; word-wrap: break-word;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.02);
      transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  }
  .chat-msg.assistant .bubble {
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.45) 0%, rgba(255, 255, 255, 0.25) 100%);
      border: 1px solid rgba(255, 255, 255, 0.55);
      border-left: 4px solid #8b5cf6;
      color: #1e293b;
      backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
      border-radius: 4px 18px 18px 18px;
  }
  .chat-msg.assistant:hover .bubble {
      box-shadow: 0 12px 32px rgba(31, 38, 135, 0.12), inset 0 1px 2px rgba(255, 255, 255, 0.6);
      border-color: rgba(79, 70, 229, 0.35);
  }
  .chat-msg.user .bubble {
      background: linear-gradient(135deg, rgba(79, 70, 229, 0.18) 0%, rgba(79, 70, 229, 0.08) 100%);
      border: 1px solid rgba(79, 70, 229, 0.22);
      border-right: 4px solid #8b5cf6;
      color: #1e293b;
      backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
      border-radius: 18px 4px 18px 18px;
  }
  .chat-msg.user:hover .bubble {
      box-shadow: 0 12px 32px rgba(79, 70, 229, 0.15), inset 0 1px 2px rgba(255, 255, 255, 0.4);
      border-color: rgba(79, 70, 229, 0.35);
  }
  .chat-msg.proactive .bubble {
      background: linear-gradient(135deg, rgba(253, 244, 255, 0.6) 0%, rgba(250, 245, 255, 0.4) 100%);
      border: 1px solid rgba(216, 180, 254, 0.6);
      border-left: 4px solid #d946ef;
      box-shadow: 0 4px 20px rgba(217, 70, 239, 0.08);
      border-radius: 4px 18px 18px 18px;
      backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
  }
  .chat-msg.proactive:hover .bubble {
      box-shadow: 0 12px 32px rgba(217, 70, 239, 0.18), inset 0 1px 2px rgba(255, 255, 255, 0.7);
      border-color: rgba(217, 70, 239, 0.5);
  }
'''

file_path = 'frontend/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find('.chat-msg {')
end_idx = content.find('.proactive-badge {')

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + old_css + "\n  " + content[end_idx:]
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Reverted chat box CSS!")
else:
    print("Could not find start or end index.")
