import pathlib, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

FFFD = '\ufffd'

files = [
    'app.py', 'pages/chat.py', 'rag_engine.py', 'login.py',
    'governance_dashboard.py', 'evaluation_dashboard.py',
    'evaluation_suite.py', 'observability_dashboard.py',
    'pages/evaluation.py', 'pages/governance.py',
]

for fpath in files:
    text = pathlib.Path(fpath).read_text(encoding='utf-8')
    bad = []
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        if FFFD in line and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'\"\"\""):
            bad.append((i, line))
    if bad:
        print(f'\n=== {fpath} ({len(bad)} lines) ===')
        for i, line in bad:
            print(f'  L{i}: {line}')
