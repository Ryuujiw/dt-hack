# 🌿 ReLeaf Agent - AI-Powered Zoo Conservation Guide

An intelligent zoo guide agent that combines real-time zoo animal data with conservation knowledge, deployed on Google Cloud Run using the Model Context Protocol (MCP).

## 🚀 Quick Deployment

### Prerequisites
- Google Cloud account with billing enabled
- `gcloud` CLI installed and configured

### Deploy in 2 Steps

1. **Set your project:**
```bash
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID
```

2. **Run deployment:**
```bash
chmod +x deployment.bash
./deployment.bash
```

That's it! Your agent will be available at: `https://releaf-agent-[PROJECT_NUMBER].us-central1.run.app`

## 🎯 Features

- **Real-time Zoo Data**: Animal locations, ages, weights, and habitats
- **Conservation Knowledge**: Endangered species info and conservation efforts  
- **Interactive Chat**: Natural conversation about animals and conservation
- **Public Access**: No authentication required - share the URL with anyone

## 📖 Usage Examples

- "Where can I find the polar bears?"
- "Tell me about conservation efforts for elephants"  
- "What endangered species do you have?"
- "Show me all the animals in the African Savanna"
