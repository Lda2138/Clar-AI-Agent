import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

_RE_THINKING = re.compile(
    r'(?:好的[，,]?\s*)?(?:现在\s*)?(?:让我们?|我来|咱们)\s*(?:再|先)?\s*(?:查|查看|调|搜|找|看|调用|了解)\s*一下[^。！？\n]*[。！？]?'
)

test_cases = [
    # Case 1: Simple thinking phrase
    "好的，现在让我们来了解一下平稳随机过程。对于严平稳过程，其n维分布函数满足 F_{X(t_1), X(t_2), \\dots, X(t_n)}(x_1, x_2, \\dots, x_n) = F_{X(t_1+\\tau), X(t_2+\\tau), \\dots, X(t_n+\\tau)}(x_1, x_2, \\dots, x_n)$$\n\n但在工程中",
    
    # Case 2: Thinking phrase where the math formula is on the SAME line without periods or newlines
    "好的，现在让我们来了解一下平稳随机过程的定义，其n维分布函数满足 F_{X(t_1)}(x_1) = F_{X(t_1+\\tau)}(x_1)$$ 但在工程中",
    
    # Case 3: A variation where there is a colon
    "好的，现在让我们来了解一下平稳随机过程：F_{X(t_1)}(x_1) = F_{X(t_1+\\tau)}(x_1)$$ 但在工程中"
]

for idx, tc in enumerate(test_cases):
    print(f"\n--- Case {idx+1} ---")
    print("Original:")
    print(tc)
    print("Modified:")
    print(_RE_THINKING.sub("", tc))
