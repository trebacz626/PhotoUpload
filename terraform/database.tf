# Cloud SQL
resource "random_string" "sql_instance_suffix" {
  length  = 4
  special = false
  upper   = false
}

resource "google_sql_database_instance" "db_instance" {
  project          = var.project_id
  name             = "${var.app_name}-db-${random_string.sql_instance_suffix.result}"
  region           = var.region
  database_version = "POSTGRES_15" 
  settings {
    tier = "db-f1-micro" 
    ip_configuration {
      ipv4_enabled = false 
      private_network = google_compute_network.vpc_network.id
    }
    backup_configuration {
      enabled = true
    }
  }
  deletion_protection = false 

  depends_on = [
    google_project_service.apis["sqladmin.googleapis.com"],
    google_compute_network.vpc_network,
    google_service_networking_connection.private_vpc_connection
  ]
}

resource "google_sql_database" "database" {
  project  = var.project_id
  instance = google_sql_database_instance.db_instance.name
  name     = var.db_name
}

resource "google_sql_user" "db_user" {
  project  = var.project_id
  instance = google_sql_database_instance.db_instance.name
  name     = var.db_user
  password = var.db_password
}

# Grant Cloud SQL Client role to the Function Service Account
resource "google_project_iam_member" "function_sa_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member = "serviceAccount:${google_service_account.function_sa.email}"

  depends_on = [google_service_account.function_sa]
}

# Grant Cloud SQL Client role to the API Service Account
resource "google_project_iam_member" "api_sa_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member = "serviceAccount:${google_service_account.api_sa.email}"

  depends_on = [google_service_account.api_sa]
}