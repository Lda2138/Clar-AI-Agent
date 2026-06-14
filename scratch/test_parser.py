import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.parser import JSONReplyStreamParser

def test_parser_normal():
    chunks = [
        '{"reply": ',
        '"Hello, this is standard text. ',
        'Have a good day!"',
        ', "quick_questions": ["q1"]}'
    ]
    parser = JSONReplyStreamParser()
    result = []
    for chunk in chunks:
        result.extend(parser.feed(chunk))
    assert "".join(result) == "Hello, this is standard text. Have a good day!"
    print("test_parser_normal: PASS")

def test_parser_escaped_newlines():
    chunks = [
        '{"reply": "Line 1\\n',
        'Line 2\\t',
        'Line 3"',
        '}'
    ]
    parser = JSONReplyStreamParser()
    result = []
    for chunk in chunks:
        result.extend(parser.feed(chunk))
    assert "".join(result) == "Line 1\nLine 2\tLine 3"
    print("test_parser_escaped_newlines: PASS")

def test_parser_unicode():
    chunks = [
        '{"reply": "\\u4f60\\u597d, ',
        'Clar!\\u2605"',
        '}'
    ]
    parser = JSONReplyStreamParser()
    result = []
    for chunk in chunks:
        result.extend(parser.feed(chunk))
    assert "".join(result) == "你好, Clar!★"
    print("test_parser_unicode: PASS")

def test_parser_split_escapes():
    # Split the backslash and the 'n' or 'u' across chunk boundaries
    chunks = [
        '{"reply": "Hello\\',
        'nWorld\\',
        'u4f',
        '60"',
        '}'
    ]
    parser = JSONReplyStreamParser()
    result = []
    for chunk in chunks:
        result.extend(parser.feed(chunk))
    assert "".join(result) == "Hello\nWorld你"
    print("test_parser_split_escapes: PASS")

def test_parser_latex_escapes():
    chunks = [
        '{"reply": "LaTeX formula: \\\\sin(\\\\theta) \\\\approx \\\\frac{x}{y}"',
        '}'
    ]
    parser = JSONReplyStreamParser()
    result = []
    for chunk in chunks:
        result.extend(parser.feed(chunk))
    # It should resolve double backslashes in JSON to a single backslash
    assert "".join(result) == "LaTeX formula: \\sin(\\theta) \\approx \\frac{x}{y}"
    print("test_parser_latex_escapes: PASS")

def test_thinking_ignored():
    chunks = [
        '<thinking>\nLet me think about how to answer this...\n</thinking>',
        '{\n  "reply": "This is the actual answer."',
        '}'
    ]
    parser = JSONReplyStreamParser()
    result = []
    for chunk in chunks:
        result.extend(parser.feed(chunk))
    assert "".join(result) == "This is the actual answer."
    print("test_thinking_ignored: PASS")

if __name__ == "__main__":
    test_parser_normal()
    test_parser_escaped_newlines()
    test_parser_unicode()
    test_parser_split_escapes()
    test_parser_latex_escapes()
    test_thinking_ignored()
    print("All parser unit tests PASSED successfully!")
