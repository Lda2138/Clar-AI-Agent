import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

_RE_THINKING = re.compile(
    r'(?:好的[，,]?\s*)?(?:现在\s*)?(?:让我们?|我来|咱们)\s*(?:再|先)?\s*(?:查|查看|调|搜|找|看|调用|了解)\s*一下[^。！？\n]*[。！？]?'
)

text = """我来了解一下平稳随机过程的定义，其n维分布函数满足 F_
{X(t_1), X(t_2), \\dots, X(t_n)}(x_1, x_2, \\dots, x_n) = F_{X(t_1+\\tau), X(t_2+\\tau), \\dots, X(t_n+\\tau)}(x_1, x_2, \\dots, x_n)$$

但在工程中，我们几乎只使用广义平稳 (WSS)，它只要求两个条件：
1. 均值是常数：m_X(t) = E[X(t)] = 常数（与t无关）。"""

print("Original:")
print(text)
print("\nAfter _RE_THINKING:")
print(_RE_THINKING.sub("", text))
