cd frontend
export PROJECT_ID="photoupload-457815"
export REGION="europe-central2"
export REPO_NAME="my-docker-repo" 
export STREAMLIT_IMAGE_NAME="landmark-app-streamlit"
export IMAGE_TAG="latest"

docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${STREAMLIT_IMAGE_NAME}:${IMAGE_TAG} .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${STREAMLIT_IMAGE_NAME}:${IMAGE_TAG}