# Single Nginx image: builds the Vue SPA, then serves it AND load balances
# the FastAPI instances. Build context must be the project root so we can
# access both ./frontend (app source) and ./nginx (config + error pages).
#
#   docker build -f nginx/Dockerfile -t cloudcrm-nginx .

# ---- Build stage: compile the Vue frontend ----
FROM node:20-alpine AS build

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---- Serve stage: Nginx serves SPA + load balances /api ----
FROM nginx:1.27-alpine

# Built SPA
COPY --from=build /app/dist /usr/share/nginx/html
# Branded error pages
COPY nginx/error-pages /usr/share/nginx/html/error-pages
# Load balancer + SPA config (replaces the default nginx.conf)
COPY nginx/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1/lb-health || exit 1

CMD ["nginx", "-g", "daemon off;"]
