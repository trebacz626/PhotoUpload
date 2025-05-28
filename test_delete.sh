#!/bin/bash

# --- Configuration ---
SERVICE_URL="https://landmark-app-api-jcj4dqmava-lm.a.run.app" # REPLACE with your actual Cloud Run URL
USERNAME="username"  # REPLACE with your test username
PASSWORD="password626"  # REPLACE with your test password
IMAGE_FILE="photo.jpeg"         # Ensure this file exists in the current directory


# --- 1. Authenticate and Get Token ---
echo "Attempting to log in as '$USERNAME'..."
TOKEN_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}" \
  "${SERVICE_URL}/api/v1/auth/login/")

# Check if jq is installed for parsing JSON
if command -v jq &> /dev/null; then
  AUTH_TOKEN=$(echo "${TOKEN_RESPONSE}" | jq -r .key)
else
  # Crude extraction if jq is not available (assumes "key":"TOKEN_VALUE" format)
  AUTH_TOKEN=$(echo "${TOKEN_RESPONSE}" | sed -n 's/.*"key":"\([^"]*\)".*/\1/p')
  echo "Warning: jq not found. Attempting crude token extraction. This might be unreliable."
fi


if [ "$AUTH_TOKEN" = "null" ] || [ -z "$AUTH_TOKEN" ] || [[ "$AUTH_TOKEN" == *"detail"* ]]; then
  echo "ERROR: Failed to get authentication token."
  echo "Response was:"
  echo "${TOKEN_RESPONSE}"
  exit 1
fi
echo "Successfully obtained authentication token."

# --- 2. Upload Photo ---
echo "Attempting to upload '$IMAGE_FILE'..."
UPLOAD_RESPONSE=$(curl -s -X DELETE \
  -H "Authorization: Token ${AUTH_TOKEN}" \
  -F "image=@${IMAGE_FILE}" \
  "${SERVICE_URL}/api/v1/photos/1/delete/")

# --- 3. Display Response ---
echo ""
echo "Upload Response:"
# If jq is available, try to pretty-print if it's JSON, otherwise print raw
if command -v jq &> /dev/null && echo "${UPLOAD_RESPONSE}" | jq . > /dev/null 2>&1; then
  echo "${UPLOAD_RESPONSE}" | jq .
  echo "${UPLOAD_RESPONSE}" | jq . > out.html
else
  echo "${UPLOAD_RESPONSE}"
  echo "${UPLOAD_RESPONSE}" > out.html
fi

echo ""
