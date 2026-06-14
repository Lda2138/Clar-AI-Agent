import re

with open('backend/signal_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace imports
content = content.replace('SignalParams, FilterParams, KalmanParams', 'SignalParams, FilterParams, KalmanParams, EnsembleParams')

ensemble_route = '''
@router.post("/api/signal/ensemble")
def api_ensemble_signal(params: EnsembleParams):
    if params.signal_type not in _SIGNAL_GENERATORS:
        raise HTTPException(status_code=400, detail=f"未知信号类型: {params.signal_type}")
    try:
        ensembles_noisy = []
        ensembles_clean = []
        all_noisy_concat = []
        
        # We need to compute an average PSD and a large combined PDF
        for i in range(params.ensemble_n):
            seed = (params.freq * params.fs) + i * 1000  # just a pseudo-random seed that changes with i
            t, clean, noisy = generate_signal(
                params.signal_type, params.freq, params.fs, params.snr_db, params.duration,
                bandwidth=params.bandwidth, freq_end=params.freq_end,
                markov_a=params.markov_a, freq2=params.freq2, seed=int(seed)
            )
            ensembles_noisy.append(_downsample(noisy))
            ensembles_clean.append(_downsample(clean))
            all_noisy_concat.extend(noisy)
            
        # Calculate features on the concatenated long array for better PDF approximation
        feats = analyze_features(
            np.array(all_noisy_concat), params.fs, np.array(all_noisy_concat), # Just need PDF
            signal_type=params.signal_type, freq=params.freq, duration=params.duration * params.ensemble_n,
            freq2=params.freq2, freq_end=params.freq_end
        )

        return {
            "t": _downsample(t),
            "ensembles_noisy": ensembles_noisy,
            "ensembles_clean": ensembles_clean,
            "pdf_x_ensemble": feats["pdf_x"].tolist(),
            "pdf_y_ensemble": feats["pdf_y"].tolist(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"系综信号生成失败: {e}")
'''

# Insert the ensemble route
content = content + '\n' + ensemble_route

with open('backend/signal_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added ensemble route")
