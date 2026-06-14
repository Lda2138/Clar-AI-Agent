import os
import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

print("Original length:", len(content))

# We need to transform the layout.
# Let's extract the main parts:
# 1. header (Clar title, btn-export) -> We will move the title to the sidebar, and btn-export to TopBar.
# 2. #cards-wrapper -> Will be inside <main>
# 3. #ai-panel -> Keep it as is, inside <div class="app-layout">
# 4. #bottom-bar -> We will split it into Sidebar Nav and TopBar Controls.

# Let's write a targeted script to extract and replace.
