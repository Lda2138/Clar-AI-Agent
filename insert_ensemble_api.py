import re

with open('frontend/js/api_service.js', 'r', encoding='utf-8') as f:
    content = f.read()

ensemble_method = '''
    async generateEnsemble(params, ensembleN = 15) {
        const payload = { ...params, ensemble_n: ensembleN };
        return await this._request('/api/signal/ensemble', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }
'''

content = content.replace('async generateSignal(params) {', ensemble_method + '\n    async generateSignal(params) {')

with open('frontend/js/api_service.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added generateEnsemble to api_service.js")
