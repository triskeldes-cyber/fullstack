#!/usr/bin/env python3
"""
Módulo de Evolution API.
Instala Evolution API para WhatsApp.
"""

import os
from .base import StackComponent
from utils import (
    run,
    gen_secret,
    get_valid_input,
    validate_domain,
    confirm_action
)
from config import DEFAULTS


class EvolutionAPI(StackComponent):
    """Maneja la instalación de Evolution API."""
    
    def __init__(self, state_manager, install_dir):
        super().__init__(
            name="evolution",
            description="Evolution API - WhatsApp",
            state_manager=state_manager,
            compose_path=f"{install_dir}/evolution-api/docker-compose.yml"
        )
        self.install_dir = install_dir
        self.dependencies = ["prerequisites", "traefik", "pgvector"]
    
    def install(self):
        """Instala Evolution API."""
        self.print_header()
        
        # Verificar dependencias
        deps_ok, missing = self.check_dependencies()
        if not deps_ok:
            self.print_error(f"Faltan dependencias: {', '.join(missing)}")
            print(f"   Instala primero: {', '.join(missing)}")
            return False
        
        # Verificar si ya está instalado
        if self.is_installed():
            print("⚠️  Evolution API ya está instalado")
            if not confirm_action("¿Deseas reinstalar?", default_yes=False):
                return False
            self.remove_stack()
        
        # Obtener configuración
        network = self.state_manager.get_network_name() or DEFAULTS['network']
        postgres_password = self.state_manager.get_postgres_password()
        
        if not postgres_password:
            self.print_error("No se encontró la contraseña de PostgreSQL")
            print("   Instala PostgreSQL primero (opción 5)")
            return False
        
        print("\n🌍 Configuración de Evolution API")
        domain = get_valid_input(
            "Dominio para Evolution API (ej: evolution.tudominio.com):",
            validate_domain,
            "❌ Dominio no válido",
            default="evolution.localhost"
        )
        
        # Generar API Key
        print("\n🔑 Generando API Key...")
        api_key = gen_secret(32)
        print(f"✅ API Key generada: {api_key[:8]}...")
        
        # Verificar compose
        if not os.path.exists(self.compose_path):
            self.print_error(f"No se encontró {self.compose_path}")
            return False
        
        # Construir DATABASE_CONNECTION_URI
        database_uri = f"postgresql://postgres:{postgres_password}@pgvector:5432/evolution"
        chatwoot_import_uri = f"postgresql://postgres:{postgres_password}@pgvector:5432/chatwoot?sslmode=disable"
        
        # Reemplazar variables
        print("\n📝 Configurando Evolution API...")
        if not self._replace_variables(network, domain, api_key, postgres_password):
            self.print_error("Error configurando variables")
            return False
        
        # Desplegar stack
        print("\n🚀 Desplegando Evolution API...")
        if not self.deploy_via_cli(self.compose_path, "evolution"):
            self.print_error("Error desplegando Evolution API")
            return False
        
        # Esperar a que esté listo
        print("\n⏳ Esperando a que Evolution API esté operativo...")
        if not self.wait_for_stack(timeout=60):
            print("⚠️  Evolution API tardó en iniciar")
        
        # Guardar en state
        self.save_to_state({
            "network": network,
            "domain": domain,
            "url": f"https://{domain}",
            "api_key": api_key,
            "database": "evolution",
            "database_uri": database_uri,
            "compose_path": self.compose_path
        })
        
        self.print_success()
        print(f"\n🔗 URL: https://{domain}")
        print(f"🔑 API Key: {api_key}")
        print(f"🗄️  Base de datos: evolution")
        print("\n📝 IMPORTANTE:")
        print("   • La base de datos se creará automáticamente")
        print("   • Usa el API Key para autenticar requests")
        print("   • Documentación: https://doc.evolution-api.com")
        
        return True
    
    def is_installed(self):
        """Verifica si Evolution API está instalado."""
        if not self.state_manager.is_installed(self.name):
            return False
        
        result = run("docker stack ps evolution --format '{{.CurrentState}}'", capture=True, check=False)
        return result and "Running" in result
    
    def _replace_variables(self, network, domain, api_key, postgres_password):
        """Reemplaza variables en el docker-compose.yml"""
        try:
            with open(self.compose_path, 'r') as f:
                content = f.read()
            
            # Reemplazar variables
            content = content.replace('${NETWORK}', network)
            content = content.replace('${EVOLUTION_API_SERVER_URL}', domain)
            content = content.replace('${EVOLUTION_API_KEY}', api_key)
            content = content.replace('${POSTGRES_PASSWORD}', postgres_password)
            
            # Guardar
            with open(self.compose_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Variables configuradas")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def uninstall(self):
        """Desinstala Evolution API."""
        print("\n⚠️  Esto eliminará Evolution API y sus instancias de WhatsApp")
        
        if not confirm_action("¿Continuar?", default_yes=False):
            return False
        
        if self.remove_stack():
            # Opcional: eliminar volúmenes
            if confirm_action("¿Deseas eliminar también los volúmenes de datos?", default_yes=False):
                run("docker volume rm evolution_instances", check=False)
                run("docker volume rm evolution_redis", check=False)
            
            self.state_manager.remove_component(self.name)
            print("✅ Evolution API desinstalado")
            return True
        
        return False