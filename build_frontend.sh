cd frontend
export PROJECT_ID="photoupload-457815"
export REGION="europe-central2"
export REPO_NAME="my-docker-repo" 
export STREAMLIT_IMAGE_NAME="landmark-app-streamlit"
export IMAGE_TAG="latest"

docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${STREAMLIT_IMAGE_NAME}:${IMAGE_TAG} .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${STREAMLIT_IMAGE_NAME}:${IMAGE_TAG}

export IMAGE_DIGEST=$(gcloud artifacts docker images describe \
  ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${STREAMLIT_IMAGE_NAME}:${IMAGE_TAG} \
  --project=${PROJECT_ID} \
  --format='get(image_summary.digest)')

echo "The digest for your pushed image is: ${IMAGE_DIGEST}"

FULL_IMAGE_WITH_DIGEST="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${STREAMLIT_IMAGE_NAME}@${IMAGE_DIGEST}"

cd ../terraform

terraform apply \
  -var="streamlit_container_image=${FULL_IMAGE_WITH_DIGEST}" \