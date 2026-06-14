# core/agent_brain.py
import os
import re
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger("signal_agent")

_RE_THINKING = re.compile(
    r'(?:好的[，,]?\s*)?(?:现在\s*)?(?:让我们?|我来|咱们)\s*(?:再|先)?\s*(?:查|查看|调|搜|找|看|调用|了解)\s*一下[^。！？\n]*[。！？]?')
_RE_XML_TAGS = re.compile(
    r"<\s*[!/]?\s*(function_calls|function_call|invoke|parameter)[^>]*>.*?<\s*/\s*(function_calls|function_call|invoke)\s*>|<\s*(function_calls|function_call|invoke|parameter)[^>]*/?>",
    flags=re.DOTALL)
_RE_INVISIBLE = re.compile(r"[​-‍﻿­‎‏]")
_RE_EMOJI = re.compile(
    r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0000FE00-\U0000FE0F\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002300-\U000023FF\U00002B50\U00002764\U00002714\U00002705\U0000200D\U000020E3\U0001F004\U0001F0CF]",
    flags=re.UNICODE)
_RE_EMPTY_XML = re.compile(r'^\s*(<[^>]*>)?\s*$')
_RE_NODE = re.compile(r"\[NODE:\s*(\w+)\]")


def _load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    load_dotenv(env_path)


def _get_knowledge_node(node_id):
    from data.signal_knowledge_base import RANDOM_SIGNAL_KB
    node = RANDOM_SIGNAL_KB["knowledge_nodes"].get(node_id)
    if not node:
        return json.dumps({"error": f"未找到节点 {node_id}"}, ens
<truncated 4013 bytes>
f_feats.get("std"),
                "rms": f_feats.get("rms")
            }
        })
        
    if signal_context.get("kalman_run"):
        result.update({
            "kalman_run": True,
            "kalman_q": signal_context.get("kalman_q"),
            "kalman_r": signal_context.get("kalman_r"),
            "kalman_v0": signal_context.get("kalman_v0"),
            "kalman_p_final": signal_context.get("kalman_p_final"),
            "kalman_k1_final": signal_context.get("kalman_k1_final"),
            "kalman_k2_final": signal_context.get("kalman_k2_final")
        })
        
    return json.dumps(result, ensure_ascii=False)


_TOOL_DISPATCH = {
    "get_knowledge_node": lambda args, ctx: _get_knowledge_node(args.get("node_id", "")),
    "get_glossary": lambda args, ctx: _get_glossary(args.get("term", "")),
    "get_problem_case": lambda args, ctx: _get_problem_case(args.get("case_id", "")),
    "get_error_warning": lambda args, ctx: _get_error_warning(args.get("err_id", "")),
    "get_current_signal": lambda args, ctx: _get_current_signal(ctx),
}


def _clean_reply(text):
    if not text: return ""
    text = _RE_XML_TAGS.sub("", text)
    text = _RE_THINKING.sub("", text)
    text = _RE_INVISIBLE.sub("", text)
    text = _RE_EMOJI.sub("", text)
    return text.strip()


TOOLS = [
    {"type": "function", "function": {"name": "get_knowledge_node",
                                      "description": "获取指定知识节点的核心概念等。解释概念时务必调用此工具确保准确。",
                                      "parameters": {"type": "object", "properties": {"node_id": {"type": "string"}},
                                                     "required": ["node_id"]}}},
    {"type": "function", "function": {"name": "get_glossary", "description": "查询术语符号表的定义。",
                                      "parameters": {"type": "object", "properties": {"term": {"type": "string"}},
                                                     "required": ["term"]}}},
    {"type": "function", "function": {"name": "get_problem_case", "description": "获取例题/题型卡片。",
                                      "parameters": {"type": "object", "properties": {"case_id": {"type": "string"}},
                                                     "required": ["case_id"]}}},
    {"type": "function", "function": {"name": "get_error_warning", "description": "获取常见误区。",
                                      "parameters": {"type": "object", "properties": {"err_id": {"type": "string"}},
                                                     "required": ["err_id"]}}},
    {"type": "function", "function": {"name": "get_current_signal", "description": "获取当前已生成信号的参数和特征。",
                                      "parameters": {"type": "object", "properties": {}, "required": []}}}
]


def _build_system_prompt(signal_context, knowledge_context=None, require_json=False):
    from data.signal_knowledge_base import RANDOM_SIGNAL_KB
    kb = RANDOM_SIGNAL_KB
    nodes = kb["knowledge_nodes"]
    node_brief = "、".join(f"{
<truncated 8622 bytes>
 generate_signal 说明：当且仅当用户请求/指示生成某种信号时，填入该对象。此时 suggested_page 务必设为 'signal-lab'。\n"
            "※ run_toolbox 说明：当用户请求在工具箱运行滑动平均滤波、RC一阶低通滤波、维纳最优滤波或卡尔曼滤波仿真，或者你在解答中决定展示某种实验时，填入此对象，并将参数传回前端，前端会自动配置参数并立即执行。此时 suggested_page 务必设为 'toolbox'。如果不涉及工具箱运行，则填 null。\n"
            "【重要】如果用户的指令比较模糊（缺少部分或全部参数），必须按如下经典值直接填入（绝对不要向用户追问参数）：\n"
            "- 'generate_signal':\n"
            "  * '正弦+白噪声': freq=200.0, fs=10000, snr_db=10.0\n"
            "  * '方波+白噪声': freq=200.0, fs=10000, snr_db=10.0\n"
            "  * '窄带': freq=200.0, fs=10000, snr_db=10.0, bandwidth=50.0\n"
            "  * '瑞利分布': freq=200.0, fs=10000, snr_db=10.0, bandwidth=50.0\n"
            "  * '线性调频(LFM)': freq=100.0, freq_end=400.0, fs=10000, snr_db=10.0\n"
            "  * '高斯白噪声': fs=10000, snr_db=10.0\n"
            "  * '一阶马尔可夫过程': markov_a=0.9, fs=10000, snr_db=10.0\n"
            "  * '三角波+白噪声': freq=200.0, fs=10000, snr_db=10.0\n"
            "  * '双频正弦+白噪声': freq=200.0, freq2=300.0, fs=10000, snr_db=10.0\n"
            "  * 若只说'生成信号'但无指明类型，默认按 '正弦+白噪声' 经典值。\n"
            "- 'run_toolbox':\n"
            "  * 'moving_average': window_size=10\n"
            "  * 'rc_lowpass': cutoff_freq=500.0\n"
            "  * 'wiener': params留空/无\n"
            "  * 'kalman': q=0.1, r=1.0, v0=1.0\n"
            "如果用户不需要生成信号/运行工具，对应的字段必须返回 null。"
        )

    return prompt


class SignalAgent:
    def __init__(self):
        _load_dotenv()
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key or api_key == "your_deepseek_api_key_here":
            raise ValueError("请在 .env 文件中设置有效的 DEEPSEEK_API_KEY")
        
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        
        timeout_val = os.getenv("DEEPSEEK_TIMEOUT", "60.0")
        try:
            timeout = float(timeout_val)
        except ValueError:
            timeout = 60.0
            
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )

    def get_smart_follow_ups(self, node_title, core_concept, engineering_meaning="", count=3):
        """
        根据知识点生成智能追问问题列表。
        调用 DeepSeek API 生成与知识点相关的追问。
        如果 API 不可用则返回 None，由调用方回退到默认问题。
        """
        prompt = (
            f"你是一个《随机信号分析》课程的 AI 助教 Clar。\n"
            f"当前讨论的知识点：{node_title}\
<truncated 4249 bytes>
quire_json=False):
        system_prompt = _build_system_prompt(signal_context, knowledge_context, require_json)
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]
        kwargs = {"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": 4096}
        if require_json: kwargs["response_format"] = {"type": "json_object"}

        try:
            client_to_use = self.client.client if hasattr(self.client, 'client') else self.client
            stream_response = client_to_use.chat.completions.create(tools=TOOLS, stream=True, **kwargs)
            
            has_tool_calls = False
            tool_calls_dict = {}
            assistant_content = ""
            
            for chunk in stream_response:
                choices = chunk.choices
                if not choices:
                    continue
                delta = choices[0].delta
                if not delta:
                    continue
                
                # Collect tool calls if any
                if delta.tool_calls:
                    has_tool_calls = True
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_dict:
                            tool_calls_dict[idx] = {
                                "id": "",
                                "name": "",
                                "arguments": ""
                            }
                        if tc.id:
                            tool_calls_dict[idx]["id"] += tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls_dict[idx]["name"] += tc.function.name
                            if tc.function.arguments:
                                tool_calls_dict[idx]["arguments"] += tc.function.arguments
                
                # Collect and yield normal content
                if delta.content:
                    if not has_tool_calls:
                        yield delta.content
                    else:
                        assistant_content += delta.content

            if has_tool_calls:
                formatted_tool_calls = []
                for idx in sorted(tool_calls_dict.keys()):
                    tc = tool_calls_dict[idx]
                    formatted_tool_calls.append({
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["arguments"]
                        }
                    })
                
                clean_content = _clean_reply(assistant_content)
                if _RE_EMPTY_XML.match(clean_content):
                    clean_content = ""
                
                messages.append({
                    "role": "assistant",
                    "content": clean_content,
                    "tool_calls": formatted_tool_calls
                })
                
                for tc in formatted_tool_calls:
                    try:
                        fn_args = json.loads(tc["function"]["arguments"]) if tc["function"]["arguments"] else {}
                    except json.JSONDecodeError:
                        fn_args = {}
                    result = self._execute_tool(tc["function"]["name"], fn_args, signal_context)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result
                    })
                
                # Second turn: stream response
                kwargs["messages"] = messages
                if not require_json:
                    kwargs.pop("response_format", None)
                
                stream_response2 = client_to_use.chat.completions.create(stream=True, **kwargs)
                for chunk in stream_response2:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content
                        
        except Exception as e:
            logger.exception("AI 服务流式调用失败")
            yield f"抱歉，AI 服务暂时不可用：{e}"