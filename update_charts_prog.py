import re

with open('frontend/js/charts.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the ensemble loop in time plot
time_old = '''            const ensembles = S.ensembleData.ensembles_noisy;
            ensembles.forEach((ens, idx) => {
                traces.push({'''

time_new = '''            const ensembles = S.ensembleData.ensembles_noisy;
            const renderCount = S.ensembleRenderCount || ensembles.length;
            for(let idx=0; idx<renderCount; idx++) {
                const ens = ensembles[idx];
                traces.push({'''

content = content.replace(time_old, time_new)
content = content.replace('});\n            traces.push({', '}\n            traces.push({')

# Replace the PDF rendering
pdf_old = '''                {
                    x: S.ensembleData.pdf_x_ensemble,
                    y: S.ensembleData.pdf_y_ensemble,
                    type: 'bar',
                    name: '系综 PDF',
                    marker: { color: 'rgba(231, 76, 60, 0.6)', line: { color: 'rgba(231, 76, 60, 1.0)', width: 1 } }
                }'''

pdf_new = '''                (function(){
                    const renderCount = S.ensembleRenderCount || S.ensembleData.ensembles_noisy.length;
                    let all_pts = [];
                    for(let i=0; i<renderCount; i++) {
                        all_pts = all_pts.concat(S.ensembleData.ensembles_noisy[i]);
                    }
                    // Simple histogram
                    let min = Math.min(...all_pts);
                    let max = Math.max(...all_pts);
                    if(min === max) { min -= 1; max += 1; }
                    let bins = 100;
                    let binWidth = (max - min) / bins;
                    let counts = new Array(bins).fill(0);
                    for(let val of all_pts) {
                        let b = Math.floor((val - min) / binWidth);
                        if(b >= bins) b = bins - 1;
                        counts[b]++;
                    }
                    // Normalize to density
                    let area = all_pts.length * binWidth;
                    let density = counts.map(c => c / area);
                    let binCenters = counts.map((_, i) => min + (i + 0.5) * binWidth);
                    
                    return {
                        x: binCenters,
                        y: density,
                        type: 'bar',
                        name: 系综 PDF (N=),
                        marker: { color: 'rgba(231, 76, 60, 0.6)', line: { color: 'rgba(231, 76, 60, 1.0)', width: 1 } }
                    };
                })()'''

content = content.replace(pdf_old, pdf_new)

with open('frontend/js/charts.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated charts.js for progressive rendering")
