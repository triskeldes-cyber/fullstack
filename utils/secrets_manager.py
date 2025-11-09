# 📄 utils/secrets_manager.py (ARCHIVO NUEVO)

import json
import os
import secrets
import string
from typing import Dict, Any

class SecretsManager:
    """Gestor centralizado de secrets para compartir entre servicios"""
    
    def __init__(self, secrets_file='.deployment_secrets.json'):
        self.secrets_file = secrets_file
        self.secrets = self._load_secrets()
    
    def _load_secrets(self) -> Dict[str, Any]:
        """Cargar secrets existentes o crear archivo nuevo"""
        if os.path.exists(self.secrets_file):
            try:
                with open(self.secrets_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("⚠️  Archivo de secrets corrupto, creando nuevo...")
        
        return {
            'postgres': {},
            'evolution_api': {}, 
            'chatwoot': {},
            'portainer': {},
            'traefik': {}
        }
    
    def save_secrets(self):
        """Guardar secrets en archivo JSON"""
        with open(self.secrets_file, 'w') as f:
            json.dump(self.secrets, f, indent=2, ensure_ascii=False)
    
    def set_secret(self, service: str, key: str, value: str):
        """Establecer un secret para un servicio"""
        if service not in self.secrets:
            self.secrets[service] = {}
        self.secrets[service][key] = value
        self.save_secrets()
    
    def get_secret(self, service: str, key: str, default=None) -> str:
        """Obtener un secret de un servicio"""
        return self.secrets.get(service, {}).get(key, default)
    
    def generate_postgres_credentials(self):
        """Generar y almacenar credenciales de PostgreSQL"""
        postgres_password = self._generate_secure_password()
        postgres_user = "postgres"
        postgres_db = "evolution"
        
        self.set_secret('postgres', 'password', postgres_password)
        self.set_secret('postgres', 'user', postgres_user)
        self.set_secret('postgres', 'database', postgres_db)
        
        return {
            'password': postgres_password,
            'user': postgres_user,
            'database': postgres_db
        }
    
    def _generate_secure_password(self, length=32) -> str:
        """Generar contraseña segura"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def get_postgres_connection_string(self):
        """Obtener string de conexión para Evolution API"""
        user = self.get_secret('postgres', 'user')
        password = self.get_secret('postgres', 'password')
        database = self.get_secret('postgres', 'database')
        return f"postgresql://{user}:{password}@pgvector:5432/{database}"