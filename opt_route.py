import re

with open('backend/signal_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to replace the analyze_features call in api_ensemble_signal
old_block = '''        # Calculate features on the concatenated long array for better PDF approximation
        feats = analyze_features(
            np.array(all_noisy_concat), params.fs, np.array(all_noisy_concat), # Just need PDF
            signal_type=params.signal_type, freq=params.freq, duration=params.duration * params.ensemble_n,
            freq2=params.freq2, freq_end=params.freq_end
        )'''

new_block = '''        # Ultra-fast O(N) PDF calculation using np.histogram on the entire ensemble
        import numpy as np
        all_noisy = np.array(all_noisy_concat)
        counts, bins = np.histogram(all_noisy, bins=100, density=True)
        pdf_y = counts
        pdf_x = (bins[:-1] + bins[1:]) / 2'''

content = content.replace(old_block, new_block)
content = content.replace('"pdf_x_ensemble": feats["pdf_x"].tolist(),', '"pdf_x_ensemble": pdf_x.tolist(),')
content = content.replace('"pdf_y_ensemble": feats["pdf_y"].tolist(),', '"pdf_y_ensemble": pdf_y.tolist(),')

with open('backend/signal_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated signal_routes.py")
