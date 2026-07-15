"""
Fix all U+FFFD corrupted emoji in active (non-commented) code.
Maps each broken byte-sequence to the correct Unicode character.
Does NOT touch commented lines or logic.
"""
import pathlib, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

F = '\ufffd'  # U+FFFD replacement char
Q = '?'

# Every corrupted sequence -> correct char
# Derived by inspecting codepoints from _inspect2 output
EMOJI_MAP = [
    # 4-byte emoji (F + QQQ)
    (F+Q+Q+Q,   '🎓'),   # graduation cap  U+1F393  -- but check 2-byte variants below first

    # 3-byte emoji with variation selector (F + Q + F + \ufe0f)
    (F+Q+F+'\ufe0f', '⚠️'),   # warning sign   U+26A0 U+FE0F

    # 3-byte emoji (F + Q + F) -- without variation selector
    (F+Q+F,     '✅'),   # check mark -- BUT this matches many things, use context

    # 2-byte sequences  (F + Q)
    (F+Q,       '→'),   # right arrow -- used as separator in docstrings/strings

    # NOTE: above order matters -- longest match first
]

# -----------------------------------------------------------------
# Per-file replacement tables  (old_str, new_str)
# Built from reading the audit output line by line.
# -----------------------------------------------------------------

# Helper: build a replacement table entry
def r(old, new): return (old, new)

# ── app.py ────────────────────────────────────────────────────────
APP_FIXES = [
    # Navigation page titles  (L1518-1520)
    r(f'title="{F+Q+Q+F} Chat"',        'title="💬 Chat"'),
    r(f'title="{F+Q}{F+Q}\ufe0f Governance"', 'title="🏛️ Governance"'),
    r(f'title="{F+Q+Q+F} Evaluation"',  'title="🧪 Evaluation"'),
    # CSS section comment separators (cosmetic only, in string literals passed to st.markdown)
    # These are inside triple-quoted CSS strings -- safe to replace globally
]

# ── pages/chat.py ─────────────────────────────────────────────────
CHAT_FIXES = [
    # hero card description dash
    r(f'services {F+Q+Q} supported by', 'services — supported by'),
    # spinner ellipsis
    r(f'knowledge base{F+Q+F} (first run', 'knowledge base… (first run'),
    # welcome card list dashes
    r(f'BVRIT</strong> {F+Q+Q} history',    'BVRIT</strong> — history'),
    r(f'Departments</strong> {F+Q+Q} CSE',  'Departments</strong> — CSE'),
    r(f'Admissions</strong> {F+Q+Q} elig',  'Admissions</strong> — elig'),
    r(f'Fee Structure</strong> {F+Q+Q} tui','Fee Structure</strong> — tui'),
    r(f'Placements</strong> {F+Q+Q} stats', 'Placements</strong> — stats'),
    r(f'Facilities</strong> {F+Q+Q} labs',  'Facilities</strong> — labs'),
    r(f'Faculty</strong> {F+Q+Q} strength', 'Faculty</strong> — strength'),
    r(f'Contact</strong> {F+Q+Q} phone',    'Contact</strong> — phone'),
    # chat input placeholder ellipsis
    r(f'placements{F+Q+F}"',   'placements…"'),
    # truncation ellipsis
    r(f'[:2000] + "{F+Q+F}"',  '[:2000] + "…"'),
]

# ── rag_engine.py ─────────────────────────────────────────────────
RAG_FIXES = [
    # Rupee symbol ₹  (U+20B9 = 3-byte UTF-8: E2 82 B9 -> corrupted to F+Q+Q or similar)
    r(f'{F+Q+Q}{{amount:,}}/year. Total 4-year: {F+Q+Q}{{amount * 4:,}}',
      '₹{amount:,}/year. Total 4-year: ₹{amount * 4:,}'),
    # Arrow in date checker output  →
    r(f'days {F+Q+Q} on {{date',  'days — on {date'),
    # Warning emoji ⚠️
    r(f'return f"{F+Q+F}\ufe0f Validation error:',  'return f"⚠️ Validation error:'),
    r(f'"answer": f"{F+Q+F}\ufe0f {{validation_error}}',
      '"answer": f"⚠️ {validation_error}'),
    r(f'return f"{F+Q+F}\ufe0f All AI models',       'return f"⚠️ All AI models'),
    # Em-dash separators in scope messages
    r(f'scope {F+Q+Q} do NOT',    'scope — do NOT'),
    # Section source separator
    r(f'key = f"{{section}} {F+Q+Q} p.{{page}}"',  'key = f"{section} — p.{page}"'),
    # OOS answer em-dash
    r(f'outside my scope {F+Q+Q} I can only',  'outside my scope — I can only'),
    # Faculty section strings with em-dash
    r(f'(CSE) {F+Q+Q} 49 faculty',         '(CSE) — 49 faculty'),
    r(f'(ECE) {F+Q+Q} 27 faculty',         '(ECE) — 27 faculty'),
    r(f'(EEE) {F+Q+Q} 16 faculty',         '(EEE) — 16 faculty'),
    r(f'(IT) {F+Q+Q} 9 faculty',           '(IT) — 9 faculty'),
    r(f'CSE {F+Q+Q} Artificial',           'CSE — Artificial'),
    r(f'(AI&ML) {F+Q+Q} 15 faculty',       '(AI&ML) — 15 faculty'),
    r(f'(BS&H) {F+Q+Q} 33 faculty',        '(BS&H) — 33 faculty'),
    # Comment arrow
    r(f'canonical_name {F+Q+Q} matched',   'canonical_name → matched'),
]

# ── login.py ─────────────────────────────────────────────────────
LOGIN_FIXES = [
    r(f'otherwise {F+Q+Q} in which',  'otherwise — in which'),
]

# ── governance_dashboard.py ───────────────────────────────────────
GOV_DB_FIXES = [
    r(f'page_icon="{F+Q}{F+Q}\ufe0f"',   'page_icon="🏛️"'),
    r(f'else "{F+Q+Q}"',                  'else "N/A"'),
    r(f'"### {F+Q}{F+Q}\ufe0f Governance Dashboard"',
      '"### 🏛️ Governance Dashboard"'),
    r(f'"{F+Q+Q+Q} Refresh"',             '"🔄 Refresh"'),
    r(f'"<h1>{F+Q}{F+Q}\ufe0f Governance &amp;',
      '"<h1>🏛️ Governance &amp;'),
    r(f'metrics {F+Q+Q} all derived',     'metrics — all derived'),
    r(f'Functional {F+Q+Q} Correctness',  'Functional — Correctness'),
    r(f'class="cat-pill">{F+Q+Q+F} 01',   'class="cat-pill">✅ 01'),
    r(f'"{F+Q+Q} No errors recorded',     '"✅ No errors recorded'),
    r(f'Quality {F+Q+Q} Response',         'Quality — Response'),
    r(f'f"{{avg_rating:.2f}} / 5" if avg_rating is not None else "{F+Q+Q}")',
      'f"{avg_rating:.2f} / 5" if avg_rating is not None else "N/A")'),
    r(f'f"{{helpful_pct*100:.0f}}%" if helpful_pct is not None else "{F+Q+Q}")',
      'f"{helpful_pct*100:.0f}%" if helpful_pct is not None else "N/A")'),
    r(f'f"{{avg_chunks:.1f}}" if avg_chunks else "{F+Q+Q}"',
      'f"{avg_chunks:.1f}" if avg_chunks else "N/A"'),
    r(f'[f"{F+Q+Q} {{i}}" for i in rating_counts',
      '[f"⭐ {i}" for i in rating_counts'),
    r(f'Safety {F+Q+Q} Content',           'Safety — Content'),
    r(f'class="cat-pill">{F+Q+Q}{F+Q}\ufe0f 03', 'class="cat-pill">🛡️ 03'),
    r(f'Security {F+Q+Q} Prompt',          'Security — Prompt'),
    r(f'class="cat-pill">{F+Q+Q+Q} 04',    'class="cat-pill">🔒 04'),
    r(f'delta=f"{F+Q}{F+Q}\ufe0f {{unacked_alerts}} open"',
      'delta=f"🚨 {unacked_alerts} open"'),
    r(f'"{F+Q+Q} No alerts recorded',      '"✅ No alerts recorded'),
    r(f'Robustness {F+Q+Q} Edge',          'Robustness — Edge'),
    r(f'class="cat-pill">{F+Q+Q+F} 05',    'class="cat-pill">🛠️ 05'),
    r(f'primary_model or "{F+Q+Q}")',       'primary_model or "N/A")'),
    r(f'Performance {F+Q+Q} Latency',      'Performance — Latency'),
    r(f'class="cat-pill">{F+Q+F} 06',      'class="cat-pill">⚡ 06'),
    r(f'Context {F+Q+Q} Retrieval',        'Context — Retrieval'),
    r(f'class="cat-pill">{F+Q+Q+Q} 07',    'class="cat-pill">🔍 07'),
    r(f'relevancy is not None else "{F+Q+Q}")',   'relevancy is not None else "N/A")'),
    r(f'faithfulness is not None else "{F+Q+Q}")', 'faithfulness is not None else "N/A")'),
    r(f'f"{F+Q}{F+Q}\ufe0f {{zero_chunk}} queries returned no context',
      'f"⚠️ {zero_chunk} queries returned no context'),
    r(f'"{F+Q+Q} All queries retrieved',   '"✅ All queries retrieved'),
    r(f'RAGAS {F+Q+Q} RAG',                'RAGAS — RAG'),
    r(f'class="cat-pill">{F+Q+Q+Q} 08',    'class="cat-pill">📊 08'),
    r(f'faithfulness is not None else "{F+Q+Q}",',  'faithfulness is not None else "N/A",'),
    r(f'relevancy is not None else "{F+Q+Q}",',     'relevancy is not None else "N/A",'),
    r(f'hallucination is not None else "{F+Q+Q}",', 'hallucination is not None else "N/A",'),
    r(f'"{F+Q}\ufe0f Download RAGAS Reports (CSV)"',
      '"📥 Download RAGAS Reports (CSV)"'),
    r(f'"{F+Q}{F+Q}\ufe0f AskBVRITH Governance Dashboard',
      '"🏛️ AskBVRITH Governance Dashboard'),
]

# ── evaluation_dashboard.py ───────────────────────────────────────
EVAL_DB_FIXES = [
    r(f'page_icon="{F+Q+F}{F}"',     'page_icon="🧪"'),
    r(f'"### {F+Q+F}{F} Evaluation Suite"', '"### 🧪 Evaluation Suite"'),
    r(f'"{F+Q+F}  Run Evaluation"',   '"▶️  Run Evaluation"'),
    r(f'"## {F+Q+F}{F} Evaluation Dashboard"', '"## 🧪 Evaluation Dashboard"'),
    r(f'8 dimensions {F+Q+Q} "',      '8 dimensions — "'),
    r(f'evaluation suite{F+Q+F}")',    'evaluation suite…")'),
    r(f'>{F+Q+F} {{d.warnings}} warn',  '>⚠️ {d.warnings} warn'),
    r(f'>{F+Q+Q} {{d.failed}} fail',    '>❌ {d.failed} fail'),
    r(f"f'<h3>{F+Q+F} Weakest:",        "f'<h3>⚠️ Weakest:"),
    r(f'icon = "{F+Q+F}" if r.status == Status.WARNING else "{F+Q+Q}"',
      'icon = "⚠️" if r.status == Status.WARNING else "❌"'),
    r(f'{F+Q+Q} {{r.case.description}}',  '— {r.case.description}'),
    r(f"f'<h3>{F+Q+Q+Q} RAGAS Diagnosis</h3>'",
      "f'<h3>📊 RAGAS Diagnosis</h3>'"),
    r(f'("{F+Q+F}" if len(res.case.input) > 60',  '("…" if len(res.case.input) > 60'),
    r(f'"{F+Q} Download Full Results (CSV)"',  '"📥 Download Full Results (CSV)"'),
    r(f'"{F+Q} Download Summary (JSON)"',       '"📥 Download Summary (JSON)"'),
    r(f'"{F+Q+F}{F} AskBVRITH Evaluation Dashboard',
      '"🧪 AskBVRITH Evaluation Dashboard'),
]

# ── evaluation_suite.py ───────────────────────────────────────────
EVAL_SUITE_FIXES = [
    r(f'# {F+Q+Q} EvaluationReport',  '# → EvaluationReport'),
    r(f'Faithfulness is low {F+Q+Q} the model',  'Faithfulness is low — the model'),
    r(f'Answer Relevancy is low {F+Q+Q} responses', 'Answer Relevancy is low — responses'),
    r(f'Context Precision is lowest {F+Q+Q} retrieval', 'Context Precision is lowest — retrieval'),
    r(f'Context Recall is low {F+Q+Q} relevant', 'Context Recall is low — relevant'),
    r('lowest ({val:.2f}) ' + F+Q+Q + ' {tips',  'lowest ({val:.2f}) — {tips'),
    r(f'year (1{F+Q+Q}4), and',    'year (1–4), and'),
    r(f'unexpectedly rejected {F+Q+Q} {{result}}', 'unexpectedly rejected — {result}'),
    r(f"correctly rejected {F+Q+Q} '{{result}}'",  "correctly rejected — '{result}'"),
    r(f"mention '{{fragment}}' {F+Q+Q} got:",       "mention '{fragment}' — got:"),
    r(f"out-of-scope {F+Q+Q} is a valid",            "out-of-scope — is a valid"),
    r(f"rejected correctly {F+Q+Q} '{{result}}'",    "rejected correctly — '{result}'"),
    r(f"missing '{{fragment}}' {F+Q+Q} got:",         "missing '{fragment}' — got:"),
    r(f"rejected valid args {F+Q+Q} {{result}}",      "rejected valid args — {result}"),
    r(f'detected in input {F+Q+Q} system prompt',    'detected in input — system prompt'),
    r(f'pattern found {F+Q+Q} input is clean',       'pattern found — input is clean'),
    r(f'placeholder {F+Q+Q} replaced by runner',     'placeholder — replaced by runner'),
    r(f'retrieval {F+Q+Q} no guard fired',            'retrieval — no guard fired'),
    r(f'Faithfulness 0.89 {F+Q+F} 0.80 threshold',  'Faithfulness 0.89 ≥ 0.80 threshold'),
    r(f'Faithfulness below 0.80 {F+Q+Q} review',    'Faithfulness below 0.80 — review'),
    r(f'Answer Relevancy 0.91 {F+Q+F} 0.80 threshold', 'Answer Relevancy 0.91 ≥ 0.80 threshold'),
    r(f'Answer Relevancy below 0.80 {F+Q+Q} refine',   'Answer Relevancy below 0.80 — refine'),
    r(f'Context Precision 0.72 {F+Q+Q} just above',     'Context Precision 0.72 — just above'),
    r(f'Context Precision {F+Q+F} 0.80',                'Context Precision ≥ 0.80'),
    r(f'Context Precision below 0.70 {F+Q+Q} reduce',   'Context Precision below 0.70 — reduce'),
    r(f'ms {F+Q+Q} exceeds 5 ms target',                 'ms — exceeds 5 ms target'),
    r(f'calls are made {F+Q+Q} all checkers',            'calls are made — all checkers'),
]

# ── observability_dashboard.py ────────────────────────────────────
OBS_FIXES = [
    r(f'page_icon="{F+Q+Q+Q}"',     'page_icon="📊"'),
    r(f'"{F+Q+Q+Q} BVRIT AI Observ', '"📊 BVRIT AI Observ'),
]

# ── pages/evaluation.py ───────────────────────────────────────────
PAGE_EVAL_FIXES = [
    r(f'>{F+Q+F} {{d.warnings}} warn',  '>⚠️ {d.warnings} warn'),
    r(f'>{F+Q+Q} {{d.failed}} fail',    '>❌ {d.failed} fail'),
    r(f'"{F+Q+F}  Run Evaluation"',      '"▶️  Run Evaluation"'),
    r(f'"## {F+Q+F}{F} Evaluation Dashboard"', '"## 🧪 Evaluation Dashboard"'),
    r(f'8 dimensions {F+Q+Q} "',        '8 dimensions — "'),
    r(f'evaluation suite{F+Q+F}")',      'evaluation suite…")'),
    r(f"f'<h3>{F+Q+F} Weakest:",         "f'<h3>⚠️ Weakest:"),
    r(f'icon = "{F+Q+F}" if r.status == Status.WARNING else "{F+Q+Q}"',
      'icon = "⚠️" if r.status == Status.WARNING else "❌"'),
    r(f'{F+Q+Q} {{r.case.description}}',   '— {r.case.description}'),
    r(f'f"<h3>{F+Q+Q+Q} RAGAS Diagnosis</h3>"',
      'f"<h3>📊 RAGAS Diagnosis</h3>"'),
    r(f'("{F+Q+F}" if len(res.case.input) > 60',  '("…" if len(res.case.input) > 60'),
    r(f'"{F+Q} Download Full Results (CSV)"',  '"📥 Download Full Results (CSV)"'),
    r(f'"{F+Q} Download Summary (JSON)"',       '"📥 Download Summary (JSON)"'),
    r(f'"{F+Q+F}{F} Evaluation Dashboard',      '"🧪 Evaluation Dashboard'),
]

# ── pages/governance.py ───────────────────────────────────────────
PAGE_GOV_FIXES = [
    r(f'else "{F+Q+Q}"',               'else "N/A"'),
    r(f'"{F+Q+Q+Q} Refresh"',          '"🔄 Refresh"'),
    r(f'"<h1>{F+Q}{F+Q}\ufe0f Governance &amp;', '"<h1>🏛️ Governance &amp;'),
    r(f'RAGAS {F+Q+Q} derived',        'RAGAS — derived'),
    r(f'Functional {F+Q+Q} Correctness', 'Functional — Correctness'),
    r(f'class="cat-pill">{F+Q+Q+F} 01',  'class="cat-pill">✅ 01'),
    r(f'"{F+Q+Q} No errors recorded',    '"✅ No errors recorded'),
    r(f'Quality {F+Q+Q} Response',       'Quality — Response'),
    r(f'"N/A"' , '"N/A"'),   # no-op placeholder
    r(f'f"{{avg_rating:.2f}} / 5" if avg_rating else "{F+Q+Q}")',
      'f"{avg_rating:.2f} / 5" if avg_rating else "N/A")'),
    r(f'f"{{helpful_pct*100:.0f}}%" if helpful_pct else "{F+Q+Q}")',
      'f"{helpful_pct*100:.0f}%" if helpful_pct else "N/A")'),
    r(f'f"{{avg_chunks:.1f}}" if avg_chunks else "{F+Q+Q}")',
      'f"{avg_chunks:.1f}" if avg_chunks else "N/A")'),
    r(f'[f"{F+Q+Q} {{i}}" for i in rc',  '[f"⭐ {i}" for i in rc'),
    r(f'Safety {F+Q+Q} Content',          'Safety — Content'),
    r(f'class="cat-pill">{F+Q+Q}{F+Q}\ufe0f 03', 'class="cat-pill">🛡️ 03'),
    r(f'evaluation reports {F+Q+Q} use',  'evaluation reports — use'),
    r(f'Security {F+Q+Q} Prompt',         'Security — Prompt'),
    r(f'class="cat-pill">{F+Q+Q+Q} 04',   'class="cat-pill">🔒 04'),
    r(f'delta=f"{F+Q}{F+Q}\ufe0f {{unacked_alerts}} open"',
      'delta=f"🚨 {unacked_alerts} open"'),
    r(f'"{F+Q+Q} No alerts recorded',     '"✅ No alerts recorded'),
    r(f'Robustness {F+Q+Q} Edge',         'Robustness — Edge'),
    r(f'class="cat-pill">{F+Q+Q+F} 05',   'class="cat-pill">🛠️ 05'),
    r(f'primary_model or "{F+Q+Q}")',      'primary_model or "N/A")'),
    r(f'Performance {F+Q+Q} Latency',     'Performance — Latency'),
    r(f'class="cat-pill">{F+Q+F} 06',     'class="cat-pill">⚡ 06'),
    r(f'Context {F+Q+Q} Retrieval',       'Context — Retrieval'),
    r(f'class="cat-pill">{F+Q+Q+Q} 07',   'class="cat-pill">🔍 07'),
    r(f'relevancy    else "{F+Q+Q}")',     'relevancy    else "N/A")'),
    r(f'faithfulness else "{F+Q+Q}")',     'faithfulness else "N/A")'),
    r(f'f"{F+Q}{F+Q}\ufe0f {{zero_chunk}} queries returned no context',
      'f"⚠️ {zero_chunk} queries returned no context'),
    r(f'else "{F+Q+Q} All queries retrieved',  'else "✅ All queries retrieved'),
    r(f'RAGAS {F+Q+Q} RAG',               'RAGAS — RAG'),
    r(f'class="cat-pill">{F+Q+Q+Q} 08',   'class="cat-pill">📊 08'),
    r(f'_pct(faithfulness)  if faithfulness  else "{F+Q+Q}")',
      '_pct(faithfulness)  if faithfulness  else "N/A")'),
    r(f'_pct(relevancy)      if relevancy      else "{F+Q+Q}")',
      '_pct(relevancy)      if relevancy      else "N/A")'),
    r(f'_pct(hallucination)  if hallucination  else "{F+Q+Q}")',
      '_pct(hallucination)  if hallucination  else "N/A")'),
    r(f'"{F+Q}\ufe0f Download RAGAS Reports (CSV)"',
      '"📥 Download RAGAS Reports (CSV)"'),
    r(f'"{F+Q}{F+Q}\ufe0f Governance Dashboard · BVRIT',
      '"🏛️ Governance Dashboard · BVRIT'),
]

ALL = {
    'app.py':                    APP_FIXES,
    'pages/chat.py':             CHAT_FIXES,
    'rag_engine.py':             RAG_FIXES,
    'login.py':                  LOGIN_FIXES,
    'governance_dashboard.py':   GOV_DB_FIXES,
    'evaluation_dashboard.py':   EVAL_DB_FIXES,
    'evaluation_suite.py':       EVAL_SUITE_FIXES,
    'observability_dashboard.py':OBS_FIXES,
    'pages/evaluation.py':       PAGE_EVAL_FIXES,
    'pages/governance.py':       PAGE_GOV_FIXES,
}

total_changed = 0
for fpath, fixes in ALL.items():
    p = pathlib.Path(fpath)
    text = p.read_text(encoding='utf-8')
    original = text
    for old, new in fixes:
        if old == new:
            continue
        n = text.count(old)
        if n:
            text = text.replace(old, new)
            total_changed += n
            print(f'  {fpath}: {n}x  {ascii(old[:50])}')
    if text != original:
        p.write_text(text, encoding='utf-8')
        print(f'  ✓ Saved {fpath}')

print(f'\nTotal replacements: {total_changed}')

# Final check: count remaining FFFD in active lines
remaining = 0
for fpath in ALL:
    text = pathlib.Path(fpath).read_text(encoding='utf-8')
    for line in text.splitlines():
        stripped = line.lstrip()
        if F in line and not stripped.startswith('#') and stripped and not stripped.startswith('"""'):
            remaining += 1
print(f'Active lines still containing U+FFFD: {remaining}')
