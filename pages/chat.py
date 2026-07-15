# """
# pages/chat.py
# �??�??�??�??�??�??�??�??�??�??�??�??�??
# Chatbot page for the AskBVRITH multi-page app.
# Called by app.py via st.navigation; do NOT run directly.
# """

# from __future__ import annotations

# import os
# import time
# import uuid
# from pathlib import Path

# import streamlit as st
# from dotenv import load_dotenv

# load_dotenv()

# from login import check_login
# from observability import ObservabilityService
# from observability.utils import count_tokens, hash_text, safe_summary
# from rag_engine import RAGEngine

# try:
#     import psutil
# except ImportError:
#     psutil = None

# ROOT        = Path(__file__).parent.parent
# LOGO_PATH   = ROOT / "static" / "images" / "bvrith_logo.png"
# ASSISTANT_AVATAR = str(LOGO_PATH) if LOGO_PATH.exists() else "🎓"

# QUICK_QUESTIONS = [
#     "What B.Tech courses are offered?",
#     "What is the admission process?",
#     "What are the tuition fees?",
#     "Tell me about placements",
#     "What are the hostel facilities?",
#     "How can I contact the college?",
# ]


# # �??�?? Shared observability service (cached across pages) �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
# @st.cache_resource
# def _get_service() -> ObservabilityService:
#     return ObservabilityService()


# # �??�?? Engine factory (cached so rebuilds survive page switches) �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
# @st.cache_resource
# def _load_engine(chunk_size: int, chunk_overlap: int, top_k: int):
#     engine = RAGEngine(chunk_size=chunk_size, chunk_overlap=chunk_overlap, top_k=top_k)
#     status = engine.initialize()
#     return engine, status


# # �??�?? Session-state initialisation �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
# def _init_state() -> None:
#     defaults = {
#         "messages":             [],
#         "chat_history":         [],
#         "engine":               None,
#         "engine_status":        None,
#         "init_error":           None,
#         "section_filter":       "All Sections",
#         "pending_question":     None,
#         "session_id":           None,
#         "user_id":              None,
#         "request_timestamps":   [],
#         "query_cache":          {},
#         "conversation_summary": "",
#         "feedback_submitted":   {},
#     }
#     for k, v in defaults.items():
#         if k not in st.session_state:
#             st.session_state[k] = v


# def _routing_badge(routing: str) -> str:
#     labels = {
#         "rag":                 "Knowledge Base",
#         "tool":                "Calculator",
#         "rag_or_conversation": "Conversation",
#         "guardrail_oos":       "Out of Scope",
#         "guardrail_validation":"Validation",
#     }
#     return labels.get(routing, routing.replace("_", " ").title())


# def _check_rate_limit() -> bool:
#     now_ts = time.time()
#     window = 60
#     st.session_state.request_timestamps = [
#         ts for ts in st.session_state.request_timestamps if now_ts - ts <= window
#     ]
#     if len(st.session_state.request_timestamps) >= 15:
#         return False
#     st.session_state.request_timestamps.append(now_ts)
#     return True


# def _initialize_session(service: ObservabilityService) -> str:
#     if not st.session_state.session_id:
#         user_id = st.session_state.get("login_username") or os.getenv("APP_USER_ID", "anonymous_user")
#         if user_id == "anonymous_user":
#             user_id = f"anonymous-{uuid.uuid4().hex[:8]}"
#         st.session_state.user_id    = user_id
#         st.session_state.session_id = service.create_session(user_id)
#     return st.session_state.session_id


# def _record_memory_usage(service: ObservabilityService) -> None:
#     if st.session_state.session_id and psutil:
#         try:
#             memory_mb = psutil.Process().memory_info().rss / (1024 * 1024)
#             service.session_tracker.record_memory(
#                 st.session_state.session_id, round(memory_mb, 2)
#             )
#         except Exception:
#             pass


# def _render_hero() -> None:
#     st.markdown(
#         '<div class="hero-card">'
#         "<h1>BVRIT Hyderabad College Assistant</h1>"
#         "<p>Ask anything about admissions, departments, fees, placements, campus life, "
#         "faculty, and services — supported by on-campus knowledge and observability insights.</p>"
#         "</div>",
#         unsafe_allow_html=True,
#     )


# def _render_overview_cards(service: ObservabilityService) -> None:
#     metrics     = service.metrics.get_live_metrics()
#     error_rate  = metrics.get("error_rate", 0.0)
#     success_rate = 100.0 - (error_rate * 100.0)
#     status_text = "Healthy" if error_rate < 0.05 else "Attention Needed"
#     avg_cost    = metrics.get("avg_cost", 0.0)
#     st.markdown(
#         '<div class="overview-card-row">'
#         f'<div class="overview-card"><div class="overview-card-title">Queries</div>'
#         f'<div class="overview-card-value">{metrics.get("query_count", 0)}</div>'
#         '<div class="overview-card-note">Total chatbot requests</div></div>'
#         f'<div class="overview-card"><div class="overview-card-title">Avg latency</div>'
#         f'<div class="overview-card-value">{metrics.get("avg_latency_ms", 0.0):.0f} ms</div>'
#         '<div class="overview-card-note">Response time across all queries</div></div>'
#         f'<div class="overview-card"><div class="overview-card-title">Avg cost</div>'
#         f'<div class="overview-card-value">${avg_cost:.3f}</div>'
#         '<div class="overview-card-note">Estimated cost per query</div></div>'
#         f'<div class="overview-card"><div class="overview-card-title">Success rate</div>'
#         f'<div class="overview-card-value">{success_rate:.0f}%</div>'
#         f'<div class="overview-card-note">System health: {status_text}</div></div>'
#         "</div>",
#         unsafe_allow_html=True,
#     )


# def _render_quick_questions() -> None:
#     st.markdown('<p class="quick-label">Quick questions</p>', unsafe_allow_html=True)
#     cols = st.columns(3)
#     for i, question in enumerate(QUICK_QUESTIONS):
#         with cols[i % 3]:
#             if st.button(question, key=f"quick_{i}", use_container_width=True):
#                 st.session_state.pending_question = question
#                 st.rerun()


# # �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
# # Main render entry point �?? called by app.py
# # �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
# def render() -> None:
#     if os.getenv("ENABLE_LOGIN", "false").lower() in ("1", "true", "yes"):
#         if not check_login():
#             st.stop()

#     _init_state()
#     service    = _get_service()
#     session_id = _initialize_session(service)
#     _record_memory_usage(service)

#     # �??�?? Sidebar �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
#     with st.sidebar:
#         st.markdown('<p class="sidebar-section">Index Settings</p>', unsafe_allow_html=True)
#         with st.expander("Index Settings", expanded=False):
#             chunk_size    = st.slider("Chunk Size",    500, 2000, 1000, 100)
#             chunk_overlap = st.slider("Chunk Overlap",  50,  500,  200,  50)
#             top_k         = st.slider("Top-K Retrieval", 1,   10,    5,   1)
#             rebuild_btn   = st.button("Rebuild Index", use_container_width=True, type="primary")

#         st.markdown('<p class="sidebar-section">Section Filter</p>', unsafe_allow_html=True)
#         section_slot = st.empty()

#         st.markdown('<p class="sidebar-section">System Status</p>', unsafe_allow_html=True)
#         status_slot = st.empty()

#         metrics = service.metrics.get_live_metrics()
#         st.markdown('<p class="sidebar-section">Live Observability</p>', unsafe_allow_html=True)
#         m1, m2, m3, m4 = st.columns(4)
#         m1.metric("Users",       metrics.get("total_users", 0))
#         m2.metric("Sessions",    metrics.get("total_sessions", 0))
#         m3.metric("Cost",        f"${metrics.get('total_cost', 0.0):.2f}")
#         m4.metric("P95 Latency", f"{metrics.get('p95_latency_ms', 0.0):.0f} ms")

#         session_stats  = service.session_tracker.get_session_stats(session_id) or {}
#         query_count    = session_stats.get("query_count", 0) or 0
#         avg_lat_ms     = round(
#             (session_stats.get("total_latency_ms", 0.0) / query_count), 1
#         ) if query_count else 0.0
#         st.markdown('<p class="sidebar-section">Session Stats</p>', unsafe_allow_html=True)
#         st.markdown(f"**Queries:** {query_count}  ")
#         st.markdown(f"**Avg latency:** {avg_lat_ms} ms  ")
#         st.markdown(f"**Total tokens:** {session_stats.get('total_tokens', 0)}  ")
#         st.markdown(f"**Session cost:** ${session_stats.get('session_cost', 0) / 100:.2f}  ")
#         st.markdown(f"**Model:** {session_stats.get('primary_model', 'unknown')}  ")
#         st.markdown(f"**Memory:** {session_stats.get('memory_usage_mb', 'N/A')} MB  ")

#         st.markdown("---")
#         if st.button("Clear Chat", use_container_width=True):
#             st.session_state.messages         = []
#             st.session_state.chat_history     = []
#             st.session_state.pending_question = None
#             st.rerun()

#         st.markdown(
#             '<p class="sidebar-footer">AskBVRITH · BVRIT Hyderabad<br>'
#             "LangChain · ChromaDB · GPT-4o Mini</p>",
#             unsafe_allow_html=True,
#         )

#     # �??�?? Engine bootstrap �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
#     spinner_slot = st.empty()
#     try:
#         if "rebuild_btn" in dir() and rebuild_btn:
#             st.session_state.engine        = None
#             st.session_state.engine_status = None

#         if st.session_state.engine is None:
#             with spinner_slot:
#                 with st.spinner("Initialising knowledge base… (first run may take ~30 s)"):
#                     engine, status = _load_engine(chunk_size, chunk_overlap, top_k)
#             st.session_state.engine        = engine
#             st.session_state.engine_status = status
#             st.session_state.init_error    = None
#             spinner_slot.empty()

#         engine: RAGEngine = st.session_state.engine
#         status            = st.session_state.engine_status

#         with status_slot.container():
#             st.markdown(f"**Document:** `{status.get('document', 'N/A')}`")
#             st.markdown(f"**Chunks:** `{status.get('chunk_count', '?')}`")
#             idx = status.get("index_status", "Unknown")
#             cls = "badge-ok" if idx.lower() in ("newly built", "loaded from disk") else "badge-warn"
#             st.markdown(f"**Index:** <span class='{cls}'>{idx}</span>", unsafe_allow_html=True)

#         with section_slot.container():
#             sel = st.selectbox(
#                 "Filter by section:", engine.get_sections(), index=0,
#                 label_visibility="collapsed",
#             )
#             st.session_state.section_filter = sel

#     except Exception as exc:
#         st.session_state.init_error = str(exc)
#         spinner_slot.empty()

#     if st.session_state.init_error:
#         st.error(f"Initialisation Error: {st.session_state.init_error}")
#         st.info(
#             "Make sure:\n"
#             "1. `data/bvrit_knowledge_base.docx` exists.\n"
#             "2. `OPENROUTER_API_KEY` is set in `.env`.\n"
#             "3. All dependencies are installed: `pip install -r requirements.txt`"
#         )
#         st.stop()

#     # �??�?? Page header �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
#     if LOGO_PATH.exists():
#         left, right = st.columns([1.1, 2.4], vertical_alignment="center")
#         with left:
#             st.image(str(LOGO_PATH), use_container_width=True)
#         with right:
#             _render_hero()
#             _render_overview_cards(service)
#     else:
#         _render_hero()
#         _render_overview_cards(service)

#     # �??�?? Chat history �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
#     if not st.session_state.messages:
#         with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
#             st.markdown(
#                 '<div class="welcome-card">'
#                 "<h3>Welcome to AskBVRITH</h3>"
#                 "<p>Hello! I'm your smart guide to "
#                 "<strong>BVRIT Hyderabad College of Engineering for Women</strong>. "
#                 "I can help you with:</p>"
#                 "<ul>"
#                 "<li><strong>About BVRIT</strong> — history, vision, accreditations</li>"
#                 "<li><strong>Departments</strong> — CSE, ECE, EEE, IT, AI&amp;ML, Data Science &amp; more</li>"
#                 "<li><strong>Admissions</strong> — eligibility, process, key dates, documents</li>"
#                 "<li><strong>Fee Structure</strong> — tuition, hostel, scholarships</li>"
#                 "<li><strong>Placements</strong> — stats, top recruiters, training</li>"
#                 "<li><strong>Campus &amp; Facilities</strong> — labs, library, sports, hostel</li>"
#                 "<li><strong>Faculty</strong> — strength, HODs, research output</li>"
#                 "<li><strong>Contact</strong> — phone, email, directions</li>"
#                 "</ul></div>",
#                 unsafe_allow_html=True,
#             )
#         _render_quick_questions()

#     for msg in st.session_state.messages:
#         avatar = "👤" if msg["role"] == "user" else ASSISTANT_AVATAR
#         with st.chat_message(msg["role"], avatar=avatar):
#             if msg["role"] == "assistant" and msg.get("routing"):
#                 st.markdown(
#                     f'<span class="routing-badge">{_routing_badge(msg["routing"])}</span>',
#                     unsafe_allow_html=True,
#                 )
#             st.markdown(msg["content"])
#             for img_path in msg.get("images", []):
#                 if Path(img_path).exists():
#                     st.image(img_path, use_container_width=True)
#             if msg.get("sources"):
#                 st.markdown(
#                     f'<div class="source-box"><strong>Sources</strong><br>{msg["sources"]}</div>',
#                     unsafe_allow_html=True,
#                 )
#             if msg.get("latency"):
#                 st.markdown(
#                     f'<div class="latency-tag">Response time: {msg["latency"]} s</div>',
#                     unsafe_allow_html=True,
#                 )

#     # �??�?? Chat input �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
#     user_input = st.chat_input("Ask about admissions, fees, departments, placements…")

#     if not user_input and st.session_state.pending_question:
#         user_input                        = st.session_state.pending_question
#         st.session_state.pending_question = None

#     if not user_input:
#         return

#     user_input = user_input.strip()
#     if not user_input:
#         return
#     if len(user_input) > 2000:
#         user_input = user_input[:2000] + "…"

#     st.session_state.messages.append({"role": "user", "content": user_input})
#     with st.chat_message("user", avatar="👤"):
#         st.markdown(user_input)

#     cache_key = hash_text(
#         user_input
#         + "|"
#         + "".join(
#             getattr(msg, "content", "") for msg in st.session_state.chat_history[-6:]
#         )
#     )
#     cached_result = st.session_state.query_cache.get(cache_key)

#     with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
#         ans_slot      = st.empty()
#         img_slot      = st.empty()
#         src_slot      = st.empty()
#         latency_slot  = st.empty()
#         feedback_slot = st.empty()

#         if cached_result:
#             result   = {**cached_result, "cached": True}
#             routing  = result.get("routing", "cache")
#             answer   = result["answer"]
#             sources  = result.get("sources", "")
#             img_paths = result.get("img_paths", [])
#             latency  = result.get("latency", 0.0)
#             st.session_state.messages.append({
#                 "role": "assistant", "content": answer,
#                 "sources": sources, "latency": latency,
#                 "images": img_paths, "routing": routing,
#             })
#             ans_slot.markdown(
#                 f'<span class="routing-badge">Cached response</span>\n\n{answer}',
#                 unsafe_allow_html=True,
#             )
#             if img_paths:
#                 with img_slot.container():
#                     for p in img_paths:
#                         st.image(p, use_container_width=True)
#             if sources:
#                 src_slot.markdown(
#                     f'<div class="source-box"><strong>Sources</strong><br>{sources}</div>',
#                     unsafe_allow_html=True,
#                 )
#             latency_slot.markdown(
#                 f'<div class="latency-tag">Response time: {latency} s</div>',
#                 unsafe_allow_html=True,
#             )
#             return

#         if not _check_rate_limit():
#             ans_slot.error("Rate limit exceeded. Please wait a moment before asking again.")
#             st.session_state.messages.append({
#                 "role": "assistant",
#                 "content": "Rate limit exceeded. Please wait a moment before asking again.",
#             })
#             return

#         active_experiment = service.db.get_active_experiment()
#         prompt_variant    = None
#         prompt_version    = "default_v1"
#         if active_experiment:
#             prompt_variant = service.ab_test.select_variant(active_experiment["id"])
#             engine.set_prompt_variant(prompt_variant)
#             prompt_version = f"{active_experiment['name']}:{prompt_variant}"
#         else:
#             active_prompt = service.ab_test.get_active_prompt_version("assistant")
#             if active_prompt:
#                 prompt_version = active_prompt["version_name"]

#         llm_call = service.logger.create_call(
#             session_id      = st.session_state.session_id,
#             user_id         = st.session_state.user_id,
#             conversation_id = st.session_state.session_id,
#             model_name      = engine.llm.model,
#         )
#         llm_call.user_message_hash    = hash_text(user_input)
#         llm_call.user_message_summary = safe_summary(user_input, max_length=120)
#         llm_call.record_context(
#             prompt_version  = prompt_version,
#             embedding_model = getattr(engine.embeddings, "model", None),
#             ab_test_variant = prompt_variant,
#         )

#         with llm_call:
#             result = engine.query_with_tools(
#                 question       = user_input,
#                 chat_history   = st.session_state.chat_history,
#                 section_filter = st.session_state.get("section_filter", "All Sections"),
#                 verbose        = False,
#             )

#         answer    = result.get("answer", "")
#         docs      = result.get("source_documents", [])
#         latency   = result.get("latency", 0.0)
#         routing   = result.get("routing", "rag")
#         sources   = engine.format_sources(docs)
#         img_paths = engine.extract_images_from_docs(docs)

#         tool_calls = result.get("tool_calls", [])
#         if tool_calls:
#             llm_call.tool_used = ",".join([t.get("tool", "tool") for t in tool_calls])
#         llm_call.record_context(
#             tool_used            = llm_call.tool_used or routing,
#             retrieved_chunk_count = len(docs),
#         )
#         llm_call.record_tokens(
#             count_tokens(user_input, engine.llm.model),
#             count_tokens(answer,     engine.llm.model),
#         )
#         service.session_tracker.set_primary_model(
#             st.session_state.session_id, engine.llm.model
#         )

#         st.session_state.query_cache[cache_key] = {
#             "answer": answer, "sources": sources,
#             "img_paths": img_paths, "latency": latency, "routing": routing,
#         }
#         st.session_state.messages.append({
#             "role": "assistant", "content": answer,
#             "sources": sources, "latency": latency,
#             "images": img_paths, "routing": routing,
#         })

#         ans_slot.markdown(
#             f'<span class="routing-badge">{_routing_badge(routing)}</span>\n\n{answer}',
#             unsafe_allow_html=True,
#         )
#         if img_paths:
#             with img_slot.container():
#                 for p in img_paths:
#                     st.image(p, use_container_width=True)
#         src_slot.markdown(
#             f'<div class="source-box"><strong>Sources</strong><br>{sources}</div>',
#             unsafe_allow_html=True,
#         )
#         latency_slot.markdown(
#             f'<div class="latency-tag">Response time: {latency} s</div>',
#             unsafe_allow_html=True,
#         )

#         alert_metrics = {
#             "latency_ms":     latency * 1000.0,
#             "cost_per_query": llm_call.estimate_cost_cents() / 100.0,
#         }
#         alerts = service.alert_engine.evaluate(
#             alert_metrics, st.session_state.session_id, llm_call.id
#         )
#         for alert in alerts:
#             st.warning(f"Alert: {alert['message']}")

#         if len(st.session_state.chat_history) > 40:
#             st.session_state.chat_history = st.session_state.chat_history[-40:]

#         feedback_id = cache_key
#         with feedback_slot.expander("Help us improve this answer", expanded=False):
#             with st.form(key=f"feedback_form_{feedback_id}"):
#                 rating        = st.radio("Answer rating", [1, 2, 3, 4, 5], index=4, horizontal=True)
#                 helpful       = st.radio("Was this helpful?", ["Yes", "No"], index=0)
#                 feedback_text = st.text_area("Comments", placeholder="Optional feedback")
#                 submitted     = st.form_submit_button("Submit feedback")
#                 if submitted:
#                     service.db.add_feedback(
#                         llm_call.id, rating,
#                         helpful == "Yes",
#                         feedback_text or None,
#                     )
#                     st.success("Thank you for your feedback.")


"""
pages/chat.py
�??�??�??�??�??�??�??�??�??�??�??�??�??
Chatbot page for the AskBVRITH multi-page app.
Called by app.py via st.navigation; do NOT run directly.
"""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from login import check_login
from observability import ObservabilityService
from observability.utils import count_tokens, hash_text, safe_summary
from rag_engine import RAGEngine

try:
    import psutil
except ImportError:
    psutil = None

ROOT        = Path(__file__).parent.parent
LOGO_PATH   = ROOT / "static" / "images" / "bvrith_logo.png"
ASSISTANT_AVATAR = str(LOGO_PATH) if LOGO_PATH.exists() else "🎓"

QUICK_QUESTIONS = [
    "What B.Tech courses are offered?",
    "What is the admission process?",
    "What are the tuition fees?",
    "Tell me about placements",
    "What are the hostel facilities?",
    "How can I contact the college?",
]


# �??�?? Shared observability service (cached across pages) �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
@st.cache_resource
def _get_service() -> ObservabilityService:
    return ObservabilityService()


# �??�?? Engine factory (cached so rebuilds survive page switches) �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
@st.cache_resource
def _load_engine(chunk_size: int, chunk_overlap: int, top_k: int):
    engine = RAGEngine(chunk_size=chunk_size, chunk_overlap=chunk_overlap, top_k=top_k)
    status = engine.initialize()
    return engine, status


# �??�?? Session-state initialisation �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
def _init_state() -> None:
    defaults = {
        "messages":             [],
        "chat_history":         [],
        "engine":               None,
        "engine_status":        None,
        "init_error":           None,
        "section_filter":       "All Sections",
        "pending_question":     None,
        "session_id":           None,
        "user_id":              None,
        "request_timestamps":   [],
        "query_cache":          {},
        "conversation_summary": "",
        "feedback_submitted":   {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _routing_badge(routing: str) -> str:
    labels = {
        "rag":                 "Knowledge Base",
        "tool":                "Calculator",
        "rag_or_conversation": "Conversation",
        "guardrail_oos":       "Out of Scope",
        "guardrail_validation":"Validation",
    }
    return labels.get(routing, routing.replace("_", " ").title())


def _check_rate_limit() -> bool:
    now_ts = time.time()
    window = 60
    st.session_state.request_timestamps = [
        ts for ts in st.session_state.request_timestamps if now_ts - ts <= window
    ]
    if len(st.session_state.request_timestamps) >= 15:
        return False
    st.session_state.request_timestamps.append(now_ts)
    return True


def _initialize_session(service: ObservabilityService) -> str:
    if not st.session_state.session_id:
        user_id = st.session_state.get("login_username") or os.getenv("APP_USER_ID", "anonymous_user")
        if user_id == "anonymous_user":
            user_id = f"anonymous-{uuid.uuid4().hex[:8]}"
        st.session_state.user_id    = user_id
        st.session_state.session_id = service.create_session(user_id)
    return st.session_state.session_id


def _record_memory_usage(service: ObservabilityService) -> None:
    if st.session_state.session_id and psutil:
        try:
            memory_mb = psutil.Process().memory_info().rss / (1024 * 1024)
            service.session_tracker.record_memory(
                st.session_state.session_id, round(memory_mb, 2)
            )
        except Exception:
            pass


def _render_hero() -> None:
    st.markdown(
        '<div class="hero-card">'
        "<h1>BVRIT Hyderabad College Assistant</h1>"
        "<p>Ask anything about admissions, departments, fees, placements, campus life, "
        "faculty, and services — supported by on-campus knowledge and observability insights.</p>"
        "</div>",
        unsafe_allow_html=True,
    )


def _render_overview_cards(service: ObservabilityService) -> None:
    metrics     = service.metrics.get_live_metrics()
    error_rate  = metrics.get("error_rate", 0.0)
    success_rate = 100.0 - (error_rate * 100.0)
    status_text = "Healthy" if error_rate < 0.05 else "Attention Needed"
    avg_cost    = metrics.get("avg_cost", 0.0)
    st.markdown(
        '<div class="overview-card-row">'
        f'<div class="overview-card"><div class="overview-card-title">Queries</div>'
        f'<div class="overview-card-value">{metrics.get("query_count", 0)}</div>'
        '<div class="overview-card-note">Total chatbot requests</div></div>'
        f'<div class="overview-card"><div class="overview-card-title">Avg latency</div>'
        f'<div class="overview-card-value">{metrics.get("avg_latency_ms", 0.0):.0f} ms</div>'
        '<div class="overview-card-note">Response time across all queries</div></div>'
        f'<div class="overview-card"><div class="overview-card-title">Avg cost</div>'
        f'<div class="overview-card-value">${avg_cost:.3f}</div>'
        '<div class="overview-card-note">Estimated cost per query</div></div>'
        f'<div class="overview-card"><div class="overview-card-title">Success rate</div>'
        f'<div class="overview-card-value">{success_rate:.0f}%</div>'
        f'<div class="overview-card-note">System health: {status_text}</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )


def _render_quick_questions() -> None:
    st.markdown('<p class="quick-label">Quick questions</p>', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, question in enumerate(QUICK_QUESTIONS):
        with cols[i % 3]:
            if st.button(question, key=f"quick_{i}", use_container_width=True):
                st.session_state.pending_question = question
                st.rerun()


# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
# Main render entry point �?? called by app.py
# �?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?��?�
def render() -> None:
    if os.getenv("ENABLE_LOGIN", "false").lower() in ("1", "true", "yes"):
        if not check_login():
            st.stop()

    _init_state()
    service    = _get_service()
    session_id = _initialize_session(service)
    _record_memory_usage(service)

    # �??�?? Sidebar �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    with st.sidebar:
        st.markdown('<p class="sidebar-section">Index Settings</p>', unsafe_allow_html=True)
        with st.expander("Index Settings", expanded=False):
            chunk_size    = st.slider("Chunk Size",    500, 2000, 1000, 100)
            chunk_overlap = st.slider("Chunk Overlap",  50,  500,  200,  50)
            top_k         = st.slider("Top-K Retrieval", 1,   10,    5,   1)
            rebuild_btn   = st.button("Rebuild Index", use_container_width=True, type="primary")

        st.markdown('<p class="sidebar-section">Section Filter</p>', unsafe_allow_html=True)
        section_slot = st.empty()

        st.markdown('<p class="sidebar-section">System Status</p>', unsafe_allow_html=True)
        status_slot = st.empty()

        # �??�?? Live Observability �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
        # NOTE: a 4-column row is too narrow for the sidebar �?? labels like
        # "P95 Latency" and values like "$0.024" get truncated. A 2x2 grid
        # gives each metric roughly double the width.
        metrics = service.metrics.get_live_metrics()
        st.markdown('<p class="sidebar-section">Live Observability</p>', unsafe_allow_html=True)
        obs_row1_col1, obs_row1_col2 = st.columns(2)
        obs_row1_col1.metric("Users",    metrics.get("total_users", 0))
        obs_row1_col2.metric("Sessions", metrics.get("total_sessions", 0))
        obs_row2_col1, obs_row2_col2 = st.columns(2)
        obs_row2_col1.metric("Cost",        f"${metrics.get('total_cost', 0.0):.2f}")
        obs_row2_col2.metric("P95 Latency", f"{metrics.get('p95_latency_ms', 0.0):.0f} ms")

        session_stats  = service.session_tracker.get_session_stats(session_id) or {}
        query_count    = session_stats.get("query_count", 0) or 0
        avg_lat_ms     = round(
            (session_stats.get("total_latency_ms", 0.0) / query_count), 1
        ) if query_count else 0.0
        st.markdown('<p class="sidebar-section">Session Stats</p>', unsafe_allow_html=True)
        st.markdown(
            '<div class="session-stats-grid">'
            f'<div class="session-stat"><span class="session-stat-label">Queries</span>'
            f'<span class="session-stat-value">{query_count}</span></div>'
            f'<div class="session-stat"><span class="session-stat-label">Avg latency</span>'
            f'<span class="session-stat-value">{avg_lat_ms} ms</span></div>'
            f'<div class="session-stat"><span class="session-stat-label">Total tokens</span>'
            f'<span class="session-stat-value">{session_stats.get("total_tokens", 0)}</span></div>'
            f'<div class="session-stat"><span class="session-stat-label">Session cost</span>'
            f'<span class="session-stat-value">${session_stats.get("session_cost", 0) / 100:.2f}</span></div>'
            f'<div class="session-stat"><span class="session-stat-label">Model</span>'
            f'<span class="session-stat-value">{session_stats.get("primary_model", "unknown")}</span></div>'
            f'<div class="session-stat"><span class="session-stat-label">Memory</span>'
            f'<span class="session-stat-value">{session_stats.get("memory_usage_mb", "N/A")} MB</span></div>'
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages         = []
            st.session_state.chat_history     = []
            st.session_state.pending_question = None
            st.rerun()

        st.markdown(
            '<p class="sidebar-footer">AskBVRITH · BVRIT Hyderabad<br>'
            "LangChain · ChromaDB · GPT-4o Mini</p>",
            unsafe_allow_html=True,
        )

    # �??�?? Engine bootstrap �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    spinner_slot = st.empty()
    try:
        if "rebuild_btn" in dir() and rebuild_btn:
            st.session_state.engine        = None
            st.session_state.engine_status = None

        if st.session_state.engine is None:
            with spinner_slot:
                with st.spinner("Initialising knowledge base… (first run may take ~30 s)"):
                    engine, status = _load_engine(chunk_size, chunk_overlap, top_k)
            st.session_state.engine        = engine
            st.session_state.engine_status = status
            st.session_state.init_error    = None
            spinner_slot.empty()

        engine: RAGEngine = st.session_state.engine
        status            = st.session_state.engine_status

        with status_slot.container():
            st.markdown(f"**Document:** `{status.get('document', 'N/A')}`")
            st.markdown(f"**Chunks:** `{status.get('chunk_count', '?')}`")
            idx = status.get("index_status", "Unknown")
            cls = "badge-ok" if idx.lower() in ("newly built", "loaded from disk") else "badge-warn"
            st.markdown(f"**Index:** <span class='{cls}'>{idx}</span>", unsafe_allow_html=True)

        with section_slot.container():
            sel = st.selectbox(
                "Filter by section:", engine.get_sections(), index=0,
                label_visibility="collapsed",
            )
            st.session_state.section_filter = sel

    except Exception as exc:
        st.session_state.init_error = str(exc)
        spinner_slot.empty()

    if st.session_state.init_error:
        st.error(f"Initialisation Error: {st.session_state.init_error}")
        st.info(
            "Make sure:\n"
            "1. `data/bvrit_knowledge_base.docx` exists.\n"
            "2. `OPENROUTER_API_KEY` is set in `.env`.\n"
            "3. All dependencies are installed: `pip install -r requirements.txt`"
        )
        st.stop()

    # �??�?? Page header �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    if LOGO_PATH.exists():
        left, right = st.columns([1.1, 2.4], vertical_alignment="center")
        with left:
            st.image(str(LOGO_PATH), use_container_width=True)
        with right:
            _render_hero()
            _render_overview_cards(service)
    else:
        _render_hero()
        _render_overview_cards(service)

    # �??�?? Chat history �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    if not st.session_state.messages:
        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
            st.markdown(
                '<div class="welcome-card">'
                "<h3>Welcome to AskBVRITH</h3>"
                "<p>Hello! I'm your smart guide to "
                "<strong>BVRIT Hyderabad College of Engineering for Women</strong>. "
                "I can help you with:</p>"
                "<ul>"
                "<li><strong>About BVRIT</strong> — history, vision, accreditations</li>"
                "<li><strong>Departments</strong> — CSE, ECE, EEE, IT, AI&amp;ML, Data Science &amp; more</li>"
                "<li><strong>Admissions</strong> — eligibility, process, key dates, documents</li>"
                "<li><strong>Fee Structure</strong> — tuition, hostel, scholarships</li>"
                "<li><strong>Placements</strong> — stats, top recruiters, training</li>"
                "<li><strong>Campus &amp; Facilities</strong> — labs, library, sports, hostel</li>"
                "<li><strong>Faculty</strong> — strength, HODs, research output</li>"
                "<li><strong>Contact</strong> — phone, email, directions</li>"
                "</ul></div>",
                unsafe_allow_html=True,
            )
        _render_quick_questions()

    for msg in st.session_state.messages:
        avatar = "👤" if msg["role"] == "user" else ASSISTANT_AVATAR
        with st.chat_message(msg["role"], avatar=avatar):
            if msg["role"] == "assistant" and msg.get("routing"):
                st.markdown(
                    f'<span class="routing-badge">{_routing_badge(msg["routing"])}</span>',
                    unsafe_allow_html=True,
                )
            st.markdown(msg["content"])
            for img_path in msg.get("images", []):
                if Path(img_path).exists():
                    st.image(img_path, use_container_width=True)
            if msg.get("sources"):
                st.markdown(
                    f'<div class="source-box"><strong>Sources</strong><br>{msg["sources"]}</div>',
                    unsafe_allow_html=True,
                )
            if msg.get("latency"):
                st.markdown(
                    f'<div class="latency-tag">Response time: {msg["latency"]} s</div>',
                    unsafe_allow_html=True,
                )

    # �??�?? Chat input �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
    user_input = st.chat_input("Ask about admissions, fees, departments, placements…")

    if not user_input and st.session_state.pending_question:
        user_input                        = st.session_state.pending_question
        st.session_state.pending_question = None

    if not user_input:
        return

    user_input = user_input.strip()
    if not user_input:
        return
    if len(user_input) > 2000:
        user_input = user_input[:2000] + "…"

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    cache_key = hash_text(
        user_input
        + "|"
        + "".join(
            getattr(msg, "content", "") for msg in st.session_state.chat_history[-6:]
        )
    )
    cached_result = st.session_state.query_cache.get(cache_key)

    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        ans_slot      = st.empty()
        img_slot      = st.empty()
        src_slot      = st.empty()
        latency_slot  = st.empty()
        feedback_slot = st.empty()

        if cached_result:
            result   = {**cached_result, "cached": True}
            routing  = result.get("routing", "cache")
            answer   = result["answer"]
            sources  = result.get("sources", "")
            img_paths = result.get("img_paths", [])
            latency  = result.get("latency", 0.0)
            st.session_state.messages.append({
                "role": "assistant", "content": answer,
                "sources": sources, "latency": latency,
                "images": img_paths, "routing": routing,
            })
            ans_slot.markdown(
                f'<span class="routing-badge">Cached response</span>\n\n{answer}',
                unsafe_allow_html=True,
            )
            if img_paths:
                with img_slot.container():
                    for p in img_paths:
                        st.image(p, use_container_width=True)
            if sources:
                src_slot.markdown(
                    f'<div class="source-box"><strong>Sources</strong><br>{sources}</div>',
                    unsafe_allow_html=True,
                )
            latency_slot.markdown(
                f'<div class="latency-tag">Response time: {latency} s</div>',
                unsafe_allow_html=True,
            )
            return

        if not _check_rate_limit():
            ans_slot.error("Rate limit exceeded. Please wait a moment before asking again.")
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Rate limit exceeded. Please wait a moment before asking again.",
            })
            return

        active_experiment = service.db.get_active_experiment()
        prompt_variant    = None
        prompt_version    = "default_v1"
        if active_experiment:
            prompt_variant = service.ab_test.select_variant(active_experiment["id"])
            engine.set_prompt_variant(prompt_variant)
            prompt_version = f"{active_experiment['name']}:{prompt_variant}"
        else:
            active_prompt = service.ab_test.get_active_prompt_version("assistant")
            if active_prompt:
                prompt_version = active_prompt["version_name"]

        llm_call = service.logger.create_call(
            session_id      = st.session_state.session_id,
            user_id         = st.session_state.user_id,
            conversation_id = st.session_state.session_id,
            model_name      = engine.llm.model,
        )
        llm_call.user_message_hash    = hash_text(user_input)
        llm_call.user_message_summary = safe_summary(user_input, max_length=120)
        llm_call.record_context(
            prompt_version  = prompt_version,
            embedding_model = getattr(engine.embeddings, "model", None),
            ab_test_variant = prompt_variant,
        )

        with llm_call:
            result = engine.query_with_tools(
                question       = user_input,
                chat_history   = st.session_state.chat_history,
                section_filter = st.session_state.get("section_filter", "All Sections"),
                verbose        = False,
            )

        answer    = result.get("answer", "")
        docs      = result.get("source_documents", [])
        latency   = result.get("latency", 0.0)
        routing   = result.get("routing", "rag")
        sources   = engine.format_sources(docs)
        img_paths = engine.extract_images_from_docs(docs)

        tool_calls = result.get("tool_calls", [])
        if tool_calls:
            llm_call.tool_used = ",".join([t.get("tool", "tool") for t in tool_calls])
        llm_call.record_context(
            tool_used            = llm_call.tool_used or routing,
            retrieved_chunk_count = len(docs),
        )
        llm_call.record_tokens(
            count_tokens(user_input, engine.llm.model),
            count_tokens(answer,     engine.llm.model),
        )
        service.session_tracker.set_primary_model(
            st.session_state.session_id, engine.llm.model
        )

        st.session_state.query_cache[cache_key] = {
            "answer": answer, "sources": sources,
            "img_paths": img_paths, "latency": latency, "routing": routing,
        }
        st.session_state.messages.append({
            "role": "assistant", "content": answer,
            "sources": sources, "latency": latency,
            "images": img_paths, "routing": routing,
        })

        ans_slot.markdown(
            f'<span class="routing-badge">{_routing_badge(routing)}</span>\n\n{answer}',
            unsafe_allow_html=True,
        )
        if img_paths:
            with img_slot.container():
                for p in img_paths:
                    st.image(p, use_container_width=True)
        src_slot.markdown(
            f'<div class="source-box"><strong>Sources</strong><br>{sources}</div>',
            unsafe_allow_html=True,
        )
        latency_slot.markdown(
            f'<div class="latency-tag">Response time: {latency} s</div>',
            unsafe_allow_html=True,
        )

        alert_metrics = {
            "latency_ms":     latency * 1000.0,
            "cost_per_query": llm_call.estimate_cost_cents() / 100.0,
        }
        alerts = service.alert_engine.evaluate(
            alert_metrics, st.session_state.session_id, llm_call.id
        )
        for alert in alerts:
            st.warning(f"Alert: {alert['message']}")

        if len(st.session_state.chat_history) > 40:
            st.session_state.chat_history = st.session_state.chat_history[-40:]

        feedback_id = cache_key
        with feedback_slot.expander("Help us improve this answer", expanded=False):
            with st.form(key=f"feedback_form_{feedback_id}"):
                rating        = st.radio("Answer rating", [1, 2, 3, 4, 5], index=4, horizontal=True)
                helpful       = st.radio("Was this helpful?", ["Yes", "No"], index=0)
                feedback_text = st.text_area("Comments", placeholder="Optional feedback")
                submitted     = st.form_submit_button("Submit feedback")
                if submitted:
                    service.db.add_feedback(
                        llm_call.id, rating,
                        helpful == "Yes",
                        feedback_text or None,
                    )
                    st.success("Thank you for your feedback.")

