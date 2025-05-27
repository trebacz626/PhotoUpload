cd api
export PROJECT_ID="photoupload-457815" # Replace with your project ID
export REGION="europe-central2"      # Replace with your region
export REPO_NAME="my-docker-repo"    # Use the repo name you created
export IMAGE_NAME="landmark-app-api" # Or your desired image name
export IMAGE_TAG="latest" # Or a specific version tag


docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${IMAGE_TAG} .

docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${IMAGE_TAG}

export IMAGE_DIGEST=$(gcloud artifacts docker images describe \
  ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${IMAGE_TAG} \
  --project=${PROJECT_ID} \
  --format='get(image_summary.digest)')

echo "The digest for your pushed image is: ${IMAGE_DIGEST}"

FULL_IMAGE_WITH_DIGEST="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}@${IMAGE_DIGEST}"

cd ../terraform

terraform apply \
  -var="api_container_image=${FULL_IMAGE_WITH_DIGEST}" \