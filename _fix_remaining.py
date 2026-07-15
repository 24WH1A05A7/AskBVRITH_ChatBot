import pathlib, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

F = '\ufffd'
Q = '?'

fixes = {
    'app.py': [
        # 🧪 Evaluation nav title — pattern is F+Q+F+F (3 replacement chars)
        (f'title="{F+Q+F}{F} Evaluation"',    'title="🧪 Evaluation"'),
        # CSS comment separators (inside st.markdown string, cosmetic)
        # These lines are inside the triple-quoted CSS -- leave as-is if no match
    ],
    'rag_engine.py': [
        # Rupee sign ₹ -- U+20BF? No, Indian rupee is U+20B9
        # Pattern seen: F+Q+F  (3-byte UTF-8: E2 82 B9 -> double-encoded)
        (f'{F+Q+F}{{amount:,}}/year. Total 4-year: {F+Q+F}{{amount * 4:,}}',
         '₹{amount:,}/year. Total 4-year: ₹{amount * 4:,}'),
        # ⚠️ fallback  (F+Q+F+\ufe0f)
        (f'f"{F+Q+F}\ufe0f All AI models',    'f"⚠️ All AI models'),
        # Arrow comments in docstring (not critical, but fix anyway)
        (f'RAGEngine {F+Q+Q} the class',      'RAGEngine — the class'),
        (f'initialize()            {F+Q+Q} dict',  'initialize()            → dict'),
        (f'query_with_tools(       {F+Q+Q} dict',  'query_with_tools(       → dict'),
        (f'get_sections()        {F+Q+Q} list',     'get_sections()        → list'),
        (f'format_sources(docs) {F+Q+Q} str',       'format_sources(docs) → str'),
        (f'extract_images_from_docs(docs) {F+Q+Q} list', 'extract_images_from_docs(docs) → list'),
        (f'engine.llm.model                        {F+Q+Q} str',
         'engine.llm.model                        → str'),
        (f'engine.embeddings.model                 {F+Q+Q} str',
         'engine.embeddings.model                 → str'),
    ],
    'governance_dashboard.py': [
        (f'"<h1>{F+Q}{F+Q}\ufe0f Governance &amp;',
         '"<h1>🏛️ Governance &amp;'),
        (f'class="cat-pill">{F+Q+Q}{F+Q}\ufe0f 03 Safety',
         'class="cat-pill">🛡️ 03 Safety'),
        (f'delta=f"{F+Q}{F+Q}\ufe0f {{unacked_alerts}} open"',
         'delta=f"🚨 {unacked_alerts} open"'),
        (f'f"{F+Q}{F+Q}\ufe0f {{zero_chunk}} queries returned',
         'f"⚠️ {zero_chunk} queries returned'),
    ],
    'evaluation_dashboard.py': [
        # Weakest header — the em-dash after the name
        (f'Weakest: {{wd.code}} {{wd.name}} {F+Q+Q} {{wd.passed}}',
         'Weakest: {wd.code} {wd.name} — {wd.passed}'),
    ],
    'pages/evaluation.py': [
        (f'Weakest: {{wd.code}} {{wd.name}} {F+Q+Q} {{wd.passed}}',
         'Weakest: {wd.code} {wd.name} — {wd.passed}'),
    ],
    'pages/governance.py': [
        (f'class="cat-pill">{F+Q+Q}{F+Q}\ufe0f 03 Safety',
         'class="cat-pill">🛡️ 03 Safety'),
        (f'delta=f"{F+Q}{F+Q}\ufe0f {{unacked_alerts}} open"',
         'delta=f"🚨 {unacked_alerts} open"'),
        (f'f"{F+Q}{F+Q}\ufe0f {{zero_chunk}} queries returned',
         'f"⚠️ {zero_chunk} queries returned'),
    ],
}

total = 0
for fpath, replacements in fixes.items():
    p = pathlib.Path(fpath)
    text = p.read_text(encoding='utf-8')
    original = text
    for old, new in replacements:
        if old == new:
            continue
        n = text.count(old)
        if n:
            text = text.replace(old, new)
            total += n
            print(f'  {fpath}: {n}x  {ascii(old[:60])}')
        else:
            print(f'  {fpath}: NOT FOUND: {ascii(old[:60])}')
    if text != original:
        p.write_text(text, encoding='utf-8')
        print(f'  Saved {fpath}')

print(f'\nAdditional replacements: {total}')

# Final count
remaining = 0
for fpath in fixes:
    text = pathlib.Path(fpath).read_text(encoding='utf-8')
    for line in text.splitlines():
        stripped = line.lstrip()
        if F in line and not stripped.startswith('#') and stripped:
            remaining += 1
print(f'Active lines still with U+FFFD: {remaining}')
