import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

class JSONReplyStreamParserOld:
    def __init__(self):
        self.buffer = ""
        self.reply_started = True
        self.reply_finished = False
        self.escaped = False

    def feed(self, chunk: str):
        self.buffer += chunk
        i = 0
        n = len(self.buffer)
        while i < n:
            char = self.buffer[i]
            if self.escaped:
                if char == 'u':
                    # Simplified for test
                    yield '\\u'
                    i += 1
                elif char == 'n': yield '\n'
                elif char == 't': yield '\t'
                elif char == 'r': yield '\r'
                elif char == 'b': yield '\b'
                elif char == 'f': yield '\f'
                else: yield char
                self.escaped = False
                i += 1
            elif char == '\\':
                self.escaped = True
                i += 1
            else:
                yield char
                i += 1
        self.buffer = self.buffer[i:]

class JSONReplyStreamParserNew:
    def __init__(self):
        self.buffer = ""
        self.reply_started = True
        self.reply_finished = False
        self.escaped = False

    def feed(self, chunk: str):
        self.buffer += chunk
        i = 0
        n = len(self.buffer)
        while i < n:
            char = self.buffer[i]
            if self.escaped:
                if char == 'u':
                    yield '\\u'
                    i += 1
                elif char == 'n': yield '\n'
                elif char == 't': yield '\t'
                elif char == 'r': yield '\r'
                elif char == 'b': yield '\b'
                elif char == 'f': yield '\f'
                elif char in ('"', '\\', '/'):
                    yield char
                else:
                    yield '\\'
                    yield char
                self.escaped = False
                i += 1
            elif char == '\\':
                self.escaped = True
                i += 1
            else:
                yield char
                i += 1
        self.buffer = self.buffer[i:]

test_input = r"This is a formula: \dots \tau and escaped \\dots \\tau."
print("Input:", repr(test_input))

old_parser = JSONReplyStreamParserOld()
old_output = "".join(old_parser.feed(test_input))
print("Old Parser Output:", repr(old_output))

new_parser = JSONReplyStreamParserNew()
new_output = "".join(new_parser.feed(test_input))
print("New Parser Output:", repr(new_output))
