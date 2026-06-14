import re

with open('frontend/js/ui.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the end of generateEnsembleData
old_logic = '''        S.ensembleData = data;
        
        navigate('signal-lab');
        updatePlots(); 
    } catch (err) {'''

new_logic = '''        S.ensembleData = data;
        navigate('signal-lab');
        
        // Start animation loop
        S.ensembleRenderCount = 1;
        updatePlots();
        
        if (window.ensembleTimer) clearInterval(window.ensembleTimer);
        window.ensembleTimer = setInterval(() => {
            if (S.ensembleRenderCount < data.ensembles_noisy.length) {
                S.ensembleRenderCount++;
                updatePlots();
            } else {
                clearInterval(window.ensembleTimer);
            }
        }, 150); // 150ms delay between each trace
        
    } catch (err) {'''

content = content.replace(old_logic, new_logic)

# Also clear ensembleTimer in generateSignal so it stops if user switches
clear_timer = '''          S.signalData = data; S.filteredData = null; S.ensembleData = null;
          if (window.ensembleTimer) clearInterval(window.ensembleTimer);'''

content = content.replace('S.signalData = data; S.filteredData = null; S.ensembleData = null;', clear_timer)

with open('frontend/js/ui.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated ui.js for animation")
