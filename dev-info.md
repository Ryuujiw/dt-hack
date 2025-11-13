# Setup guide

## Run Docker container

Ensure that docker desktop is installed.

Change directory to location of notebook file and run:

For Windows

```
docker run --rm -it -p 8888:8888 -v "%cd%":/home/jovyan/work gboeing/osmnx:latest
```

For Linux

```
docker run --rm -it -p 8888:8888 -v "$PWD":/home/jovyan/work gboeing/osmnx:latest
```

## Run bash

For Windows

```
docker run --rm -it -v "%cd%":/home/jovyan/work gboeing/osmnx:latest /bin/bash
```

For Linux

```
docker run --rm -it -v "$PWD":/home/jovyan/work gboeing/osmnx:latest /bin/bash
```

## Reference

- Github with full examples: https://github.com/gboeing/osmnx-examples
- Docker container: https://hub.docker.com/r/gboeing/osmnx

## 🚀 Quick Deployment of ReLeaf Agent

### Prerequisites
1. A Google Cloud account with billing enabled
- Launch Google Cloud Console
- Create new project and select the project
- Menu > Billing, link to a billing account

2. `gcloud` CLI installed and authenticated
- Run `sudo snap install google-cloud-cli --classic` to install gcloud cli
- Run `gcloud auth login` in wsl
- Open the link in browser and authenticate yourself
- Get your Project ID from the console

### Deploy in 2 Steps

1. **Set your project:**
```bash
export PROJECT_ID="us-con-gcp-sbx-0001190-100925"
gcloud config set project $PROJECT_ID
```

2. **Run deployment:**
```bash
chmod +x ./agent_deployment.bash
./agent_deployment.bash
```

4. run `gcloud beta run services proxy releaf-agent --port=8080 --region=us-central1` 
   in gcloud console.

3. Click the proxied link to launch the Agent in your browser and start chatting!
