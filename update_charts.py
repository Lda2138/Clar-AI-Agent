import re

with open('frontend/js/charts.js', 'r', encoding='utf-8') as f:
    content = f.read()

waveform_replacement = '''
        if (S.ensembleData) {
            // Plot ensemble traces
            const ensembles = S.ensembleData.ensembles_noisy;
            ensembles.forEach((ens, idx) => {
                traces.push({
                    y: ens,
                    x: S.ensembleData.t,
                    name: idx === 0 ? '系综实现' : '',
                    showlegend: idx === 0,
                    line: { width: 1, color: 'rgba(231, 76, 60, 0.15)' },
                    hoverinfo: 'skip'
                });
            });
            traces.push({
                y: data.clean_fine || data.clean, 
                x: data.t_fine || data.t, 
                name: '纯净信号 s(t)', 
                line: { width: 2.5, color: '#4285f4' } 
            });
        } else {
            traces = [
                { 
                    y: data.clean_fine || data.clean, 
                    x: data.t_fine || data.t, 
                    name: '纯净信号 s(t)', 
                    line: { width: 1.5, color: '#4285f4' } 
                },
                { 
                    y: data.noisy_fine || data.noisy, 
                    x: data.t_fine || data.t, 
                    name: '含噪信号 x(t)', 
                    line: { width: 1, color: '#e74c3c' } 
                }
            ];
        }
'''

content = re.sub(
    r'traces = \[\s*\{\s*y: data\.clean_fine \|\| data\.clean,\s*x: data\.t_fine \|\| data\.t,.*?(?=\} else if \(timeAnalysis === \'autocorr\'\))',
    waveform_replacement,
    content,
    flags=re.DOTALL
)

pdf_replacement = '''
        if (S.ensembleData) {
            if (cardTitleEl) cardTitleEl.innerText = 系综概率密度 (Ensemble PDF);
            traces = [
                {
                    x: S.ensembleData.pdf_x_ensemble,
                    y: S.ensembleData.pdf_y_ensemble,
                    type: 'bar',
                    name: '系综 PDF',
                    marker: { color: 'rgba(231, 76, 60, 0.6)', line: { color: 'rgba(231, 76, 60, 1.0)', width: 1 } }
                }
            ];
        } else {
            traces = [
                {
                    x: data.pdf_x,
                    y: data.pdf_y,
                    type: 'bar',
                    name: '观测序列 PDF',
                    marker: { color: 'rgba(231, 76, 60, 0.6)', line: { color: 'rgba(231, 76, 60, 1.0)', width: 1 } }
                }
            ];
        }
        if (data.pdf_x_clean && data.pdf_x_clean.length > 0) {
'''

content = re.sub(
    r'traces = \[\s*\{\s*x: data\.pdf_x,\s*y: data\.pdf_y,\s*type: \'bar\',\s*name: \'观测序列 PDF\',\s*marker: \{ color: \'rgba\(231, 76, 60, 0\.6\)\', line: \{ color: \'rgba\(231, 76, 60, 1\.0\)\', width: 1 \} \}\s*\}\s*\];\s*if \(data\.pdf_x_clean && data\.pdf_x_clean\.length > 0\) \{',
    pdf_replacement,
    content,
    flags=re.DOTALL
)


with open('frontend/js/charts.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated charts.js")
