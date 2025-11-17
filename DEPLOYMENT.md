# Deployment Guide

This guide covers deploying the QA-with-evidence system in production environments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisites

### System Requirements

**Minimum**:
- CPU: 2 cores
- RAM: 2GB
- Storage: 1GB
- OS: Linux, macOS, or Windows with Docker

**Recommended**:
- CPU: 4 cores
- RAM: 4GB
- Storage: 5GB
- OS: Linux (Ubuntu 20.04+)

### Software Dependencies

- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 2.0+ (for orchestration)
- **Python**: 3.11+ (for local development)
- **Git**: 2.30+ (for version control)

### Installation

```bash
# Install Docker (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Install Docker (macOS)
brew install --cask docker

# Verify installation
docker --version
docker-compose --version
```

---

## 2. Local Development

### Setup Virtual Environment

```bash
# Clone repository
git clone <repository-url>
cd qa-with-evidence

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -U pip wheel
pip install -r requirements.txt
```

### Run Pipeline Locally

```bash
# Complete pipeline
make all

# Or step by step:
make ingest    # Process corpus
make index     # Build embeddings
make batch     # Run questions
make eval      # Evaluate results

# Test single question
python -m src.cli answer --q "What soil pH is recommended for canola?"
```

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific test
pytest tests/test_offsets.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 3. Docker Deployment

### Quick Start

```bash
# 1. Build Docker image
docker-compose build

# 2. Run complete pipeline
docker-compose run --rm qa-with-evidence make all

# 3. Check results
ls -lh artifacts/
```

### Step-by-Step Deployment

#### Build Image

```bash
# Build with docker-compose
docker-compose build

# Or build directly with Docker
docker build -t qa-with-evidence:latest .

# Verify image
docker images | grep qa-with-evidence
```

#### Run Ingestion

```bash
docker-compose run --rm qa-with-evidence \
  python -m src.cli ingest \
  --in data/corpus_raw \
  --out artifacts/sentences.jsonl
```

Expected output:
```
Ingesting corpus from data/corpus_raw
✓ Ingested 1847 sentences to artifacts/sentences.jsonl
Enriching tags...
✓ Tags enriched
Verifying offsets...
✓ Sampled 200/1847 sentences: 100% correct offsets
```

#### Build Index

```bash
docker-compose run --rm qa-with-evidence \
  python -m src.cli build-index \
  --sentences artifacts/sentences.jsonl
```

Expected output:
```
Building index...
✓ Index built: 1847 sentences, dim=384
```

#### Run Batch Questions

```bash
docker-compose run --rm qa-with-evidence \
  python -m src.cli batch \
  --questions data/questions.txt \
  --out artifacts/run.jsonl
```

Expected output:
```
Processing 22 questions...
[████████████████████████████████] 22/22 (100%)
✓ Batch complete: 22 questions → artifacts/run.jsonl
```

#### Evaluate Results

```bash
docker-compose run --rm qa-with-evidence \
  python -m src.cli eval \
  --run artifacts/run.jsonl
```

Expected output:
```
Answer Rate: 75.0% (15/20 answered, 5 abstained)
Redundancy Reduction: 52.3% (0.65 → 0.31)
Coverage Diversity: 8.2 unique crop×practice pairs per answer
Offset Verification: 100% correct (45/45 citations)
```

### Production Container Setup

#### Using Docker Compose (Recommended)

```bash
# Start service in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Execute commands
docker-compose exec qa-with-evidence python -m src.cli answer --q "What is canola?"

# Stop service
docker-compose down
```

#### Using Docker Directly

```bash
# Run with volume mounts
docker run -it --rm \
  -v $(pwd)/artifacts:/app/artifacts \
  -v $(pwd)/data:/app/data:ro \
  --name qa-with-evidence \
  qa-with-evidence:latest \
  python -m src.cli batch

# Interactive shell
docker run -it --rm \
  -v $(pwd)/artifacts:/app/artifacts \
  qa-with-evidence:latest \
  /bin/bash
```

### Resource Configuration

Edit `docker-compose.yml` to adjust resources:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'      # Max CPU cores
      memory: 4G       # Max RAM
    reservations:
      cpus: '2.0'      # Guaranteed CPU
      memory: 2G       # Guaranteed RAM
```

---

## 4. Cloud Deployment

### AWS EC2

#### 1. Launch Instance

```bash
# Launch Ubuntu 20.04 instance
# Instance type: t3.medium (2 vCPU, 4GB RAM) or larger
# Security group: Allow SSH (22)
# Storage: 10GB EBS
```

#### 2. Install Docker

```bash
# SSH into instance
ssh ubuntu@<instance-ip>

# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker ubuntu
newgrp docker
```

#### 3. Deploy Application

```bash
# Clone repository
git clone <repository-url>
cd qa-with-evidence

# Build and run
docker-compose build
docker-compose run --rm qa-with-evidence make all

# Check results
ls -lh artifacts/
```

#### 4. Schedule Batch Jobs (Optional)

```bash
# Create cron job for daily processing
crontab -e

# Add line (runs daily at 2 AM):
0 2 * * * cd /home/ubuntu/qa-with-evidence && docker-compose run --rm qa-with-evidence make batch
```

### AWS ECS (Elastic Container Service)

#### 1. Push Image to ECR

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag image
docker tag qa-with-evidence:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/qa-with-evidence:latest

# Push image
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/qa-with-evidence:latest
```

#### 2. Create Task Definition

```json
{
  "family": "qa-with-evidence",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "qa-container",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/qa-with-evidence:latest",
      "command": ["python", "-m", "src.cli", "batch"],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/qa-with-evidence",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### 3. Run Task

```bash
# Run as one-time task
aws ecs run-task \
  --cluster qa-cluster \
  --task-definition qa-with-evidence \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"
```

### GCP Cloud Run Jobs

#### 1. Build and Push Image

```bash
# Set project
gcloud config set project <project-id>

# Build with Cloud Build
gcloud builds submit --tag gcr.io/<project-id>/qa-with-evidence

# Or push local image
docker tag qa-with-evidence:latest gcr.io/<project-id>/qa-with-evidence:latest
docker push gcr.io/<project-id>/qa-with-evidence:latest
```

#### 2. Create Cloud Run Job

```bash
gcloud run jobs create qa-batch \
  --image gcr.io/<project-id>/qa-with-evidence:latest \
  --region us-central1 \
  --memory 4Gi \
  --cpu 4 \
  --max-retries 3 \
  --command "python" \
  --args "-m,src.cli,batch"
```

#### 3. Execute Job

```bash
# Manual execution
gcloud run jobs execute qa-batch --region us-central1

# Schedule with Cloud Scheduler (daily at 2 AM)
gcloud scheduler jobs create http qa-daily \
  --location us-central1 \
  --schedule "0 2 * * *" \
  --uri "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/<project-id>/jobs/qa-batch:run" \
  --http-method POST \
  --oauth-service-account-email <service-account>@<project-id>.iam.gserviceaccount.com
```

### Kubernetes

#### 1. Create Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qa-with-evidence
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: qa-with-evidence
  template:
    metadata:
      labels:
        app: qa-with-evidence
    spec:
      containers:
      - name: qa
        image: qa-with-evidence:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "2"
          limits:
            memory: "4Gi"
            cpu: "4"
        volumeMounts:
        - name: artifacts
          mountPath: /app/artifacts
        - name: data
          mountPath: /app/data
          readOnly: true
      volumes:
      - name: artifacts
        persistentVolumeClaim:
          claimName: qa-artifacts-pvc
      - name: data
        configMap:
          name: qa-corpus-data
```

#### 2. Create PVC for Artifacts

```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: qa-artifacts-pvc
  namespace: production
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
```

#### 3. Deploy

```bash
kubectl apply -f pvc.yaml
kubectl apply -f deployment.yaml

# Check status
kubectl get pods -n production
kubectl logs -f <pod-name> -n production
```

---

## 5. Monitoring & Maintenance

### Health Checks

```bash
# Docker health check
docker inspect --format='{{.State.Health.Status}}' qa-with-evidence

# Manual health check
docker-compose exec qa-with-evidence python -c "import src; print('OK')"
```

### Logging

```bash
# View container logs
docker-compose logs -f

# View specific command logs
docker-compose run --rm qa-with-evidence python -m src.cli batch 2>&1 | tee batch.log
```

### Metrics Collection

Create `metrics.py` for Prometheus integration (future enhancement):

```python
from prometheus_client import Counter, Histogram, start_http_server

# Define metrics
questions_total = Counter('qa_questions_total', 'Total questions processed')
questions_answered = Counter('qa_questions_answered', 'Questions answered')
questions_abstained = Counter('qa_questions_abstained', 'Questions abstained')
processing_time = Histogram('qa_processing_seconds', 'Processing time per question')

# Start metrics server
start_http_server(8000)
```

### Backup & Recovery

```bash
# Backup artifacts
tar -czf artifacts-backup-$(date +%Y%m%d).tar.gz artifacts/

# Copy to S3
aws s3 cp artifacts-backup-20250117.tar.gz s3://my-bucket/backups/

# Restore from backup
tar -xzf artifacts-backup-20250117.tar.gz
```

### Updating Corpus

```bash
# Add new documents to data/corpus_raw/
cp new_document.md data/corpus_raw/wheat/

# Rebuild index
docker-compose run --rm qa-with-evidence make ingest
docker-compose run --rm qa-with-evidence make index

# Verify
docker-compose run --rm qa-with-evidence python -m src.cli retrieve --q "test query" --k 5
```

---

## 6. Troubleshooting

### Issue: Container Build Fails

**Symptoms**:
```
ERROR: failed to solve: process "/bin/sh -c pip install -r requirements.txt" did not complete successfully
```

**Solutions**:
1. Check internet connectivity
2. Use `--no-cache` flag:
   ```bash
   docker-compose build --no-cache
   ```
3. Update base image:
   ```dockerfile
   FROM python:3.11-slim
   ```

### Issue: Out of Memory

**Symptoms**:
```
Killed
```

**Solutions**:
1. Increase Docker memory limit:
   ```bash
   # Docker Desktop: Settings → Resources → Memory → 4GB+
   ```
2. Reduce batch size in config.yaml
3. Use smaller embedding model

### Issue: Slow Inference

**Symptoms**:
- Query time > 5 seconds per question

**Solutions**:
1. Enable CPU optimization:
   ```yaml
   # docker-compose.yml
   environment:
     - OMP_NUM_THREADS=4
     - MKL_NUM_THREADS=4
   ```
2. Build FAISS with optimizations:
   ```bash
   pip install faiss-cpu --no-binary faiss-cpu
   ```
3. Consider GPU deployment for large corpora

### Issue: Offset Verification Fails

**Symptoms**:
```
❌ Offset mismatch: expected "...", got "..."
```

**Solutions**:
1. Check file encoding (must be UTF-8):
   ```bash
   file -i data/corpus_raw/**/*.md
   ```
2. Verify no text preprocessing is applied
3. Re-run ingestion:
   ```bash
   make clean
   make ingest
   ```

### Issue: Low Answer Rate

**Symptoms**:
- < 50% of questions answered

**Solutions**:
1. Lower abstention threshold:
   ```yaml
   # config.yaml
   selection:
     abstain_score_thresh: 0.28  # Lower from 0.35
   ```
2. Check corpus coverage:
   ```bash
   python -m src.cli retrieve --q "sample question" --k 20
   ```
3. Inspect abstention reasons in `run.jsonl`:
   ```bash
   jq '.run_notes.decision' artifacts/run.jsonl
   ```

### Issue: High Redundancy

**Symptoms**:
- Final answers contain repetitive sentences

**Solutions**:
1. Increase similarity threshold:
   ```yaml
   # config.yaml
   selection:
     max_sim_threshold: 0.88  # Increase from 0.82
   ```
2. Adjust MMR lambda:
   ```yaml
   selection:
     mmr_lambda: 0.60  # More diversity (down from 0.70)
   ```

---

## Performance Benchmarks

### Corpus: 29 docs, ~2000 sentences

| Operation | Time (CPU) | Time (GPU) |
|-----------|-----------|------------|
| Ingestion | 5s | N/A |
| Index Build | 30s | 10s |
| Single Query | 400ms | 150ms |
| Batch (22 questions) | 10s | 4s |

### Resource Usage

| Stage | CPU | RAM | Storage |
|-------|-----|-----|---------|
| Ingestion | < 50% | 200MB | 2MB |
| Index Build | 90% | 800MB | 100MB |
| Query | 60% | 500MB | 100MB |

---

## Security Best Practices

1. **Use Read-Only Mounts**:
   ```yaml
   volumes:
     - ./data:/app/data:ro  # Read-only
   ```

2. **Run as Non-Root User**:
   ```dockerfile
   RUN useradd -m -u 1000 qauser
   USER qauser
   ```

3. **Scan Images for Vulnerabilities**:
   ```bash
   docker scan qa-with-evidence:latest
   ```

4. **Use Secrets for API Keys** (if needed):
   ```bash
   docker-compose run --rm \
     -e API_KEY_FILE=/run/secrets/api_key \
     qa-with-evidence
   ```

---

## Next Steps

1. ✅ Deploy using Docker Compose locally
2. ✅ Test with sample questions
3. ✅ Verify results and metrics
4. 🔄 Deploy to cloud (AWS/GCP/Azure)
5. 🔄 Set up monitoring and alerts
6. 🔄 Schedule automated batch processing

---

**For technical architecture details, see** `ARCHITECTURE.md`  
**For usage instructions, see** `README.md`  
**For implementation details, see** `IMPLEMENTATION_SUMMARY.md`

