"""Controller configuration (control plane)."""
import os


class Settings:
    # Compose project + service used to find/scale API containers.
    compose_project = os.getenv("COMPOSE_PROJECT_NAME", "crm")
    api_service = os.getenv("API_SERVICE", "api")

    # Image + network used when starting new API containers.
    api_image = os.getenv("API_IMAGE", "crm-api")
    api_network = os.getenv("API_NETWORK", "crm_private_net")
    db_url = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://crm:crm@db:5432/crm"
    )
    secret_key = os.getenv("SECRET_KEY", "change-me-in-production")
    algorithm = os.getenv("ALGORITHM", "HS256")

    # ---- Scaling guardrails (prevent runaway scaling) ----
    min_instances = int(os.getenv("MIN_INSTANCES", "1"))
    max_instances = int(os.getenv("MAX_INSTANCES", "6"))
    # Seconds to wait after a scale action before allowing another (cooldown).
    cooldown_seconds = int(os.getenv("COOLDOWN_SECONDS", "15"))

    # ---- Autoscaler thresholds (requests/sec per instance) ----
    # Scale UP when avg RPS per instance exceeds this; scale DOWN when below.
    target_rps_high = float(os.getenv("TARGET_RPS_HIGH", "8"))
    target_rps_low = float(os.getenv("TARGET_RPS_LOW", "2"))
    autoscale_interval = int(os.getenv("AUTOSCALE_INTERVAL", "10"))


settings = Settings()
