# BVRIT AI Chatbot - Production Observability System

## Overview

This document describes the complete production-ready observability system for the BVRIT AI Chatbot. The system provides enterprise-level monitoring, logging, cost tracking, alerting, and analytics.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  • Streamlit Chat UI (Current)      • Next.js Dashboard (New)   │
│  • Real-time session metrics        • Admin analytics           │
│  • Live alerts & feedback           • A/B test results          │
└──────────────┬──────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────┐
│                      FastAPI Backend Layer                      │
├──────────────────────────────────────────────────────────────────┤
│  /api/health     - Health check endpoints                       │
│  /api/chat       - Chat queries with logging                    │
│  /api/logs       - Log retrieval and management                 │
│  /api/metrics    - Live metrics and analytics                   │
│  /api/alerts     - Alert management                             │
│  /api/costs      - Cost tracking and analysis                   │
│  /api/abtest     - A/B testing framework                        │
│  /api/analytics  - Comprehensive analytics                      │
│  /api/exports    - CSV/JSON/PDF export                          │
└──────────────┬──────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────┐
│                    Observability Core Layer                     │
├──────────────────────────────────────────────────────────────────┤
│  observability/                                                  │
│  ├── database.py      - SQLite schema and persistence           │
│  ├── logging.py       - LLM call logging wrapper                │
│  ├── session.py       - Session tracking                        │
│  ├── metrics.py       - Live metrics aggregation                │
│  ├── alerts.py        - Alert threshold evaluation              │
│  ├── cost.py          - Cost calculation                        │
│  ├── ab_testing.py    - A/B experiment framework                │
│  ├── evaluation.py    - Quality metrics (RAGAS, etc)            │
│  ├── exports.py       - Report generation                       │
│  └── utils.py         - Utilities (hashing, tokenization)       │
└──────────────┬──────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────┐
│                   Data Storage & Processing                     │
├──────────────────────────────────────────────────────────────────┤
│  • SQLite Database (data/observability.db)                       │
│  • JSON/CSV exports                                              │
│  • Session caching & conversation summaries                     │
│  • Rate limiting counters                                       │
└──────────────────────────────────────────────────────────────────┘
```

## Data Models

### LLM Logs Table
```sql
CREATE TABLE llm_logs (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  conversation_id TEXT,
  user_id_hash TEXT,
  created_at TEXT,
  model_name TEXT,
  model_version TEXT,
  prompt_version TEXT,
  tool_used TEXT,
  input_tokens INTEGER,
  output_tokens INTEGER,
  total_tokens INTEGER,
  latency_ms FLOAT,
  input_cost INTEGER,
  output_cost INTEGER,
  total_cost INTEGER,
  status TEXT,
  error_message TEXT,
  embedding_latency_ms FLOAT,
  retrieval_latency_ms FLOAT,
  generation_latency_ms FLOAT,
  retrieved_chunks INTEGER,
  confidence_score FLOAT
)
```

### Sessions Table
```sql
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  user_id_hash TEXT,
  created_at TEXT,
  updated_at TEXT,
  query_count INTEGER DEFAULT 0,
  total_latency_ms FLOAT DEFAULT 0,
  total_tokens INTEGER DEFAULT 0,
  session_cost INTEGER DEFAULT 0,
  primary_model TEXT,
  memory_usage_mb REAL
)
```

### Costs Table
```sql
CREATE TABLE costs (
  id TEXT PRIMARY KEY,
  date TEXT,
  model_name TEXT,
  input_tokens INTEGER,
  output_tokens INTEGER,
  input_cost INTEGER,
  output_cost INTEGER,
  total_cost INTEGER,
  session_id TEXT,
  user_id_hash TEXT
)
```

### Alerts Table
```sql
CREATE TABLE alerts (
  id TEXT PRIMARY KEY,
  alert_type TEXT,
  severity TEXT,
  message TEXT,
  threshold_value REAL,
  current_value REAL,
  created_at TEXT,
  acknowledged BOOLEAN DEFAULT 0,
  acknowledged_at TEXT,
  acknowledgment_user TEXT
)
```

## API Endpoints

### Health Checks
- `GET /api/health/status` - Health status
- `GET /api/health/readiness` - Readiness probe
- `GET /api/health/liveness` - Liveness probe

### Logging
- `GET /api/logs/list` - List logs with filters
- `GET /api/logs/{log_id}` - Get specific log
- `DELETE /api/logs/{log_id}` - Delete log
- `GET /api/logs/errors/recent` - Get recent errors
- `GET /api/logs/summary/daily` - Daily summary

### Metrics
- `GET /api/metrics/live` - Live dashboard metrics
- `GET /api/metrics/daily` - Daily metrics
- `GET /api/metrics/hourly` - Hourly metrics
- `GET /api/metrics/latency/breakdown` - Latency components
- `GET /api/metrics/quality/metrics` - Quality scores
- `GET /api/metrics/tool-usage` - Tool statistics
- `GET /api/metrics/model-usage` - Model statistics

### Alerts
- `GET /api/alerts/list` - List alerts
- `GET /api/alerts/active` - Active alerts only
- `GET /api/alerts/thresholds` - Alert configurations
- `PUT /api/alerts/thresholds` - Update thresholds
- `POST /api/alerts/{alert_id}/acknowledge` - Acknowledge alert
- `DELETE /api/alerts/{alert_id}` - Delete alert

### Costs
- `GET /api/costs/today` - Today's cost
- `GET /api/costs/daily` - Daily breakdown
- `GET /api/costs/monthly` - Monthly summary
- `GET /api/costs/by-model` - Cost by model
- `GET /api/costs/by-user` - Cost by user
- `GET /api/costs/expensive-queries` - Expensive queries
- `GET /api/costs/projected-monthly` - Projection

### A/B Testing
- `GET /api/abtest/versions` - List prompt versions
- `POST /api/abtest/versions` - Create new version
- `GET /api/abtest/experiments` - List experiments
- `POST /api/abtest/experiments` - Create experiment
- `GET /api/abtest/experiments/{id}/results` - Experiment results
- `POST /api/abtest/experiments/{id}/rollout` - Rollout winner

### Analytics
- `GET /api/analytics/dashboard` - Dashboard data
- `GET /api/analytics/user-analytics` - User metrics
- `GET /api/analytics/session-analytics` - Session metrics
- `GET /api/analytics/query-analytics` - Query statistics
- `GET /api/analytics/feedback-analytics` - Feedback metrics
- `GET /api/analytics/quality-analytics` - Quality metrics
- `GET /api/analytics/error-analytics` - Error analysis

### Exports
- `GET /api/exports/logs/csv` - Export logs as CSV
- `GET /api/exports/logs/json` - Export logs as JSON
- `GET /api/exports/logs/jsonl` - Export logs as JSONL
- `GET /api/exports/metrics/csv` - Export metrics as CSV
- `GET /api/exports/report/daily` - Daily report
- `GET /api/exports/report/weekly` - Weekly report
- `GET /api/exports/report/monthly` - Monthly report

## Deployment

### Running the Backend
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Running the Streamlit UI
```bash
streamlit run app.py
```

## Monitoring Dashboard

The Next.js dashboard provides:
- **Overview**: Key metrics at a glance
- **Logs**: Real-time log viewing and search
- **Metrics**: Charts and trends
- **Alerts**: Active and historical alerts
- **Costs**: Detailed cost analysis
- **A/B Tests**: Experiment results
- **Analytics**: User and session analytics
- **Settings**: Alert thresholds and configuration

## Security Considerations

### What We Log
✅ Timestamp
✅ Request ID
✅ Conversation ID
✅ Model name
✅ Input/Output tokens
✅ Latency
✅ Cost estimate
✅ Status (success/failure)
✅ Tool used

### What We Never Log
❌ Full prompts
❌ Full responses
❌ User messages (only hashes)
❌ Passwords
❌ API keys
❌ Secrets
❌ PII
❌ Medical data
❌ Financial data

## Cost Tracking

### Supported Models
- GPT-4o: $15/MTok input, $60/MTok output
- GPT-4o Mini: $0.15/MTok input, $0.60/MTok output
- GPT-5: $15/MTok input, $60/MTok output
- Embeddings: $0.10/MTok

### Cost Display Hierarchy
- Per Query
- Per Session
- Per User
- Daily
- Monthly
- Projected Monthly

## Alert Thresholds

```python
{
  "latency_ms": 10000,           # Alert if latency > 10s
  "error_rate": 0.05,            # Alert if error rate > 5%
  "cost_per_query": 0.10,        # Alert if cost > $0.10
  "hallucination_threshold": 0.30,
  "faithfulness_threshold": 0.80,
  "bias_threshold": 0.20,
  "toxicity_threshold": 0.10,
}
```

## A/B Testing Workflow

1. Create prompt versions (A, B, C, ...)
2. Create experiment with traffic split (default 50/50)
3. Route requests randomly to versions
4. Track metrics (latency, cost, quality, feedback)
5. Analyze results with statistical tests
6. Recommend winner
7. Rollout winner to 100%

## Evaluation Integration

Integrated with:
- RAGAS: Faithfulness, relevance, context precision
- Giskard: Bias, toxicity detection
- Promptfoo: Automated evaluation

## Next Steps

1. ✅ Backend API scaffold
2. ⏳ Integrate chat endpoints with RAG engine
3. ⏳ Build Next.js dashboard
4. ⏳ Add Slack/email notifications
5. ⏳ Integrate evaluation frameworks
6. ⏳ Add WebSocket support for real-time updates
7. ⏳ Production deployment and monitoring

## Support

For issues or questions, check:
- API documentation: http://localhost:8000/api/docs
- Database schema: `observability/database.py`
- Configuration: `backend/config.py`
