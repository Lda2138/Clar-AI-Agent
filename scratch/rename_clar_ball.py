# scratch/rename_clar_ball.py
import glob

files = glob.glob('frontend/**/*.js', recursive=True) + glob.glob('frontend/*.html')

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Let's count occurrences
    occurrences = content.lower().count('clar-all')
    if occurrences > 0:
        print(f"Found {occurrences} occurrences in {fpath}")
        
        # Replace occurrences
        # We need to preserve case
        # Case 1: Clar-all -> Clar-ball
        content = content.replace('Clar-all', 'Clar-ball')
        # Case 2: clar-all -> clar-ball (some class names are collapsed-clar-all -> collapsed-clar-ball)
        content = content.replace('clar-all', 'clar-ball')
        # Case 3: CLAR-ALL -> CLAR-BALL
        content = content.replace('CLAR-ALL', 'CLAR-BALL')
        
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {fpath}")
