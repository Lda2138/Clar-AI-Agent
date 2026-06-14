# core/agent_brain.py
import os
import re
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv

from core.prompts import _build_system_prompt
from core.tools import TOOLS, _execute_tool

logger = logging.getLogger("signal_agent")

_RE_THINKING = re.compile(
    r'(?:好的[，,]?\s*)?(?:现在\s*)?(?:让我们?|我来|咱们)\s*(?:再|先)?\s*(?:调用(?:工具|函数|api)|查|查看|调|搜|找|看|了解)\s*一下')
_RE_XML_TAGS = re.compile(
    r"<\s*[!/]?\s*(function_calls|function_call|invoke|parameter)[^>]*>.*?<\s*/\s*(function_calls|function_call|invoke)\s*>|<\s*(function_calls|function_call|invoke|parameter)[^>]*/?>",
    flags=re.DOTALL)
_RE_INVISIBLE = re.compile(r"[​-‍﻿­‎‏]")
_RE_EMOJI = re.compile(
    r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0000FE00-\U0000FE0F\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002300-\U000023FF\U00002B50\U00002764\U00002714\U00002705\U0000200D\U000020E3\U0001F004\U0001F0CF]",
    flags=re.UNICODE)
_RE_EMPTY_XML = re.compile(r'^\s*(<[^>]*>)?\s*$')
_RE_NODE = re.compile(r"\[NODE:\s*(\w+)\]")
_RE_STATUS = re.compile(r'(?:🔍|📊|📝|⚠️|📖)\s*正在[^\n]*\n*')


def _load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    load_dotenv(env_path)


def _clean_reply(text):
    if not text: return ""
    text = _RE_XML_TAGS.sub("", text)
    text = _RE_THINKING.sub("", text)
    text = _RE_INVISIBLE.sub("", text)
    text = _RE_STATUS.sub("", text)
    text = _RE_EMOJI.sub("", text)
    text = re.sub(r'<\s*[|｜]?\s*[|｜]?\s*DSML[\s\S]*?<\s*/\s*[|｜]?\s*[|｜]?\s*DSML[^>]*tool_calls\s*>', "", text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*[|｜]?\s*[|｜]?\s*DSML[^>]*>', "", text, flags=re.IGNORECASE)
    return text.strip()


class SignalAgent:
    def __init__(self):
        _load_dotenv()
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key or api_key == "your_deepseek_api_key_here":
            raise ValueError("请在 .env 文件中设置有效的 DEEPSEEK_API_KEY")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.client = OpenAI(api_key=api_key, base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))

    def get_smart_follow_ups(self, node_title, core_concept, engineering_meaning="", count=3):
        """
        根据知识点生成智能追问问题列表。
        """
        prompt = (
            f"你是一个《随机信号分析》课程的 AI 助教 Clar。\n"
            f"当前讨论的知识点：{node_title}\n"
            f"核心概念：{core_concept}\n"
            f"工程意义：{engineering_meaning or '暂无'}\n\n"
            f"请生成 {count} 个能够引导学生深入思考该知识点的追问问题，"
            f"问题应当具有启发性和工程关联性。\n"
            f"请严格按照 JSON 格式返回：{{\"questions\": [\"问题1\", \"问题2\", ...]}}"
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=512,
                response_format={"type": "json_object"},
                timeout=120,
            )
            raw = response.choices[0].message.content
            data = json.loads(raw) if raw else {}
            questions = data.get("questions", [])
            if questions and len(questions) >= 1:
                return questions
            return None
        except Exception:
            logger.exception("智能追问生成失败")
            return None

    def chat(self, user_message, signal_context=None, knowledge_context=None, history=None, temperature=0.5, require_json=False):
        system_prompt = _build_system_prompt(signal_context, knowledge_context, require_json)
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for h in history:
                if isinstance(h, dict) and "role" in h and "content" in h:
                    content = _clean_reply(h["content"]) if h["role"] == "assistant" else h["content"]
                    if require_json and h["role"] == "assistant":
                        try:
                            json.loads(content)
                        except Exception:
                            content = json.dumps({"reply": content}, ensure_ascii=False)
                    messages.append({"role": h["role"], "content": content})
        messages.append({"role": "user", "content": user_message})
        kwargs = {"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": 4096}
        if require_json:
            kwargs["response_format"] = {"type": "json_object"}


        try:
            response = self.client.chat.completions.create(tools=TOOLS, timeout=120, **kwargs)
            msg = response.choices[0].message
            if msg.tool_calls:
                clean_content = _clean_reply(msg.content or "")
                if _RE_EMPTY_XML.match(clean_content): clean_content = ""
                messages.append({"role": "assistant", "content": clean_content, "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in
                    msg.tool_calls]})
                for tc in msg.tool_calls:
                    try:
                        fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    except json.JSONDecodeError:
                        fn_args = {}
                    result = _execute_tool(tc.function.name, fn_args, signal_context)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

                kwargs["messages"] = messages

                response2 = self.client.chat.completions.create(timeout=120, **kwargs)
                reply = response2.choices[0].message.content
            else:
                reply = msg.content
        except Exception as e:
            logger.exception("AI 服务调用失败")
            reply = f"抱歉，AI 服务暂时不可用：{e}"

        reply = _clean_reply(reply or "抱歉，我暂时无法回答这个问题。")

        node_id = None
        match = _RE_NODE.search(reply)
        if match:
            node_id = match.group(1)
            reply = _RE_NODE.sub("", reply).strip()

        return reply, node_id

    def chat_stream(self, user_message, signal_context=None, knowledge_context=None, history=None, temperature=0.5, require_json=False):
        system_prompt = _build_system_prompt(signal_context, knowledge_context, require_json)
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for h in history:
                if isinstance(h, dict) and "role" in h and "content" in h:
                    content = _clean_reply(h["content"]) if h["role"] == "assistant" else h["content"]
                    if require_json and h["role"] == "assistant":
                        try:
                            json.loads(content)
                        except Exception:
                            content = json.dumps({"reply": content}, ensure_ascii=False)
                    messages.append({"role": h["role"], "content": content})
        messages.append({"role": "user", "content": user_message})
        kwargs = {"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": 4096}
        if require_json:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            client_to_use = self.client.client if hasattr(self.client, 'client') else self.client
            # Single pass API call, no tools parameter anymore!
            stream_response = client_to_use.chat.completions.create(stream=True, timeout=120, **kwargs)
            
            for chunk in stream_response:
                choices = chunk.choices
                if not choices:
                    continue
                delta = choices[0].delta
                if not delta:
                    continue
                
                if delta.content:
                    yield delta.content
                        
        except Exception as e:
            logger.exception("AI 服务流式调用失败")
            yield f"抱歉，AI 服务暂时不可用：{e}"