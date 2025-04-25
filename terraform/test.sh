API_URL=$(terraform output -raw backend_api_url)

# Test the simple hello endpoint
echo "Testing /api/hello/ endpoint..."
curl ${API_URL}/api/hello/
echo "" # Add a newline

# Test the database connection endpoint
echo "Testing /api/db_check/ endpoint..."
curl ${API_URL}/api/db_check/
echo "" # Add a newline