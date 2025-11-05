# Setting up Google Cloud Secrets for GitHub Actions

## Step 1: Create a Service Account in Google Cloud

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **IAM & Admin** → **Service Accounts**
3. Click **Create Service Account**
4. Fill in the details:
   - **Name**: `github-actions-deployer`
   - **Description**: `Service account for GitHub Actions deployment`
5. Click **Create and Continue**

## Step 2: Grant Required Permissions

Add these roles to your service account:
- **Cloud Run Admin** (`roles/run.admin`)
- **Service Account User** (`roles/iam.serviceAccountUser`)
- **Artifact Registry Admin** (`roles/artifactregistry.admin`)
- **Cloud Build Editor** (`roles/cloudbuild.builds.editor`)

## Step 3: Create and Download Key

1. Click on the created service account
2. Go to **Keys** tab
3. Click **Add Key** → **Create new key**
4. Select **JSON** format
5. Click **Create** - this will download a JSON file

## Step 4: Add Secrets to GitHub

### Navigate to Repository Secrets:
1. Go to: https://github.com/Ryuujiw/dt-hack
2. Click **Settings** tab
3. Left sidebar: **Secrets and variables** → **Actions**
4. Click **New repository secret**

### Add These Secrets:

#### Secret 1: GCP_PROJECT_ID
- **Name**: `GCP_PROJECT_ID`
- **Value**: Your Google Cloud project ID (found in the JSON file or GCP console)

#### Secret 2: GCP_SA_KEY  
- **Name**: `GCP_SA_KEY`
- **Value**: The entire content of the downloaded JSON file, including the outer braces

Example JSON structure (don't use these values):
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "github-actions-deployer@your-project-id.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/github-actions-deployer%40your-project-id.iam.gserviceaccount.com"
}
```
