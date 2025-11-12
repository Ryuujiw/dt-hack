#!/bin/bash

set -e  # Exit on any error

echo "🌿 Starting ReLeaf Agent Deployment..."

# Set up environment variables
export PROJECT_ID=$(gcloud config get-value project)
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
export SA_NAME=releaf-service
export SERVICE_ACCOUNT="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
export REGION=us-central1

echo "📋 Project: $PROJECT_ID"
echo "📋 Project Number: $PROJECT_NUMBER"
echo "📋 Service Account: $SERVICE_ACCOUNT"

# Done
    # # Enable required APIs
    # echo "🔧 Enabling Google Cloud APIs..."
    # gcloud services enable \
    #     run.googleapis.com \
    #     artifactregistry.googleapis.com \
    #     cloudbuild.googleapis.com \
    #     aiplatform.googleapis.com \
    #     compute.googleapis.com

    # # Create service account
    # echo "👤 Creating service account..."
    # gcloud iam service-accounts create ${SA_NAME} \
    #     --display-name="ReLeaf Service Account" \
    #     --quiet || echo "Service account already exists"


    # # Set permissions
    # echo "🔐 Setting up permissions..."
    # gcloud projects add-iam-policy-binding $PROJECT_ID \
    #     --member="serviceAccount:$SERVICE_ACCOUNT" \
    #     --role="roles/run.invoker" \
    #     --quiet

    # gcloud projects add-iam-policy-binding $PROJECT_ID \
    #     --member="serviceAccount:$SERVICE_ACCOUNT" \
    #     --role="roles/aiplatform.user" \
    #     --quiet

# Deploy MCP Server
echo "🔌 Deploying ReLeaf MCP Server..."
gcloud run deploy releaf-mcp-server \
    --source ./ReLeaf_Agent/mcp \
    --region=$REGION \
    --allow-unauthenticated \
    --quiet

# Get MCP Server URL
MCP_URL="https://releaf-mcp-server-${PROJECT_NUMBER}.${REGION}.run.app/mcp/"
echo "✅ MCP Server deployed at: $MCP_URL"

# Update agent configuration
echo "⚙️  Configuring ReLeaf Agent..."
cat > ./ReLeaf_Agent/.env << EOF
MODEL="gemini-2.5-flash"
MCP_SERVER_URL=$MCP_URL
EOF

# Deploy ReLeaf Agent
echo "🤖 Deploying ReLeaf Agent..."
uvx --from google-adk adk deploy cloud_run \
    --project=$PROJECT_ID \
    --region=$REGION \
    --service_name=releaf-agent \
    --with_ui \
    ./ReLeaf_Agent \
    -- \
    --labels=app=releaf-agent \
    --service-account=$SERVICE_ACCOUNT \
    --allow-unauthenticated

echo ""
echo "🎉 Deployment Complete!"
echo "🔌 MCP Server: https://releaf-mcp-server-${PROJECT_NUMBER}.${REGION}.run.app/mcp/"
echo "🤖 Agent: https://releaf-agent-${PROJECT_NUMBER}.${REGION}.run.app"
echo ""
