# CloudCRM — Cloud-Networked CRM (BTEC Unit 6: Networking in the Cloud)

A full-stack CRM (FastAPI + Vue.js) deployed behind an Nginx load balancer,
designed to demonstrate cloud-networking concepts: load balancing, horizontal
auto-scaling, public/private subnet separation, and a CI/CD automation
pipeline. The app includes a dedicated **Infrastructure** page that visualises
the live network topology and lets you manage the load balancer.

## Architecture

```
                       Internet (host :8080 / :80)
                                │
                   ┌────────────▼────────────┐   public subnet
                   │  nginx                   │   serves Vue SPA +
                   │  (SPA host + Load Bal.)  │   load balances /api
                   └────────────┬────────────┘   upstream crm_api (Docker DNS)
              ┌─────────────────┼─────────────────┐
        ┌─────▼─────┐     ┌─────▼─────┐     ┌─────▼─────┐  private subnet
        │  api #1   │     │  api #2   │     │  api #N   │  FastAPI (scalable)
        └─────┬─────┘     └─────┬─────┘     └─────┬─────┘
              └─────────────────┼─────────────────┘
                          ┌─────▼─────┐
                          │    db     │   PostgreSQL (private subnet)
                          └───────────┘
```

A single Nginx service handles both jobs: it serves the built Vue SPA and load
balances API traffic across the FastAPI instances. It also serves branded
404 / 50x error pages.

| BTEC component | Where it lives |
|---|---|
| VPC + public/private subnets | `docker-compose.yml` `public_net` / `private_net` |
| Internet/NAT Gateway | `nginx` service (public ingress, bridges both subnets) |
| Load Balancer | `nginx/nginx.conf` (`upstream crm_api`) |
| Auto-scaling | `docker compose up --scale api=N` + Docker DNS `resolve` |
| Instance registry & topology | `backend/app/routers/infrastructure.py` |
| CI/CD pipeline | `.github/workflows/ci.yml`, `deploy.yml` |
| Network visualisation / LB mgmt | `frontend/src/views/Infrastructure.vue` |
| Branded error pages | `nginx/error-pages/404.html`, `50x.html` |

## Tech stack

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, JWT auth (python-jose + bcrypt)
- **Frontend:** Vue 3, Vite, Pinia, Vue Router, Chart.js, vis-network
- **Infra:** Docker, Docker Compose, Nginx (single service: SPA host + load balancer)
- **CI/CD:** GitHub Actions → GHCR → SSH deploy

## Run locally

```bash
# Start the full stack with 3 API instances behind the load balancer
docker compose up -d --build --scale api=3

# Open the app
open http://localhost:8080
# Login: admin@cloudcrm.dev / admin123
```

### Demonstrate load balancing

Open the **Infrastructure** page and click **Start load**. Requests are fired
through the Nginx load balancer; the distribution bars show traffic spreading
evenly across instances. Or from the CLI:

```bash
for i in $(seq 1 30); do
  curl -s http://localhost:8080/api/infrastructure/ping \
    | python3 -c "import sys,json;print(json.load(sys.stdin)['served_by'])"
done | sort | uniq -c
```

### Demonstrate auto-scaling

```bash
# Scale up — new instances auto-register with the load balancer
docker compose up -d --scale api=5 --no-recreate

# Scale down
docker compose up -d --scale api=2 --no-recreate
```

The new/removed instances appear in the topology graph and instances table
within a few seconds (heartbeat window).

## Tests

```bash
# Run inside the API container (Python 3.12 environment)
docker compose exec -e TESTING=1 api python -m pytest tests/ -q
```

CI runs the same suite against a PostgreSQL service on every push.

## Deployment (CI/CD)

`deploy.yml` triggers on push to `main`:

1. Builds backend & nginx (SPA + LB) images, pushes to GitHub Container Registry.
2. Copies `docker-compose.prod.yml` to the server over SCP.
3. Pulls images and runs `docker compose up -d --scale api=3` over SSH.

Required repository secrets: `SERVER_HOST`, `SERVER_USER`, `SERVER_SSH_KEY`,
`SERVER_PORT` (optional), `PROD_SECRET_KEY`.

## Security notes

- The `/api/infrastructure/ping` endpoint is intentionally public so the
  frontend can generate load without auth; all CRM and management endpoints
  require a JWT.
- Change `SECRET_KEY` / `PROD_SECRET_KEY` and the default admin password before
  any real deployment.
- `CORS_ORIGINS` defaults to `*` for the demo; restrict it in production.
