variable "project_id" {
  description = "photoupload-457815"
  type        = string
}

variable "region" {
  description = "The GCP region for resources."
  type        = string
  default     = "europe-central2"
}

variable "app_name" {
  description = "Base name for resources."
  type        = string
  default     = "landmark-app"
}

variable "db_name" {
  description = "Name for the Cloud SQL database."
  type        = string
  default     = "landmarkdb"
}

variable "db_user" {
  description = "Username for the Cloud SQL database user."
  type        = string
  default     = "landmarkuser"
}

variable "db_password" {
  description = "Password for the Cloud SQL database user."
  type        = string
  sensitive   = true
}

variable "vision_api_key" {
  description = "API Key for Cloud Vision API."
  type        = string
  sensitive   = true
}

variable "geocoding_api_key" {
  description = "API Key for Geocoding API."
  type        = string
  sensitive   = true
}

variable "function_runtime" {
  description = "Runtime for the Cloud Function (e.g., python311, nodejs18)."
  type        = string
  default     = "python311"
}

variable "function_entry_point" {
  description = "Entry point function name in the Cloud Function code."
  type        = string
  default     = "process_photo"
}

variable "api_container_image" {
  description = "Full path to the container image for the Cloud Run API (e.g., gcr.io/PROJECT_ID/APP_NAME-api:latest)."
  type        = string
}

variable "streamlit_container_image" {
  description = "Full path to the container image for the Cloud Run Streamlit frontend."
  type        = string
}

# path to key for accessing photos
# variable "google_credentials_path" {
#   description = "Path to the GCP service account JSON credentials file"
#   type        = string
# }