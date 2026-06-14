import re

_RE_THINKING = re.compile(
    r'(?:好的[，,]?\s*)?(?:现在\s*)?(?:让我们?|我来|咱们)\s*(?:再|先)?\s*(?:查|查看|调|搜|找|看|调用|了解)\s*一下[^。！？\n]*[。！？]?'
)

text = "好的，现在让我们来了解一下平稳随机过程。对于严平稳过程，其n维分布函数满足 F_{X(t_1), X(t_2), \\dots, X(t_n)}(x_1, x_2, \\dots, x_n) = F_{X(t_1+\\tau), X(t_2+\\tau), \\dots, X(t_n+\\tau)}(x_1, x_2, \\dots, x_n)$$\n\n但在工程中"

print("Original text:")
print(text)
print("\nAfter regex substitution:")
print(_RE_THINKING.sub("", text))
