import re

with open('frontend/js/ui.js', 'r', encoding='utf-8') as f:
    content = f.read()

ensemble_func = '''
async function generateEnsembleData() {
    try {
        const params = {
            signal_type: document.getElementById('sig-type').value,
            freq: parseFloat(document.getElementById('sig-freq').value) || 200,
            fs: parseInt(document.getElementById('sig-fs').value) || 10000,
            snr_db: parseFloat(document.getElementById('sig-snr').value) || 10,
            bandwidth: parseFloat(document.getElementById('sig-bandwidth').value) || 50,
            freq_end: parseFloat(document.getElementById('sig-freq-end').value) || 300,
            markov_a: parseFloat(document.getElementById('sig-markov-a').value) || 0.9,
            freq2: parseFloat(document.getElementById('sig-freq2').value) || 300,
        };
        const data = await api('/api/signal/ensemble', { method: 'POST', body: JSON.stringify({...params, ensemble_n: 15}) });
        if (data.error) { alert(data.error); return; }
        
        // We also need the base signalData so that FFT works fine.
        // If we don't have it, fetch it.
        if (!S.signalData || S.signalData.features.mean === undefined) {
             await generateSignal(false, false);
        }
        
        S.ensembleData = data;
        
        navigate('signal-lab');
        updatePlots(); 
    } catch (err) {
        console.error(err);
    }
}
'''

content = content.replace('async function applyFilter(type) {', ensemble_func + '\nasync function applyFilter(type) {')

with open('frontend/js/ui.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added generateEnsembleData to ui.js")
