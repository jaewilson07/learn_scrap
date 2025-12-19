# Tutorial: Deploying to Google Cloud Run

This tutorial will guide you through deploying your FastAPI application as a Docker container to Google Cloud Run.

## Prerequisites

1.  **GCP Account:** You need a Google Cloud Platform account with billing enabled. ✔️
2.  **`gcloud` CLI:** Install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) and authenticate with your account:
    ```bash
    gcloud auth login
    ``` ✔️
3.  **Docker:** Docker must be installed and running on your local machine. ✔️

## Part 1: GCP Project Setup

1.  **Create a GCP Project:**
    Go to the [GCP Console](https://console.cloud.google.com/projectcreate) and create a new project. Note your **Project ID**. ✔️

2.  **Set Your Project:**
    Replace `<YOUR_PROJECT_ID>` with your actual Project ID and run:
    ```bash
    gcloud config set project <YOUR_PROJECT_ID>
    ``` ✔️

3.  **Enable APIs:**
    Enable the necessary APIs for your project:
    ```bash
    gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
    ``` ✔️

## Part 2: Storing Secrets with Secret Manager

Never expose your secrets in your code or Docker image. Use Secret Manager to store them securely.

1.  **Create Secrets:**
    Create secrets for your application's environment variables.
    ```bash
    # Google Client ID
    echo -n "<YOUR_GOOGLE_CLIENT_ID>" | gcloud secrets create "google-client-id" --data-file=-

    # Google Client Secret
    echo -n "<YOUR_GOOGLE_CLIENT_SECRET>" | gcloud secrets create "google-client-secret" --data-file=-

    # Starlette Session Key
    echo -n "<YOUR_STARLET_SECRET_KEY>" | gcloud secrets create "starlette-session-key" --data-file=-
    ```

## Part 3: Building and Pushing the Docker Image

1.  **Create an Artifact Registry Repository:**
    Choose a region for your repository (e.g., `us-central1`) and run:
    ```bash
    gcloud artifacts repositories create legendary-potato-repo --repository-format=docker --location=<YOUR_REGION>
    ``` ✔️

2.  **Configure Docker:**
    Configure the Docker client to authenticate to your new repository:
    ```bash
    gcloud auth configure-docker <YOUR_REGION>-docker.pkg.dev
    ```

3.  **Build and Tag the Image:**
    Build your Docker image and tag it with the path to your Artifact Registry repository.
    ```bash
    docker build -t legendary-potato .
    docker tag legendary-potato <YOUR_REGION>-docker.pkg.dev/<YOUR_PROJECT_ID>/legendary-potato-repo/legendary-potato:latest
    ```

4.  **Push the Image:**
    Push the image to Artifact Registry:
    ```bash
    docker push <YOUR_REGION>-docker.pkg.dev/<YOUR_PROJECT_ID>/legendary-potato-repo/legendary-potato:latest
    ```

## Part 4: Deploying to Cloud Run

Now you can deploy your container image to Cloud Run.

1.  **Deploy the Service:**
    Choose a name for your service (e.g., `legendary-potato`) and run the following command. Replace the placeholders with your own values.

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
    -   `--set-env-vars`: Sets environment variables for your service. We set `ENV=production` to disable `ngrok`.
    -   `--set-secrets`: Mounts your secrets from Secret Manager as environment variables.

## Part 5: Post-Deployment Steps

1.  **Get the Service URL:**
    After the deployment is complete, `gcloud` will print the URL of your new service. It will look something like this:
    `https://<YOUR_SERVICE_NAME>-<RANDOM_HASH>-<REGION>.a.run.app`

2.  **Update `PUBLIC_DOMAIN`:**
    Your application needs to know its own public URL for OAuth. Update your Cloud Run service to include the `PUBLIC_DOMAIN` environment variable.

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

Your application is now deployed and ready to use!
