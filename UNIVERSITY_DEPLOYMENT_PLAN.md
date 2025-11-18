# GSU CS Chatbot - University Server Integration Plan

## 🏗️ Recommended Production Architecture

### **Option 1: University Web Server Integration (Recommended)**
```
Students → cs.gsu.edu/chatbot → University Web Server → Flask App
                                      ↓
                            Docker Container/VM → Ollama GPU Server
                                      ↓
                            Persistent Cache → Daily Refresh Cron Job
```

### **Option 2: Dedicated AI Server**
```
Students → ai.cs.gsu.edu → Dedicated AI Server → Multiple AI Services
                                ↓
                          GSU Chatbot Container → Vector Database
                                ↓
                          Shared GPU Resources → Multiple Models
```

### **Option 3: Integration with Existing LMS**
```
Students → Brightspace/Canvas → Embedded Widget → University API Gateway
                                      ↓
                                GSU Chatbot Service
```

## 🔧 Technical Migration Steps

### **Phase 1: Containerization (Week 1)**
1. **Create Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

ENV FLASK_ENV=production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

2. **Create docker-compose.yml**:
```yaml
version: '3.8'
services:
  chatbot:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - FLASK_ENV=production
      - OLLAMA_HOST=ollama
    depends_on:
      - ollama
  
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  ollama_data:
```

### **Phase 2: University Server Deployment (Week 2)**

**Step 1: Server Setup**
```bash
# On university server (as admin)
sudo docker-compose up -d
sudo systemctl enable docker
```

**Step 2: Network Configuration**
```nginx
# /etc/nginx/sites-available/gsu-chatbot
server {
    listen 80;
    server_name cs.gsu.edu;
    
    location /chatbot {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Step 3: SSL/Security**
```bash
sudo certbot --nginx -d cs.gsu.edu
```

### **Phase 3: Production Configuration**

**Environment Variables**:
```bash
# /app/.env
FLASK_ENV=production
OLLAMA_HOST=ollama
CACHE_DIR=/app/data
LOG_LEVEL=INFO
MAX_CACHE_SIZE=1GB
REFRESH_SCHEDULE="0 3 * * *"  # 3 AM daily
```

**Production Flask Config**:
```python
# config/production.py
import os

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'localhost')
    CACHE_DIR = os.environ.get('CACHE_DIR', '/app/data')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Security settings
    WTF_CSRF_ENABLED = True
    SSL_REQUIRED = True
    
    # Performance settings  
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    SEND_FILE_MAX_AGE_DEFAULT = 31536000   # 1 year cache
```

### **Phase 4: University Integration Points**

**Authentication Integration**:
```python
# Add GSU SSO integration
from flask_login import LoginManager
from gsu_sso import GSUAuthentication

@app.before_request
def require_gsu_auth():
    if not current_user.is_authenticated:
        return redirect('/sso/login')
```

**Database Integration**:
```python
# Connect to university MySQL/PostgreSQL
from sqlalchemy import create_engine
engine = create_engine('postgresql://chatbot:password@db.gsu.edu:5432/chatbot_db')
```

**Logging Integration**:
```python
# Send logs to university log aggregation
import syslog
logger.addHandler(syslog.SysLogHandler(address=('logs.gsu.edu', 514)))
```

## ⚡ Scheduler Migration for Production

### **Current Issue: Windows Task Scheduler → Linux Cron**

**Local (Windows):**
```batch
# Windows Task Scheduler runs run_refresh.bat
python refresh_scheduler.py
```

**Production (Linux Server):**
```bash
# /etc/cron.d/gsu-chatbot-refresh
0 3 * * * chatbot /usr/bin/docker exec gsu-chatbot python /app/refresh_scheduler.py
```

### **Enhanced Production Scheduler**

**Container-Aware Refresh**:
```python
# refresh_scheduler.py (Production version)
import docker

def scheduled_refresh():
    """Run refresh inside the container"""
    client = docker.from_env()
    container = client.containers.get('gsu-chatbot')
    
    result = container.exec_run([
        'python', '/app/document_processor.py', '--refresh'
    ])
    
    return result.exit_code == 0
```

**Kubernetes CronJob** (if using K8s):
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: chatbot-refresh
spec:
  schedule: "0 3 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: refresh
            image: gsu/chatbot:latest
            command: ["python", "/app/refresh_scheduler.py"]
          restartPolicy: OnFailure
```

## 📊 University Integration Benefits

### **For Students**:
- ✅ Single Sign-On (GSU credentials)
- ✅ Integration with student portal
- ✅ Always available (99.9% uptime)
- ✅ Fast responses (dedicated server)

### **For University**:
- ✅ Centralized management and monitoring
- ✅ Cost-effective (one server, many students)
- ✅ Data security and compliance
- ✅ Integration with existing IT infrastructure

### **For You**:
- ✅ Professional deployment experience
- ✅ Scalable architecture
- ✅ Production monitoring and logging
- ✅ Real-world impact measurement

## 🎯 Immediate Next Steps

1. **Contact GSU IT Department**:
   - Request meeting about chatbot deployment
   - Discuss server resources and requirements
   - Get approval for GPU usage (for Ollama)

2. **Prepare Demo Package**:
   - Docker container with your current app
   - Demo video showing functionality
   - Technical documentation

3. **Address University Requirements**:
   - Security review and approval
   - Data privacy compliance
   - User authentication integration
   - Monitoring and logging setup

## 💰 Cost Considerations

**GPU Server Requirements**:
- **Minimum**: 1x RTX 4090 (24GB VRAM) - $1,600
- **Recommended**: 2x RTX A6000 (48GB VRAM) - $8,000
- **Alternative**: Cloud GPU instances (AWS/GCP)

**Operating Costs**:
- **Power**: ~$100/month for dedicated GPU server
- **Maintenance**: Minimal (Docker containers)
- **Updates**: Automated via CI/CD pipeline

The university likely already has GPU servers for research that could host this!