import os

# Update chat.js
with open('frontend/js/chat.js', 'r', encoding='utf-8') as f:
    chat_content = f.read()

chat_content = chat_content.replace(
    "fetch(API_BASE + '/api/log', {",
    "Api.sendLog(message, 'chat', e);"
)
chat_content = chat_content.replace(
    "method: 'POST',",
    ""
).replace(
    "headers: API_HEADERS,",
    ""
).replace(
    "body: JSON.stringify({ message: String(message), source: 'chat', error: e ? String(e) : null })",
    ""
).replace(
    "}); // Best effort log",
    ""
)

chat_content = chat_content.replace(
    "const resp = await fetch(API_BASE + '/api/chat', { \n            method: 'POST', \n            headers: API_HEADERS,\n            body: JSON.stringify(payload)\n        });",
    "const resp = await Api._request('/api/chat', { method: 'POST', body: JSON.stringify(payload) });"
)
chat_content = chat_content.replace(
    "const resp = await fetch(API_BASE + '/api/chat/proactive', {\n            method: 'POST',\n            headers: API_HEADERS,\n            body: JSON.stringify(payload)\n        });",
    "const resp = await Api._request('/api/chat/proactive', { method: 'POST', body: JSON.stringify(payload) });"
)

with open('frontend/js/chat.js', 'w', encoding='utf-8') as f:
    f.write(chat_content)


# Update telemetry.js
with open('frontend/js/telemetry.js', 'r', encoding='utf-8') as f:
    telemetry_content = f.read()

telemetry_content = telemetry_content.replace(
    "const res = await fetch('/api/telemetry', {\n                method: 'POST',\n                headers: {\n                    'Content-Type': 'application/json'\n                },\n                body: JSON.stringify(payload)\n            });",
    "const res = await Api._request('/api/telemetry', { method: 'POST', body: JSON.stringify(payload) });"
)

with open('frontend/js/telemetry.js', 'w', encoding='utf-8') as f:
    f.write(telemetry_content)

print("Chat and Telemetry decoupled.")
