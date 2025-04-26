# output "backend_api_url" {
#   description = "URL of the deployed Cloud Run backend API"
#   value       = google_cloud_run_v2_service.api_service.uri
# }

output "photo_bucket_name" {
  description = "Name of the GCS bucket for storing photos"
  value = google_storage_bucket.photos_bucket.name
}

output "function_source_bucket_name" {
  description = "Name of the GCS bucket for storing function source code"
  value = google_storage_bucket.function_source_bucket.name
}

output "cloud_sql_instance_connection_name" {
  description = "Connection name for the Cloud SQL instance (used by Cloud SQL Proxy/libraries)"
  value = google_sql_database_instance.db_instance.connection_name
}

output "cloud_sql_instance_private_ip" {
  description = "Private IP address of the Cloud SQL instance"
  value = google_sql_database_instance.db_instance.private_ip_address
}

# output "cloud_function_name" {
#   description = "Name of the deployed Cloud Function"
#   value       = google_cloudfunctions2_function.processor_function.name
# }

output "function_service_account_email" {
  description = "Email of the service account used by the Cloud Function"
  value = google_service_account.function_sa.email
}

output "api_service_account_email" {
  description = "Email of the service account used by the Cloud Run API"
  value = google_service_account.api_sa.email
}

output "backend_api_url" {
  description = "URL of the deployed Cloud Run backend API"
  value = google_cloud_run_v2_service.api_service.uri
}

output "streamlit_app_url" {
  description = "URL of the deployed Cloud Run Streamlit frontend"
  value       = google_cloud_run_v2_service.streamlit_service.uri
}