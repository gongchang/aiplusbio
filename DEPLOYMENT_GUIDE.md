# AI + Biology Events App - Deployment Guide

This guide will help you deploy your Flask application to Google Cloud Run using Docker.

## Prerequisites

Before you begin, make sure you have the following installed:

1. **Docker** - [Install Docker](https://docs.docker.com/get-docker/)
2. **Google Cloud CLI** - [Install gcloud CLI](https://cloud.google.com/sdk/docs/install)
3. **Google Cloud Account** with billing enabled
4. **OpenAI API Key** (for event categorization)

## Quick Start

### 1. Set Up Google Cloud Project

```bash
# Create a new project (or use existing)
gcloud projects create your-project-id --name="AI Plus Bio Events"

# Set the project
gcloud config set project your-project-id

# Enable billing (required for Cloud Run)
# Go to: https://console.cloud.google.com/billing
```

### 2. Configure Environment Variables

Copy the production configuration template:

```bash
cp config.production.env .env
```

Edit `.env` and update the following values:

```bash
# Required: Your OpenAI API key
OPENAI_API_KEY=sk-your-actual-api-key-here

# Required: Your Google Cloud project ID
GOOGLE_CLOUD_PROJECT=your-project-id

# Optional: Generate a secret key for Flask
SECRET_KEY=your-secret-key-here
```

### 3. Deploy Using the Automated Script

```bash
# Make the script executable (already done)
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

The script will:
- Build your Docker image
- Push it to Google Container Registry
- Deploy to Cloud Run
- Provide you with the service URL

## Manual Deployment Steps

If you prefer to deploy manually:

### 1. Build and Push Docker Image

```bash
# Set your project ID
export PROJECT_ID="your-project-id"

# Build the image
docker build -t gcr.io/$PROJECT_ID/aiplusbio-app .

# Push to Google Container Registry
docker push gcr.io/$PROJECT_ID/aiplusbio-app
```

### 2. Deploy to Cloud Run

```bash
gcloud run deploy aiplusbio-app \
    --image gcr.io/$PROJECT_ID/aiplusbio-app \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300 \
    --concurrency 80 \
    --set-env-vars "FLASK_ENV=production,FLASK_DEBUG=False,PORT=8080"
```

## Local Development with Docker

### Using Docker Compose

```bash
# Start the application
docker-compose up --build

# The app will be available at http://localhost:8080
```

### Using Docker directly

```bash
# Build the image
docker build -t aiplusbio-app .

# Run the container
docker run -p 8080:8080 \
    -v $(pwd)/data:/app/data \
    -e FLASK_ENV=development \
    aiplusbio-app
```

## Environment Variables

### Required Variables

- `OPENAI_API_KEY`: Your OpenAI API key for event categorization
- `GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID

### Optional Variables

- `FLASK_ENV`: Set to `production` for production deployment
- `FLASK_DEBUG`: Set to `False` for production
- `DATABASE_PATH`: Path to SQLite database (default: `/app/data/events.db`)
- `SCRAPING_INTERVAL_HOURS`: How often to scrape events (default: 6)
- `REQUEST_TIMEOUT`: HTTP request timeout in seconds (default: 30)
- `LOG_LEVEL`: Logging level (default: INFO)

## Setting Environment Variables in Cloud Run

### Using gcloud CLI

```bash
gcloud run services update aiplusbio-app \
    --region us-central1 \
    --set-env-vars "OPENAI_API_KEY=your-key-here,FLASK_ENV=production"
```

### Using Google Cloud Console

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click on your service
3. Click "Edit & Deploy New Revision"
4. Go to "Variables & Secrets" tab
5. Add your environment variables

## Managing Secrets

For sensitive data like API keys, use Google Secret Manager:

### 1. Create a Secret

```bash
echo -n "your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-
```

### 2. Grant Access to the Secret

```bash
gcloud secrets add-iam-policy-binding openai-api-key \
    --member="serviceAccount:your-service-account@your-project.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 3. Use the Secret in Cloud Run

```bash
gcloud run services update aiplusbio-app \
    --region us-central1 \
    --set-secrets "OPENAI_API_KEY=openai-api-key:latest"
```

## Monitoring and Logs

### View Logs

```bash
# View recent logs
gcloud run services logs read aiplusbio-app --region us-central1

# Follow logs in real-time
gcloud run services logs tail aiplusbio-app --region us-central1
```

### Monitor Performance

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click on your service
3. View metrics, logs, and traces

## Custom Domain Setup

### 1. Map a Custom Domain

```bash
gcloud run domain-mappings create \
    --service aiplusbio-app \
    --domain your-domain.com \
    --region us-central1
```

### 2. Update DNS Records

Follow the instructions provided by the domain mapping command to update your DNS records.

## Scaling Configuration

### Automatic Scaling

Your app is configured with:
- **Min instances**: 0 (scales to zero when not in use)
- **Max instances**: 10
- **Memory**: 1GB
- **CPU**: 1 vCPU
- **Concurrency**: 80 requests per instance

### Manual Scaling

```bash
gcloud run services update aiplusbio-app \
    --region us-central1 \
    --min-instances 1 \
    --max-instances 20 \
    --memory 2Gi \
    --cpu 2
```

## Troubleshooting

### Common Issues

1. **Build fails**: Check Dockerfile syntax and dependencies
2. **Deployment fails**: Verify project ID and permissions
3. **App doesn't start**: Check environment variables and logs
4. **Database issues**: Ensure data directory is writable

### Debug Commands

```bash
# Check service status
gcloud run services describe aiplusbio-app --region us-central1

# View detailed logs
gcloud run services logs read aiplusbio-app --region us-central1 --limit 100

# Test locally
docker run -p 8080:8080 gcr.io/your-project/aiplusbio-app
```

## Cost Optimization

### Tips to Reduce Costs

1. **Set min instances to 0** (already configured)
2. **Use appropriate memory/CPU** for your workload
3. **Monitor usage** in Google Cloud Console
4. **Set up billing alerts**

### Estimated Costs

- **Free tier**: 2 million requests per month
- **After free tier**: ~$0.40 per million requests
- **Memory/CPU**: ~$0.00002400 per vCPU-second, ~$0.00000250 per GB-second

## Security Best Practices

1. **Use Secret Manager** for API keys
2. **Enable IAM** and least privilege access
3. **Use HTTPS** (automatic with Cloud Run)
4. **Regular updates** of dependencies
5. **Monitor logs** for suspicious activity

## Next Steps

1. **Set up CI/CD** using Cloud Build
2. **Configure monitoring** and alerting
3. **Set up custom domain**
4. **Implement backup strategy** for your database
5. **Add authentication** if needed

## Support

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Docker Documentation](https://docs.docker.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)

For issues specific to this application, check the logs and ensure all environment variables are properly set.






