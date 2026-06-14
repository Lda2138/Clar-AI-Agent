import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent_brain import SignalAgent

def test_streaming():
    print("Initializing SignalAgent...")
    try:
        agent = SignalAgent()
    except ValueError as e:
        print(f"Skipping integration test because API key is missing: {e}")
        return
        
    print("Testing regular message streaming (should immediately yield tokens)...")
    stream = agent.chat_stream("你好, 请问你是谁？", require_json=True)
    chunks = []
    first_token_received = False
    for chunk in stream:
        if not first_token_received:
            print("First token received!")
            first_token_received = True
        chunks.append(chunk)
        sys.stdout.write(chunk)
        sys.stdout.flush()
    print("\nTotal chunks received:", len(chunks))
    assert len(chunks) > 0, "No chunks received!"
    
    print("\nTesting tool call integration (should collect tool call internally and output final JSON)...")
    # This prompt is highly likely to trigger get_knowledge_node or other tools
    stream_tool = agent.chat_stream("我想查看关于“平稳”知识点的信息。", require_json=True)
    tool_chunks = []
    for chunk in stream_tool:
        tool_chunks.append(chunk)
        sys.stdout.write(chunk)
        sys.stdout.flush()
    print("\nTotal tool chunks received:", len(tool_chunks))
    assert len(tool_chunks) > 0, "No chunks received for tool call!"
    
    print("\nAll integration tests PASSED successfully!")

if __name__ == "__main__":
    test_streaming()
