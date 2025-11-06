#!/bin/bash

# AI + Biology Events App - Google Cloud Run Deployment Script
# This script helps you deploy your Flask app to Google Cloud Run

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=""
REGION="us-central1"
SERVICE_NAME="aiplusbio-app"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo -e "${BLUE}🚀 AI + Biology Events App - Google Cloud Run Deployment${NC}"
echo "=================================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud CLI is not installed.${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed.${NC}"
    echo "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Get project ID if not set
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}📋 Please enter your Google Cloud Project ID:${NC}"
    read -p "Project ID: " PROJECT_ID
    
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}❌ Project ID cannot be empty.${NC}"
        exit 1
    fi
fi

# Set the project
echo -e "${BLUE}🔧 Setting Google Cloud project to: $PROJECT_ID${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${BLUE}🔧 Enabling required Google Cloud APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Configure Docker to use gcloud as a credential helper
echo -e "${BLUE}🔧 Configuring Docker authentication...${NC}"
gcloud auth configure-docker

# Build the Docker image
echo -e "${BLUE}🏗️  Building Docker image...${NC}"
docker build -t $IMAGE_NAME .

# Push the image to Google Container Registry
echo -e "${BLUE}📤 Pushing image to Google Container Registry...${NC}"
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo -e "${BLUE}🚀 Deploying to Google Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
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

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Your app is available at: $SERVICE_URL${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Update your environment variables in the Google Cloud Console"
echo "2. Set up your OpenAI API key as a secret"
echo "3. Configure your domain (optional)"
echo ""
echo -e "${BLUE}🔧 To update environment variables:${NC}"
echo "gcloud run services update $SERVICE_NAME --region=$REGION --set-env-vars KEY=VALUE"
echo ""
echo -e "${BLUE}📊 To view logs:${NC}"
echo "gcloud run services logs read $SERVICE_NAME --region=$REGION"







