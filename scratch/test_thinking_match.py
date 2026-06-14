import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

_RE_THINKING = re.compile(
    r'(?:好的[，,]?\s*)?(?:现在\s*)?(?:让我们?|我来|咱们)\s*(?:再|先)?\s*(?:查|查看|调|搜|找|看|调用|了解)\s*一下[^。！？\n]*[。！？]?'
)

text = "我来了解一下平稳随机过程的定义，其n维分布函数满足 F_{X(t_1), X(t_2)}(x_1, x_2) = F_{X(t_1+\\tau), X(t_2+\\tau)}(x_1, x_2)$$"

print("Original:")
print(text)
print("Modified:")
print(_RE_THINKING.sub("", text))
print("Match length:", len(_RE_THINKING.search(text).group(0)) if _RE_THINKING.search(text) else "No match")
