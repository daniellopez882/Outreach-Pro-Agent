# 🚀 Quick Start Guide - Personalized Outreach Architect

## Get Running in 10 Minutes

### Step 1: Setup (2 minutes)

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
nano .env  # Add your Kimi API key
```

**Minimum required in .env:**
```bash
KIMI_API_KEY=your_moonshot_kimi_key_here
DATABASE_URL=postgresql://postgres:password@localhost:5432/outreach_db
SENDGRID_API_KEY=your_sendgrid_key  # Optional for testing
FROM_EMAIL=test@example.com
FROM_NAME=Your Name
```

### Step 2: Setup Database (2 minutes)

```bash
# Option A: Local PostgreSQL
createdb outreach_db

# Option B: Use SQLite for quick testing (modify config.py)
# DATABASE_URL=sqlite:///./outreach.db
```

### Step 3: Start Server (1 minute)

```bash
python main.py
```

Server starts at: http://localhost:8000

API docs at: http://localhost:8000/docs

### Step 4: Test the System (5 minutes)

#### Option A: Use the Example Script

```bash
python example_usage.py
```

This will:
1. Create 2 test leads
2. Generate personalized emails
3. Show quality scores
4. Display analytics

#### Option B: Use the API Directly

```bash
# 1. Create a lead
curl -X POST http://localhost:8000/leads \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "company": "Test Company",
    "job_title": "CTO",
    "linkedin_url": "https://linkedin.com/in/testuser"
  }'

# 2. Generate campaign
curl -X POST http://localhost:8000/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "lead_ids": [1],
    "company_context": "We help companies improve productivity",
    "value_proposition": "Reduce costs by 40%",
    "auto_send": false
  }'

# 3. Check results
curl http://localhost:8000/campaigns
```

---

## Using with Kimi 2.5

### Get Kimi API Key

1. Go to: https://platform.moonshot.cn/
2. Sign up for account
3. Get API key from dashboard
4. Add to `.env`: `KIMI_API_KEY=your_key_here`

### Kimi Model Options

```python
# In config.py, you can use:

# Kimi 2.5 (128k context, best for this use case)
KIMI_MODEL=moonshot-v1-128k  # Default

# Kimi 2.0 (32k context, faster but less powerful)
KIMI_MODEL=moonshot-v1-32k

# Kimi 1.5 (8k context, cheapest)
KIMI_MODEL=moonshot-v1-8k
```

### Expected Kimi API Usage

```
Per lead processed:
- Analysis: ~3,000 tokens input, ~1,000 output
- Email generation: ~2,000 tokens input, ~500 output
Total: ~6,500 tokens per lead

Cost at Kimi pricing (~$0.001 per 1K tokens):
~$0.0065 per lead = ~$6.50 per 1000 leads
```

---

## Production Deployment (Docker)

### Quick Deploy

```bash
# 1. Edit environment
cp .env.example .env
nano .env

# 2. Start everything
docker-compose up -d

# 3. Check status
docker-compose ps

# 4. View logs
docker-compose logs -f app
```

Services started:
- API Server: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- pgAdmin: http://localhost:5050 (optional)

---

## Testing Without API Keys

You can test the basic system structure without external API keys:

```python
# test_mode.py
import asyncio
from models import Lead
from orchestrator import OutreachOrchestrator

# Create mock lead
lead = Lead(
    name="Test User",
    email="test@example.com",
    company="Test Co"
)

# Test workflow (will fail at Kimi call but shows structure)
orchestrator = OutreachOrchestrator(db_session)

# Process lead
try:
    result = await orchestrator.process_lead(
        lead=lead,
        company_context="Test context",
        value_proposition="Test value"
    )
    print(result)
except Exception as e:
    print(f"Expected error without API keys: {e}")
```

---

## Common Issues & Solutions

### Issue: "Cannot connect to database"
```bash
# Check PostgreSQL is running
pg_isready

# Or use SQLite instead
# In config.py: DATABASE_URL=sqlite:///./outreach.db
```

### Issue: "Kimi API authentication failed"
```bash
# Verify your API key
echo $KIMI_API_KEY

# Test directly
curl https://api.moonshot.cn/v1/models \
  -H "Authorization: Bearer $KIMI_API_KEY"
```

### Issue: "ModuleNotFoundError"
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Issue: "Port 8000 already in use"
```bash
# Use different port
uvicorn main:app --host 0.0.0.0 --port 8080

# Or kill existing process
lsof -ti:8000 | xargs kill -9
```

---

## Next Steps

Once running:

1. **Read the docs**: 
   - `README.md` - Full feature overview
   - `ARCHITECTURE.md` - Technical deep dive
   - `DEPLOYMENT.md` - Production deployment

2. **Customize prompts**:
   - Edit `kimi_agent.py` to adjust email style
   - Modify system prompts for your industry

3. **Add data sources**:
   - Configure LinkedIn credentials
   - Add NewsAPI key for better company intel
   - Integrate your CRM

4. **Scale up**:
   - Start with 10-20 leads
   - Monitor quality scores
   - Increase batch sizes gradually

---

## Support

- **Issues**: Create GitHub issue
- **Questions**: Check `README.md` FAQ section
- **Customization**: See `ARCHITECTURE.md`

**Ready to get 15-20% response rates!** 🎯
