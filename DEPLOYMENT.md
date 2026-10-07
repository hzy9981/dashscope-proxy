# Production Deployment Guide for graceful-tenure-298505

## 1. Prerequisites
1.  **GCS Configuration**: Ensure `config.json` exists in `gs://graceful-tenure-298505_cloudbuild/config.json`.
2.  **IAM Permissions**:
    -   Cloud Run service account needs `roles/aiplatform.customJobAdmin`.
    -   Cloud Run service account needs `roles/storage.objectUser`.

## 2. Build, Push, & Deploy
Execute these commands in the `dashscope-proxy` directory:

```bash
# 1. Build the container image
docker build -t gcr.io/graceful-tenure-298505/dashscope-proxy .

# 2. Push to Google Container Registry
docker push gcr.io/graceful-tenure-298505/dashscope-proxy

# 3. Deploy to Cloud Run
gcloud run deploy dashscope-proxy \
  --image gcr.io/graceful-tenure-298505/dashscope-proxy \
  --platform managed \
  --region us-central1 \
  --set-secrets DASHSCOPE_API_KEY=DASHSCOPE_API_KEY:latest \
  --allow-unauthenticated
```

## 3. Post-Deployment
- After deployment, you will receive a `Service URL`.
- Access your tool at: `https://[SERVICE_URL]/`
- Your data will persist at: `gs://graceful-tenure-298505_cloudbuild/feedback.csv`
