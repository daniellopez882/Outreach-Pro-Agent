# Production Deployment Guide

## Quick Deploy with Docker

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your production values
nano .env
```

Required environment variables:
```
KIMI_API_KEY=your_kimi_key
DATABASE_URL=postgresql://postgres:password@db:5432/outreach_db
SENDGRID_API_KEY=your_sendgrid_key
FROM_EMAIL=noreply@yourdomain.com
```

### 2. Start Services

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

### 3. Initialize Database

```bash
# Database is auto-initialized on first run
# To manually run migrations:
docker-compose exec app python -c "from models import Base; from sqlalchemy import create_engine; engine = create_engine('postgresql://postgres:outreach_password@db:5432/outreach_db'); Base.metadata.create_all(bind=engine)"
```

### 4. Verify Installation

```bash
# Test API
curl http://localhost:8000/

# Test Kimi connection
curl -X POST http://localhost:8000/test/kimi

# Access API docs
open http://localhost:8000/docs

# Access pgAdmin (optional)
open http://localhost:5050
```

---

## Cloud Deployment

### AWS (EC2 + RDS)

```bash
# 1. Launch EC2 instance (t3.medium or larger)
# 2. Create RDS PostgreSQL instance
# 3. SSH into EC2

# Install Docker
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repo
git clone <your-repo>
cd outreach-architect

# Setup environment
cp .env.example .env
# Edit .env with RDS connection string

# Deploy
docker-compose up -d

# Setup nginx reverse proxy
sudo yum install nginx -y
# Configure nginx (see nginx.conf example below)
```

### Google Cloud (Cloud Run)

```bash
# 1. Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/outreach-architect

# 2. Deploy to Cloud Run
gcloud run deploy outreach-architect \
  --image gcr.io/PROJECT_ID/outreach-architect \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="KIMI_API_KEY=$KIMI_API_KEY,DATABASE_URL=$DATABASE_URL"

# 3. Setup Cloud SQL (PostgreSQL)
gcloud sql instances create outreach-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1
```

### DigitalOcean (Droplet + Managed DB)

```bash
# 1. Create Droplet (4GB RAM, 2 CPUs)
# 2. Create Managed PostgreSQL Database
# 3. SSH into droplet

# Install Docker & Docker Compose
sudo apt update
sudo apt install docker.io docker-compose -y

# Clone and deploy
git clone <your-repo>
cd outreach-architect
cp .env.example .env
# Edit .env with managed DB connection

docker-compose up -d
```

---

## Scaling Strategies

### Horizontal Scaling

```yaml
# docker-compose.override.yml
services:
  app:
    deploy:
      replicas: 3
      
  celery:
    deploy:
      replicas: 5
```

### Load Balancing (nginx)

```nginx
# nginx.conf
upstream outreach_backend {
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

server {
    listen 80;
    server_name outreach.yourdomain.com;

    location / {
        proxy_pass http://outreach_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Database Optimization

```sql
-- Create indexes for performance
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_company ON leads(company);
CREATE INDEX idx_campaigns_status ON outreach_campaigns(status);
CREATE INDEX idx_campaigns_lead ON outreach_campaigns(lead_id);
CREATE INDEX idx_campaigns_sent ON outreach_campaigns(sent_at);

-- Partition large tables
CREATE TABLE outreach_campaigns_2024_q1 PARTITION OF outreach_campaigns
FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
```

---

## Monitoring Setup

### Prometheus + Grafana

```yaml
# Add to docker-compose.yml
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Application Metrics

```python
# Add to main.py
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
email_sent = Counter('emails_sent_total', 'Total emails sent')
response_rate = Gauge('email_response_rate', 'Current response rate')
processing_time = Histogram('lead_processing_seconds', 'Lead processing time')

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## Backup & Recovery

### Database Backups

```bash
# Automated daily backups
# Add to cron: 0 2 * * *
docker-compose exec -T db pg_dump -U postgres outreach_db | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore from backup
gunzip < backup_20240205.sql.gz | docker-compose exec -T db psql -U postgres outreach_db
```

### S3 Backup Script

```bash
#!/bin/bash
# backup-to-s3.sh

BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql.gz"
docker-compose exec -T db pg_dump -U postgres outreach_db | gzip > $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE s3://your-backup-bucket/databases/

# Cleanup old backups (keep last 30 days)
find . -name "backup_*.sql.gz" -mtime +30 -delete
```

---

## Security Checklist

- [ ] Use HTTPS (SSL certificate via Let's Encrypt)
- [ ] Enable firewall (only ports 80, 443, 22)
- [ ] Use strong database passwords
- [ ] Rotate API keys regularly
- [ ] Enable PostgreSQL SSL connections
- [ ] Set up VPC/private network
- [ ] Use secrets manager (AWS Secrets Manager, etc.)
- [ ] Enable API rate limiting
- [ ] Add authentication to API endpoints
- [ ] Regular security updates
- [ ] Monitor for suspicious activity
- [ ] Backup encryption

---

## Performance Tuning

### Database Connection Pool

```python
# config.py
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 40
SQLALCHEMY_POOL_TIMEOUT = 30
```

### Async Processing

```python
# Use Celery for long-running tasks
@celery.task
def process_lead_batch(lead_ids):
    # Heavy processing here
    pass
```

### Caching Strategy

```python
# Cache frequently accessed data
import redis
cache = redis.Redis(host='redis', port=6379)

@app.get("/leads/{lead_id}")
def get_lead(lead_id: int):
    # Try cache first
    cached = cache.get(f"lead:{lead_id}")
    if cached:
        return json.loads(cached)
    
    # Query database
    lead = db.query(Lead).get(lead_id)
    
    # Cache for 1 hour
    cache.setex(f"lead:{lead_id}", 3600, json.dumps(lead.to_dict()))
    
    return lead
```

---

## Maintenance

### Health Checks

```bash
# Automated health monitoring
# Add to cron: */5 * * * *
curl -f http://localhost:8000/ || systemctl restart outreach-architect
```

### Log Rotation

```bash
# /etc/logrotate.d/outreach-architect
/app/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
```

### Update Procedure

```bash
# 1. Backup database
./backup-to-s3.sh

# 2. Pull latest code
git pull origin main

# 3. Rebuild containers
docker-compose build

# 4. Rolling update
docker-compose up -d --no-deps --build app

# 5. Verify
curl http://localhost:8000/
```

---

## Troubleshooting Production Issues

### High Memory Usage

```bash
# Check container stats
docker stats

# Increase memory limit
# docker-compose.yml
services:
  app:
    mem_limit: 2g
```

### Database Connection Errors

```bash
# Check connections
docker-compose exec db psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Increase max connections
# In docker-compose.yml
db:
  command: postgres -c max_connections=200
```

### API Timeouts

```python
# Increase timeout in main.py
app = FastAPI(
    timeout=300,  # 5 minutes
)
```

---

## Cost Optimization

### Infrastructure Costs (Monthly Estimates)

**Small (100-500 leads/day):**
- EC2 t3.small: $15
- RDS db.t3.micro: $15
- Total: ~$30/month

**Medium (1000-5000 leads/day):**
- EC2 t3.medium: $30
- RDS db.t3.small: $30
- ElastiCache (Redis): $15
- Total: ~$75/month

**Large (10,000+ leads/day):**
- EC2 t3.large (x2): $120
- RDS db.m5.large: $140
- ElastiCache: $30
- Load Balancer: $20
- Total: ~$310/month

### API Costs

**Kimi 2.5:**
- ~$0.001 per 1K tokens
- Avg email generation: 5K tokens
- 1000 emails/day = $5/day = $150/month

**SendGrid:**
- Free tier: 100 emails/day
- Essentials: $15/month (50K emails)
- Pro: $60/month (100K emails)

---

## Support & Next Steps

1. **Join Community**: [Discord/Slack link]
2. **Report Issues**: GitHub Issues
3. **Feature Requests**: GitHub Discussions
4. **Pro Support**: support@yourdomain.com

---

**Ready for production!** 🚀
