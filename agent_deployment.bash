#!/bin/bash

set -e  # Exit on any error

echo "🌿 Starting ReLeaf Agent Deployment..."

# Set up environment variables
export PROJECT_ID=$(gcloud config get-value project)
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
export SA_NAME=releaf-service
export SERVICE_ACCOUNT="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
export REGION=us-central1

# Retrieve Google Maps API Key from Secret Manager
echo "🔐 Retrieving Google Maps API Key from Secret Manager..."
export GOOGLE_MAPS_API_KEY=$(gcloud secrets versions access latest --secret="google-maps-api-key" 2>/dev/null || echo "")

if [ -z "$GOOGLE_MAPS_API_KEY" ]; then
    echo "⚠️  Warning: Google Maps API Key not found in Secret Manager."
    exit 1
fi

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
    #     compute.googleapis.com \
    #     secretmanager.googleapis.com

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

    # # Grant access to Secret Manager for Google Maps API key
    # gcloud projects add-iam-policy-binding $PROJECT_ID \
    #     --member="serviceAccount:$SERVICE_ACCOUNT" \
    #     --role="roles/secretmanager.secretAccessor" \
    #     --quiet

# Deploy MCP Server
echo "🔌 Deploying ReLeaf MCP Server..."
DEPLOY_ARGS="--source ./ReLeaf_Agent/mcp --region=$REGION --quiet"

# Add Google Maps API key if available
if [ ! -z "$GOOGLE_MAPS_API_KEY" ]; then
    DEPLOY_ARGS="$DEPLOY_ARGS --set-env-vars=GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_API_KEY"
fi

gcloud run deploy releaf-mcp-server $DEPLOY_ARGS

# Get MCP Server URL
MCP_URL="https://releaf-mcp-server-${PROJECT_NUMBER}.${REGION}.run.app/mcp/"
echo "✅ MCP Server deployed at: $MCP_URL"

# Update agent configuration
echo "⚙️  Configuring ReLeaf Agent..."
cat > ./ReLeaf_Agent/.env << EOF
MODEL="gemini-2.5-flash"
MCP_SERVER_URL=$MCP_URL
EOF

# Add Google Maps API key to agent environment if available
if [ ! -z "$GOOGLE_MAPS_API_KEY" ]; then
    echo "GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_API_KEY" >> ./ReLeaf_Agent/.env
fi

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
    --service-account=$SERVICE_ACCOUNT 

echo ""
echo "🎉 Deployment Complete!"
echo "🔌 MCP Server: https://releaf-mcp-server-${PROJECT_NUMBER}.${REGION}.run.app/mcp/"
echo "🤖 Agent: https://releaf-agent-${PROJECT_NUMBER}.${REGION}.run.app"
echo ""
