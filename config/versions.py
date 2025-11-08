#!/usr/bin/env python3
"""
Versiones de imágenes Docker centralizadas.
"""

VERSIONS = {
    "traefik": "v3.4.0",
    "portainer": "latest",
    "portainer_agent": "latest",
    "postgres": "pgvector/pgvector:pg16",
    "evolution_api": "evoapicloud/evolution-api:v2.3.6",
    "chatwoot": "ghcr.io/fazer-ai/chatwoot:latest",
    "redis": "redis:latest",
    "n8n": "n8nio/n8n:latest"  # Para futuro
}

# Configuración por defecto
DEFAULTS = {
    "network": "TriskelNET",
    "repo_url": "https://github.com/triskeldes-cyber/stackschat",
    "install_dir": "/opt/docker-config",
    "state_file": "/opt/docker-config/.installation_state.json",
    "credentials_file": "/opt/docker-config/CREDENCIALES.txt"
}