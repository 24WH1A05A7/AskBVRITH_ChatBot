import pathlib, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
F = '\ufffd'

for fpath in ['governance_dashboard.py', 'pages/governance.py']:
    text = pathlib.Path(fpath).read_text(encoding='utf-8')
    for i, line in enumerate(text.splitlines(), 1):
        if F in line and not line.lstrip().startswith('#'):
            cps = [hex(ord(c)) for c in line if ord(c) > 127]
            print(f'{fpath} L{i}: {cps[:20]}')
            print(f'  text: {line[:80]}')
