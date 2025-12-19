# Tutorial: Deploying to Google Cloud Run

This tutorial will guide you through deploying your FastAPI application as a Docker container to Google Cloud Run. We'll cover everything from setting up your Google Cloud project to troubleshooting common deployment issues.

## Prerequisites

Before you begin, make sure you have the following:

1.  **GCP Account:** You need a Google Cloud Platform account with billing enabled. You can create one at [https://cloud.google.com/](https://cloud.google.com/).
2.  **`gcloud` CLI:** Install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) (also known as the `gcloud` SDK). This tool allows you to interact with your GCP account from your terminal.
3.  **Authenticate `gcloud`:** After installing, authenticate the CLI with your GCP account by running:
    ```bash
    gcloud auth login
    ```
4.  **Docker:** Docker must be installed and running on your local machine. This is used to build your application into a container. You can download it from the [Docker website](https://www.docker.com/get-started).

## Part 1: GCP Project Setup

First, we'll set up a project in Google Cloud to house all of our resources.

1.  **Create a GCP Project:**
    Go to the [GCP Console](https://console.cloud.google.com/projectcreate) and create a new project. Give it a descriptive name, like `legendary-potato`. Once created, take note of your **Project ID**. You can find this on your project's dashboard.

2.  **Set Your Project:**
    Tell the `gcloud` CLI which project you want to work on. Replace `<YOUR_PROJECT_ID>` with your actual Project ID and run:
    ```bash
    gcloud config set project <YOUR_PROJECT_ID>
    ```

3.  **Enable APIs:**
    Your project needs to have certain Google Cloud services (APIs) enabled to work with Cloud Run, Secret Manager, and other tools. This command enables all the necessary APIs at once:
    ```bash
    gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
    ```
    This may take a few moments to complete.

## Part 2: Storing Secrets with Secret Manager

You should never hard-code sensitive information like API keys or database passwords directly in your code. **Google Secret Manager** is a secure service for storing and managing such secrets.

1.  **Create Secrets:**
    We'll create secrets for each of the sensitive environment variables our application needs.
    ```bash
    # Google Client ID
    echo -n "<YOUR_GOOGLE_CLIENT_ID>" | gcloud secrets create "google-client-id" --data-file=-

    # Google Client Secret
    echo -n "<YOUR_GOOGLE_CLIENT_SECRET>" | gcloud secrets create "google-client-secret" --data-file=-

    # Starlette Session Key
    echo -n "<YOUR_STARLET_SECRET_KEY>" | gcloud secrets create "starlette-session-key" --data-file=-
    ```

2.  **Troubleshooting: Secret Already Exists**
    If you run one of these commands and see an error like `ALREADY_EXISTS`, it simply means you've created that secret before. This is not a problem, and you can safely move on to the next step.

## Part 3: Building and Pushing the Docker Image

Next, we will package our application into a Docker image and push it to **Google Artifact Registry**, which is a private Docker image repository.

1.  **Create an Artifact Registry Repository:**
    Choose a region for your repository (e.g., `us-central1`) and run:
    ```bash
    gcloud artifacts repositories create legendary-potato-repo --repository-format=docker --location=<YOUR_REGION>
    ```

2.  **Configure Docker:**
    This command configures your local Docker client to authenticate with your new repository in Artifact Registry, allowing you to push images to it.
    ```bash
    gcloud auth configure-docker <YOUR_REGION>-docker.pkg.dev
    ```

3.  **Build and Tag the Image:**
    Build your Docker image and tag it with the full path to your Artifact Registry repository.
    ```bash
    docker build -t legendary-potato .
    docker tag legendary-potato <YOUR_REGION>-docker.pkg.dev/<YOUR_PROJECT_ID>/legendary-potato-repo/legendary-potato:latest
    ```

4.  **Push the Image:**
    Push the tagged image to Artifact Registry:
    ```bash
    docker push <YOUR_REGION>-docker.pkg.dev/<YOUR_PROJECT_ID>/legendary-potato-repo/legendary-potato:latest
    ```

## Part 4: Deploying to Cloud Run

**Google Cloud Run** is a fully managed platform that automatically scales your stateless containers. Now we'll deploy our container image to Cloud Run.

1.  **Deploy the Service:**
    Choose a name for your service (e.g., `legendary-potato-service`) and run the following command. Replace the placeholders with your own values.

    ```bash
    gcloud run deploy <YOUR_SERVICE_NAME> \
        --image=<YOUR_REGION>-docker.pkg.dev/<YOUR_PROJECT_ID>/legendary-potato-repo/legendary-potato:latest \
        --platform=managed \
        --region=<YOUR_REGION> \
        --allow-unauthenticated \
        --set-env-vars="ENV=production" \
        --set-secrets="GOOGLE_CLIENT_ID=google-client-id:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest,STARLET_SECRET_KEY=starlette-session-key:latest"
    ```

    -   `--image`: The full path to your container image in Artifact Registry.
    -   `--platform=managed`: Use the fully-managed Cloud Run platform.
    -   `--region`: The region where you want to deploy your service.
    -   `--allow-unauthenticated`: This makes your service publicly accessible.
    -   `--set-env-vars`: Sets environment variables for your service. We set `ENV=production` to disable `ngrok` in the deployed environment.
    -   `--set-secrets`: Mounts your secrets from Secret Manager as environment variables in the running container.

## Part 5: Troubleshooting Deployment Failures

You may encounter a couple of common issues during deployment. Here's how to fix them.

### Issue 1: Permission Denied on Secret

**Error Message:** `Permission denied on secret: ... The service account used must be granted the 'Secret Manager Secret Accessor' role...`

**Why it happens:** By default, the Cloud Run service does not have permission to access secrets stored in Secret Manager. You need to explicitly grant this permission to its service account.

**How to fix it:**
You need to grant the `Secret Manager Secret Accessor` role to the service account for each secret.

1.  **Find the Service Account:** The service account email will be in the error message. It usually looks like `<PROJECT_NUMBER>-compute@developer.gserviceaccount.com`.

2.  **Grant Permissions:** Run the following command for each of your secrets, replacing the placeholders with your own values.

    ```bash
    gcloud secrets add-iam-policy-binding <SECRET_NAME> \
        --member="serviceAccount:<SERVICE_ACCOUNT_EMAIL>" \
        --role="roles/secretmanager.secretAccessor"
    ```
    For example:
    ```bash
    gcloud secrets add-iam-policy-binding google-client-id \
        --member="serviceAccount:273852515674-compute@developer.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
    ```

### Issue 2: Container Failed to Start

**Error Message:** `The user-provided container failed to start and listen on the port defined provided by the PORT=8080 environment variable...`

**Why it happens:** Cloud Run tells your container which port to listen on by setting the `PORT` environment variable (it defaults to `8080`). If your application is hard-coded to listen on a different port (e.g., `8001`), it won't receive traffic from Cloud Run, and the health check will fail.

**How to fix it:**
Update your application's startup script to use the `PORT` environment variable if it's available.

In our case, we updated `start.sh`:
```bash
#!/bin/bash
export PYTHONPATH=$PYTHONPATH:./src
# Use the PORT from Cloud Run, or default to 8001 for local development
uvicorn legendary_potato.app.main:app --host 0.0.0.0 --port ${PORT:-8001}
```

After fixing this, you'll need to **rebuild and re-push your Docker image** before attempting to deploy again.

## Part 6: Post-Deployment Steps

Once your deployment is successful, there are a couple of final steps.

1.  **Get the Service URL:**
    After a successful deployment, `gcloud` will print the URL of your new service. You can also retrieve it at any time with this command:
    ```bash
    gcloud run services describe <YOUR_SERVICE_NAME> --platform=managed --region=<YOUR_REGION> --format="value(status.url)"
    ```
    Your URL will look something like this: `https://<YOUR_SERVICE_NAME>-<RANDOM_HASH>-<REGION>.a.run.app`

2.  **Update `PUBLIC_DOMAIN`:**
    Your application needs to know its own public URL to correctly handle the OAuth redirect. We'll update the Cloud Run service to set the `PUBLIC_DOMAIN` environment variable to the service URL.
    ```bash
    gcloud run services update <YOUR_SERVICE_NAME> \
        --region=<YOUR_REGION> \
        --update-env-vars="ENV=production,PUBLIC_DOMAIN=<YOUR_SERVICE_URL>"
    ```

3.  **Update Google Cloud Console:**
    Go back to the "Credentials" page in the Google Cloud Console for your project. Add the following URL to your "Authorized redirect URIs", replacing `<YOUR_SERVICE_URL>` with your actual service URL:

    ```
    <YOUR_SERVICE_URL>/auth/google/callback
    ```

## Part 7: Viewing Your Deployed App

You can see your running application in the GCP Console.

*   **Go to the Cloud Run Dashboard:** [https://console.cloud.google.com/run](https://console.cloud.google.com/run)
*   Select your project.
*   You will see your `legendary-potato-service` in the list. Click on it to see details, logs, and manage revisions.

Your application is now deployed and ready to use!
