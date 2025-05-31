terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.2"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "apis" {
  for_each = toset([
    "compute.googleapis.com",
    "vpcaccess.googleapis.com",
    "sqladmin.googleapis.com",
    "servicenetworking.googleapis.com",
    "storage.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "eventarc.googleapis.com",
    "vision.googleapis.com",
    "aiplatform.googleapis.com",
    "geocoding-backend.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "artifactregistry.googleapis.com"
  ])
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# Networking
resource "google_compute_network" "vpc_network" {
  project                 = var.project_id
  name                    = "${var.app_name}-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.apis["compute.googleapis.com"]]
}

resource "google_compute_subnetwork" "subnet" {
  project                  = var.project_id
  name                     = "${var.app_name}-subnet"
  ip_cidr_range            = "10.0.0.0/24"
  region                   = var.region
  network                  = google_compute_network.vpc_network.id
  private_ip_google_access = true
}

resource "google_compute_global_address" "private_service_access_range" {
  project       = var.project_id
  name          = "${var.app_name}-service-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc_network.id

  depends_on = [google_compute_network.vpc_network]
}

# Private connection between VPC and other services
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_access_range.name]

  depends_on = [
    google_project_service.apis["servicenetworking.googleapis.com"],
    google_compute_global_address.private_service_access_range
  ]
}

resource "google_compute_subnetwork" "vpc_connector_subnet" {
  project       = var.project_id
  name          = "${var.app_name}-connector-subnet"
  ip_cidr_range = "10.0.1.0/28"
  region        = var.region
  network       = google_compute_network.vpc_network.id
  purpose       = "PRIVATE"

  depends_on = [google_compute_network.vpc_network]
}


resource "google_compute_firewall" "allow_internal" {
  project = var.project_id
  name    = "${var.app_name}-allow-internal"
  network = google_compute_network.vpc_network.name
  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "icmp"
  }
  source_ranges = [google_compute_subnetwork.subnet.ip_cidr_range]
}

resource "google_vpc_access_connector" "connector" {
  project = var.project_id
  name    = "${var.app_name}-connector"
  region  = var.region
  subnet { name = google_compute_subnetwork.vpc_connector_subnet.name }
  machine_type = "e2-micro"
  depends_on = [
    google_project_service.apis["vpcaccess.googleapis.com"],
    google_compute_subnetwork.vpc_connector_subnet
  ]
}

# Secrets
resource "google_secret_manager_secret" "db_password_secret" {
  project   = var.project_id
  secret_id = "${var.app_name}-db-password"
  replication {
    auto {} 
  }
  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}
resource "google_secret_manager_secret_version" "db_password_version" {
  secret      = google_secret_manager_secret.db_password_secret.id
  secret_data = var.db_password
}

resource "google_secret_manager_secret" "vision_api_key_secret" {
  project   = var.project_id
  secret_id = "${var.app_name}-vision-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}
resource "google_secret_manager_secret_version" "vision_api_key_version" {
  secret      = google_secret_manager_secret.vision_api_key_secret.id
  secret_data = var.vision_api_key
}

resource "google_secret_manager_secret" "geocoding_api_key_secret" {
  project   = var.project_id
  secret_id = "${var.app_name}-geocoding-api-key"
  replication {
    auto {} 
  }
  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}
resource "google_secret_manager_secret_version" "geocoding_api_key_version" {
  secret      = google_secret_manager_secret.geocoding_api_key_secret.id
  secret_data = var.geocoding_api_key
}

# Storage
resource "google_storage_bucket" "photos_bucket" {
  project                     = var.project_id
  name                        = "${var.project_id}-${var.app_name}-photos"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true
  depends_on                  = [google_project_service.apis["storage.googleapis.com"]]
}

resource "google_storage_bucket" "function_source_bucket" {
  project                     = var.project_id
  name                        = "${var.project_id}-${var.app_name}-function-source"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
  depends_on                  = [google_project_service.apis["storage.googleapis.com"]]
}

# Cloud Function Deployment
# data "archive_file" "function_source_zip" {
#   type        = "zip"
#   source_dir  = "${path.root}/function_source"
#   output_path = "${path.root}/function_source.zip"
# }

# resource "google_storage_bucket_object" "function_source_object" {
#   name   = "function_source_${data.archive_file.function_source_zip.output_md5}.zip"
#   bucket = google_storage_bucket.function_source_bucket.name
#   source = data.archive_file.function_source_zip.output_path
# }

# Service Account for the Cloud Function
resource "google_service_account" "function_sa" {
  project      = var.project_id
  account_id   = "${var.app_name}-processor-sa"
  display_name = "Service Account for Landmark Processor Function"
  depends_on   = [google_project_service.apis["iam.googleapis.com"]]
}



# Cloud Run API Service
# Service Account for the Cloud Run API
resource "google_service_account" "api_sa" {
  project      = var.project_id
  account_id   = "${var.app_name}-api-sa"
  display_name = "Service Account for Landmark Backend API"
  depends_on   = [google_project_service.apis["iam.googleapis.com"]]
}

resource "google_cloud_run_v2_service" "api_service" {
  project  = var.project_id
  name     = "${var.app_name}-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.api_sa.email

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.db_instance.connection_name]
      }
    }

    containers {
      image = var.api_container_image

      volume_mounts {
         name       = "cloudsql"
         mount_path = "/cloudsql"
       }

      ports { container_port = 8080 }
      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }
      env {
        name  = "DB_USER"
        value = var.db_user
      }
      env {
        name  = "DB_NAME"
        value = var.db_name
      }
      env {
        name  = "DB_INSTANCE_CONNECTION_NAME"
        value = google_sql_database_instance.db_instance.connection_name
      }
      env {
        name  = "PHOTOS_BUCKET_NAME"
        value = google_storage_bucket.photos_bucket.name
      }

      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_password_secret.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "VISION_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.vision_api_key_secret.secret_id
            version = "latest"
          }
        }
      }


      env {
        name = "GEOCODING_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.geocoding_api_key_secret.secret_id
            version = "latest"
          }
        }
      }
    }

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }


  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_vpc_access_connector.connector,
    google_service_account.api_sa,
    google_sql_database_instance.db_instance,
    google_secret_manager_secret_version.db_password_version,
    google_project_service.apis["run.googleapis.com"]
  ]
}

resource "google_service_account" "streamlit_sa" {
  project      = var.project_id
  account_id   = "${var.app_name}-streamlit-sa"
  display_name = "Service Account for Landmark Streamlit Frontend"
  depends_on   = [google_project_service.apis["iam.googleapis.com"]]
}

resource "google_cloud_run_v2_service" "streamlit_service" {
  project  = var.project_id
  name     = "${var.app_name}-streamlit"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.streamlit_sa.email

    containers {
      image = var.streamlit_container_image
      ports { container_port = 8501 }

      env {
        name = "BACKEND_API_URL"
        value = google_cloud_run_v2_service.api_service.uri
      }
    }


    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_cloud_run_v2_service.api_service,
    google_service_account.streamlit_sa,
    google_project_service.apis["run.googleapis.com"]
  ]
}

##TODO remove later when final deploy
resource "google_cloud_run_v2_service_iam_member" "allow_unauthenticated_api" {
  project  = google_cloud_run_v2_service.api_service.project
  location = google_cloud_run_v2_service.api_service.location
  name     = google_cloud_run_v2_service.api_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"

  depends_on = [google_cloud_run_v2_service.api_service]
}

resource "google_cloud_run_v2_service_iam_member" "allow_unauthenticated_streamlit" {
  project  = google_cloud_run_v2_service.streamlit_service.project
  location = google_cloud_run_v2_service.streamlit_service.location
  name     = google_cloud_run_v2_service.streamlit_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"

  depends_on = [google_cloud_run_v2_service.streamlit_service]
}


# IAM Permissions (Non-DB related)
# Function SA permissions (excluding cloudsql.client which is now in database.tf)
resource "google_project_iam_member" "function_sa_storage_reader" {
  project    = var.project_id
  role       = "roles/storage.objectViewer"
  member     = "serviceAccount:${google_service_account.function_sa.email}"
  depends_on = [google_service_account.function_sa]
}
resource "google_project_iam_member" "function_sa_vision_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.function_sa.email}"
  depends_on = [
    google_service_account.function_sa,
    google_project_service.apis["aiplatform.googleapis.com"]
  ]
}
resource "google_project_iam_member" "function_sa_secret_accessor" {
  project    = var.project_id
  role       = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.function_sa.email}"
  depends_on = [google_service_account.function_sa]
}
resource "google_project_iam_member" "function_sa_eventarc_receiver" {
  project    = var.project_id
  role       = "roles/eventarc.eventReceiver"
  member     = "serviceAccount:${google_service_account.function_sa.email}"
  depends_on = [google_service_account.function_sa]
}

# GCS Service Agent permissions
data "google_storage_project_service_account" "gcs_account" {
  project = var.project_id
}
resource "google_project_iam_member" "gcs_eventarc_publisher" {
  project = var.project_id
  role    = "roles/eventarc.publisher"
  member  = "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"
}

# API SA permissions (excluding cloudsql.client which is now in database.tf)
resource "google_project_iam_member" "api_sa_storage_admin" {
  project    = var.project_id
  role       = "roles/storage.objectAdmin"
  member     = "serviceAccount:${google_service_account.api_sa.email}"
  depends_on = [google_service_account.api_sa]
}
resource "google_project_iam_member" "api_sa_secret_accessor" {
  project    = var.project_id
  role       = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.api_sa.email}"
  depends_on = [google_service_account.api_sa]
}

resource "google_project_iam_member" "api_sa_vision_user" {
  project = var.project_id
  role    = "roles/aiplatform.user" # <--- CHANGE THIS ROLE
  member  = "serviceAccount:${google_service_account.api_sa.email}"
  depends_on = [
    google_service_account.api_sa,
    google_project_service.apis["vision.googleapis.com"],      # Keep this dependency
    google_project_service.apis["aiplatform.googleapis.com"] # Good to also ensure this is enabled
  ]
}

resource "google_secret_manager_secret_iam_member" "db_password_secret_access" {
  secret_id = google_secret_manager_secret.db_password_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api_sa.email}"
  depends_on = [google_secret_manager_secret.db_password_secret, google_service_account.api_sa]
}
