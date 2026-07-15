# Production Deployment Guide

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL or SQLite
- OpenAI API key

### 1. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Initialize database
python -c "from observability.database import ObservabilityDatabase; db = ObservabilityDatabase(); print('✅ Database initialized')"

# Run backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup (Next.js Dashboard)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Production build
npm run build
npm start
```

### 3. Streamlit Chat UI

```bash
# Terminal 1: Run the Streamlit app
streamlit run app.py

# Access at: http://localhost:8501
```

## Architecture Overview

### Multi-Tier Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                         │
├─────────────────────────────────────────────────────────┤
│  • Streamlit Chat UI (User Chat)                        │
│  • Next.js Dashboard (Admin Monitoring)                 │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                   API Layer (FastAPI)                   │
├─────────────────────────────────────────────────────────┤
│  • REST endpoints                                       │
│  • WebSocket connections (real-time updates)           │
│  • Request validation & middleware                      │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│              Business Logic Layer                       │
├─────────────────────────────────────────────────────────┤
│  • RAG Engine (Chat)                                    │
│  • Observability Service                                │
│  • Cost Calculator                                      │
│  • Alert Evaluator                                      │
│  • A/B Testing Engine                                   │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│              Data Persistence Layer                     │
├─────────────────────────────────────────────────────────┤
│  • SQLite/PostgreSQL                                    │
│  • Redis Cache (optional)                               │
│  • File Exports (CSV/JSON/PDF)                          │
└─────────────────────────────────────────────────────────┘
```

## Database Configuration

### SQLite (Development/Small Scale)

```python
# .env
DATABASE_URL=sqlite:///./data/observability.db
```

### PostgreSQL (Production)

```python
# .env
DATABASE_URL=postgresql://user:password@localhost/bvrit_obs
```

## Monitoring & Logging

### Structured Logging

Every request is logged with:
- Timestamp
- Request ID
- Duration
- Status code
- User ID (hashed)
- Endpoint
- Response size

### Log Files

```
logs/
├── app.log           # Main application log
├── api.log          # API server logs
├── observability.log # Observability system logs
└── errors.log       # Error logs only
```

### Log Levels

```python
DEBUG   - Development debugging
INFO    - General information
WARNING - Warning messages
ERROR   - Error messages
CRITICAL - Critical failures
```

## Performance Optimization

### Response Caching

```python
# Cache settings in config.py
CACHE_TTL_SECONDS = 300  # 5 minutes
CACHE_ENABLED = True
```

### Database Optimization

```sql
-- Indexes for faster queries
CREATE INDEX idx_llm_logs_session_id ON llm_logs(session_id);
CREATE INDEX idx_llm_logs_created_at ON llm_logs(created_at);
CREATE INDEX idx_costs_date ON costs(date);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
```

### Rate Limiting

```python
# In middleware.py
RATE_LIMIT_REQUESTS = 100      # per window
RATE_LIMIT_WINDOW_SECONDS = 60 # 1 minute
```

## Security Hardening

### API Authentication (Recommended for Production)

```python
# Add JWT authentication
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthCredentials = Depends(security)):
    if credentials.credentials != os.getenv("API_TOKEN"):
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials
```

### Environment Variables

```bash
# Never commit these!
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://...
JWT_SECRET=...
SLACK_WEBHOOK=...
```

### CORS Configuration

```python
# In production, specify allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Not ["*"]
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Scaling Considerations

### Horizontal Scaling

1. **Load Balancer**: Use Nginx or HAProxy
   ```nginx
   upstream backend {
       server backend1:8000;
       server backend2:8000;
       server backend3:8000;
   }
   ```

2. **Database**: Scale up with read replicas
   ```
   Primary DB → Read Replicas
   ```

3. **Cache**: Use Redis for distributed cache
   ```python
   REDIS_URL=redis://localhost:6379/0
   ```

### Deployment Options

#### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      DATABASE_URL: postgresql://user:password@db:5432/bvrit
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: bvrit
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

#### Cloud Deployment

**AWS:**
```bash
# ECR for Docker images
aws ecr create-repository --repository-name bvrit-chatbot

# ECS for container orchestration
aws ecs create-service ...

# RDS for database
aws rds create-db-instance ...
```

**Google Cloud:**
```bash
# Cloud Run for serverless
gcloud run deploy bvrit-chatbot --source .

# Cloud SQL for database
gcloud sql instances create bvrit-db
```

**Azure:**
```bash
# Azure Container Instances
az container create --resource-group ...

# Azure Database for PostgreSQL
az postgres server create ...
```

## Monitoring & Observability

### Application Monitoring

Use Prometheus + Grafana:

```python
from prometheus_client import Counter, Histogram

request_count = Counter(
    'bvrit_requests_total',
    'Total requests',
    ['method', 'endpoint']
)

request_latency = Histogram(
    'bvrit_request_latency_seconds',
    'Request latency'
)
```

### Error Tracking

Use Sentry:

```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://...@sentry.io/...",
    traces_sample_rate=1.0,
)
```

### Alerting

Configure alerts in your system:

```python
# Slack notifications
@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    alert = db.get_alert(alert_id)
    if alert:
        send_slack_message(
            f"Alert {alert_id} acknowledged",
            webhook=os.getenv("SLACK_WEBHOOK")
        )
```

## Maintenance & Operations

### Database Backups

```bash
# Daily backup
0 2 * * * pg_dump -U user -d bvrit > /backups/bvrit_$(date +%Y%m%d).sql

# Restore
psql -U user -d bvrit < /backups/bvrit_20240101.sql
```

### Log Rotation

```bash
# In /etc/logrotate.d/bvrit
/app/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
}
```

### Health Checks

```bash
# Monitor health endpoint
*/5 * * * * curl http://localhost:8000/api/health/status || alert "API Down"
```

## Troubleshooting

### High Latency

1. Check database connection
2. Monitor API response times
3. Check LLM API latency
4. Verify network connectivity

### High Costs

1. Review cost trends
2. Check expensive queries
3. Analyze model usage
4. Optimize prompts

### High Error Rate

1. Check error logs
2. Verify API keys
3. Check rate limits
4. Review LLM responses

## Support & Documentation

- API Docs: http://your-domain/api/docs
- GitHub: https://github.com/yourrepo
- Issues: Report via GitHub Issues
- Email: support@example.com

## Checklist for Production

- [ ] Environment variables configured
- [ ] Database backups automated
- [ ] SSL/TLS certificates installed
- [ ] API authentication enabled
- [ ] CORS configured correctly
- [ ] Rate limiting configured
- [ ] Monitoring alerts set up
- [ ] Error tracking configured
- [ ] Load balancer configured
- [ ] Database replicas set up
- [ ] Cache (Redis) configured
- [ ] Log rotation configured
- [ ] Health checks monitoring
- [ ] Security audit completed
- [ ] Performance testing done
