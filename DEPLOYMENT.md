# HackLaunch AI — Production Deployment Guide

This document contains step-by-step instructions to configure, run, and scale HackLaunch AI in production envs, specifically utilizing Docker Compose and Google Cloud Platform (GCP).

---

## 🛠️ Infrastructure Overview

1. **FastAPI Web Server**: High-performance asynchronous gateway proxying client requests and workflows.
2. **Next.js Web Client**: Production static/dynamic React app served via Node runner.
3. **Nginx Reverse Proxy**: External entrypoint handles TLS termination, rate-limiting (`15r/m`), Gzip compression, and proxying.
4. **Redis Cache Database**: Key-value data cache pool.
5. **Qdrant Vector Database**: Vector storage collection for semantic RAG lookups.
6. **PostgreSQL Database**: Persistent storage for users, events, and GTM package status.

---

## 🐳 Docker Compose Deployment (On-Prem / VM)

To deploy the entire multi-container service stack on a single Virtual Machine (e.g. AWS EC2, Google Compute Engine, or DigitalOcean Droplet):

### 1. Copy variables configuration
Create a production `.env` file inside `backend/`:
```bash
cp backend/.env.example backend/.env
```
Ensure the variables reflect the database credentials, Redis url, and Qdrant endpoints.

### 2. Startup command
Launch the multi-container configuration in the background:
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

### 3. Verify Container healths
Ensure all six containers are running and report as healthy:
```bash
docker ps
```
The FastAPI container exposes a custom health auditing endpoint at `/health` verifying the status of PostgreSQL, Redis, and Qdrant connections.

---

## ☁️ Google Cloud Platform (GCP) Deployment

For serverless, auto-scaling, and secure cloud environments, it is recommended to deploy FastAPI and Next.js onto **Google Cloud Run** and use managed databases:

### 1. Build and Push Containers to Artifact Registry
Configure Artifact Registry and build the container images:
```bash
# Auth gcloud CLI
gcloud auth login
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build & push backend
docker build -t us-central1-docker.pkg.dev/[PROJECT_ID]/hacklaunch/backend:latest ./backend
docker push us-central1-docker.pkg.dev/[PROJECT_ID]/hacklaunch/backend:latest

# Build & push frontend
docker build -t us-central1-docker.pkg.dev/[PROJECT_ID]/hacklaunch/frontend:latest ./frontend
docker push us-central1-docker.pkg.dev/[PROJECT_ID]/hacklaunch/frontend:latest
```

### 2. Deploy Backend Cloud Run Service
Deploy the backend container, setting the production environment variables:
```bash
gcloud run deploy hacklaunch-backend \
  --image us-central1-docker.pkg.dev/[PROJECT_ID]/hacklaunch/backend:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="DATABASE_URL=postgresql+asyncpg://[DB_USER]:[DB_PASSWORD]@[DB_HOST]:5432/[DB_NAME],REDIS_URL=redis://[REDIS_HOST]:6379/0,QDRANT_URL=https://[QDRANT_HOST],GEMINI_API_KEY=[API_KEY]"
```

### 3. Deploy Frontend Cloud Run Service
Deploy the Next.js container, pointing `NEXT_PUBLIC_API_URL` to the live Cloud Run backend URL:
```bash
gcloud run deploy hacklaunch-frontend \
  --image us-central1-docker.pkg.dev/[PROJECT_ID]/hacklaunch/frontend:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="NEXT_PUBLIC_API_URL=https://[BACKEND_URL_HERE]/api/v1"
```

---

## 📈 Logging, Monitoring, & Security

### 1. Structured Logging
In production (`APP_ENV=production`), the backend logs are written in a structured formats suitable for ingestion by Cloud Logging (Google Cloud Operations Suite / Stackdriver), Datadog, or ELK stacks.

### 2. API Throttling
Nginx is preconfigured with a rate limiting zone allocating `15 requests per minute` with burst allowances of up to 5 requests to protect against denial-of-service attempts.

### 3. Caching Latencies
All RAG context compilations and previous queries utilize the Redis cache to maintain sub-100ms response cycles.
