# backend/parser.py
import re
import json

class JSONReplyStreamParser:
    """
    Robust stream parser that extracts the contents of the "reply" key
    from a JSON stream, avoiding streaming raw JSON formatting characters.
    """
    def __init__(self):
        self.buffer = ""
        self.reply_started = False
        self.reply_finished = False
        self.escaped = False

    def feed(self, chunk: str):
        if self.reply_finished:
            return
            
        self.buffer += chunk
        
        if not self.reply_started:
            # Look for the start of the "reply", "回复", "text", "content", or "answer" value
            keys = ['reply', '回复', 'text', 'content', 'answer']
            for key in keys:
                match = re.search(rf'"{key}"\s*:\s*"', self.buffer)
                if not match:
                    match = re.search(rf"'{key}'\s*:\s*'", self.buffer)
                if match:
                    self.reply_started = True
                    self.buffer = self.buffer[match.end():]
                    break
            if not self.reply_started:
                # Do not yield anything until reply key is found
                return

        if self.reply_started:
            i = 0
            n = len(self.buffer)
            out_chars = []
            
            while i < n:
                char = self.buffer[i]
                if self.escaped:
                    if char == 'u':
                        if i + 4 < n:
                            hex_str = self.buffer[i+1:i+5]
                            try:
                                code = int(hex_str, 16)
                                out_chars.append(chr(code))
                                i += 5
                                self.escaped = False
                                continue
                            except ValueError:
                                out_chars.append('\\u')
                                i += 1
                                self.escaped = False
                                continue
                        else:
                            # Not enough hex characters yet, wait for next feed
                            break
                    elif char == 'n':
                        out_chars.append('\n')
                    elif char == 't':
                        out_chars.append('\t')
                    elif char == 'r':
                        out_chars.append('\r')
                    elif char == 'b':
                        out_chars.append('\b')
                    elif char == 'f':
                        out_chars.append('\f')
                    elif char in ('"', '\\', '/'):
                        out_chars.append(char)
                    else:
                        out_chars.append('\\')
                        out_chars.append(char)
                    self.escaped = False
                    i += 1
                elif char == '\\':
                    self.escaped = True
                    i += 1
                elif char == '"':
                    self.reply_finished = True
                    self.buffer = ""
                    break
                else:
                    out_chars.append(char)
                    i += 1
            
            # Slice buffer to keep remaining characters
            if i < n:
                self.buffer = self.buffer[i:]
            else:
                self.buffer = ""
                
            if out_chars:
                yield "".join(out_chars)


def fix_json_backslashes(text: str) -> str:
    # Match valid JSON escape sequences first (group 1), or match any backslash (group 2)
    # Valid escapes: \", \\, \/, \b, \f, \n, \r, \t, and \uXXXX
    pattern = re.compile(r'(\\["\\/bfnrt]|\\u[0-9a-fA-F]{4})|(\\)')
    
    def replace(match):
        if match.group(1):
            return match.group(1)
        else:
            return r'\\'

    return pattern.sub(replace, text)


def try_parse_json(text: str):
    try:
        data = json.loads(text, strict=False)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
        
    # Try fixing invalid backslashes (often LaTeX formulas)
    try:
        fixed_text = fix_json_backslashes(text)
        data = json.loads(fixed_text, strict=False)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    cleaned_text = re.sub(r'\\u[0-9a-fA-F]{0,3}$', '', text)
    cleaned_text = re.sub(r'\\$', '', cleaned_text)
    
    cleaned_text_fixed = fix_json_backslashes(cleaned_text)
    
    suffixes = [
        '" }',
        '"}',
        '"]}',
        '"] }',
        '"}}',
        '"} }',
        ' }',
        '}}'
    ]
    for suffix in suffixes:
        try:
            data = json.loads(cleaned_text_fixed + suffix, strict=False)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return None


def extract_reply_by_regex(text: str) -> str:
    cleaned = text.strip()
    match = re.search(r'"reply"\s*:\s*"(.*?)(?<!\\)"', cleaned, re.DOTALL)
    if match:
        reply_val = match.group(1)
        
        def replace_escape(m):
            seq = m.group(1)
            if seq == 'n': return '\n'
            if seq == 't': return '\t'
            if seq == 'r': return '\r'
            if seq == 'b': return '\b'
            if seq == 'f': return '\f'
            if seq in ('"', '\\', '/'): return seq
            if seq.startswith('u'):
                try:
                    return chr(int(seq[1:], 16))
                except ValueError:
                    return m.group(0)
            return m.group(0)
            
        return re.sub(r'\\(n|t|r|b|f|["\\/]|u[0-9a-fA-F]{4})', replace_escape, reply_val)
    return text


def extract_reply_robust(text: str) -> dict:
    clean_str = text.strip()
    match_json = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_str, re.DOTALL)
    if match_json:
        clean_str = match_json.group(1).strip()
    else:
        if clean_str.startswith("```json"):
            clean_str = clean_str[7:]
        elif clean_str.startswith("```"):
            clean_str = clean_str[3:]
        if clean_str.endswith("```"):
            clean_str = clean_str[:-3]
        clean_str = clean_str.strip()

    data = try_parse_json(clean_str)
    if not data:
        data = {}

    reply_text = data.get("reply")
    if not reply_text:
        reply_text = extract_reply_by_regex(text)

    node_id = data.get("node_id")
    if not node_id:
        node_match = re.search(r'"node_id"\s*:\s*"([^"]+)"', clean_str)
        if node_match:
            node_id = node_match.group(1)

    suggested_page = data.get("suggested_page", "none")
    sp_match = re.search(r'"suggested_page"\s*:\s*"([^"]+)"', clean_str)
    if sp_match:
        suggested_page = sp_match.group(1)

    if suggested_page.startswith("tool"):
        suggested_page = "toolbox"
    elif suggested_page.startswith("sign"):
        suggested_page = "signal-lab"
    elif suggested_page.startswith("know"):
        suggested_page = "knowledge-map"
    elif suggested_page not in ("toolbox", "signal-lab", "knowledge-map"):
        suggested_page = "none"

    generate_signal = data.get("generate_signal")
    if not generate_signal:
        gs_match = re.search(r'"generate_signal"\s*:\s*(\{.*?\})', clean_str, re.DOTALL)
        if gs_match:
            try:
                generate_signal = json.loads(gs_match.group(1), strict=False)
            except Exception:
                pass

    run_toolbox = data.get("run_toolbox")
    if not run_toolbox:
        rt_match = re.search(r'"run_toolbox"\s*:\s*(\{.*?\})', clean_str, re.DOTALL)
        if rt_match:
            try:
                run_toolbox = json.loads(rt_match.group(1), strict=False)
            except Exception:
                pass

    time_analysis_type = data.get("time_analysis_type")
    if not time_analysis_type:
        tat_match = re.search(r'"time_analysis_type"\s*:\s*"([^"]+)"', clean_str)
        if tat_match:
            time_analysis_type = tat_match.group(1)

    freq_analysis_type = data.get("freq_analysis_type")
    if not freq_analysis_type:
        fat_match = re.search(r'"freq_analysis_type"\s*:\s*"([^"]+)"', clean_str)
        if fat_match:
            freq_analysis_type = fat_match.group(1)

    new_card = data.get("new_card")
    if not new_card:
        nc_match = re.search(r'"new_card"\s*:\s*(\{.*?\})', clean_str, re.DOTALL)
        if nc_match:
            try:
                new_card = json.loads(nc_match.group(1), strict=False)
            except Exception:
                pass

    quick_questions = data.get("quick_questions", [])
    if not quick_questions:
        qq_match = re.search(r'"quick_questions"\s*:\s*(\[.*?\])', clean_str, re.DOTALL)
        if qq_match:
            try:
                quick_questions = json.loads(qq_match.group(1), strict=False)
            except Exception:
                pass

    return {
        "reply": reply_text,
        "node_id": node_id,
        "new_card": new_card,
        "quick_questions": quick_questions,
        "suggested_page": suggested_page,
        "generate_signal": generate_signal,
        "run_toolbox": run_toolbox,
        "time_analysis_type": time_analysis_type,
        "freq_analysis_type": freq_analysis_type
    }
