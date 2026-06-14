import sys
import os
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent_brain import _clean_reply

# Force stdout to use utf-8
sys.stdout.reconfigure(encoding='utf-8')

def test():
    text = """平稳随机过程是随机信号分析中最基础也最重要的概念之一。我们先从数学定义出发，再谈物理含义，最后指出常见误区。

**1. 数学定义**
平稳随机过程分为严平稳和宽平稳（WSS）两类。
- **严平稳**：随机过程 $X(t)$ 的任意有限维分布函数与时间起点无关。即对于任意 $n$、任意 $t_1,\\dots,t_n$ 和任意时间偏移 $\\tau$，联合分布函数满足：
  $$F_{X(t_1),\\dots,X(t_n)}(x_1,\\dots,x_n) = F_{X(t_1+\\tau),\\dots,X(t_n+\\tau)}(x_1,\\dots,x_n)$$
- **宽平稳（WSS）**：工程中更常用，只需满足两个条件：
  - 均值是常数：$m_X(t) = E[X(t)] = m_X$（与 $t$ 无关）"""

    print("=== Original text ===")
    print(text)
    
    print("\n=== Cleaned text ===")
    cleaned = _clean_reply(text)
    print(cleaned)
    
    if text.strip() == cleaned.strip():
        print("\nSUCCESS: No change detected!")
    else:
        print("\nWARNING: Text was modified!")
        # Print differences line by line
        orig_lines = text.strip().split('\n')
        clean_lines = cleaned.strip().split('\n')
        for i, (ol, cl) in enumerate(zip(orig_lines, clean_lines)):
            if ol != cl:
                print(f"Diff at line {i+1}:")
                print(f"  ORIG : {repr(ol)}")
                print(f"  CLEAN: {repr(cl)}")

if __name__ == "__main__":
    test()
