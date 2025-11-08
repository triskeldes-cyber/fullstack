#!/usr/bin/env python3
"""
Módulo de Traefik.
Instala Traefik como reverse proxy con SSL automático.
"""

import os
from .base import StackComponent
from utils import (
    run,
    get_valid_input,
    validate_email,
    confirm_action
)
from config import DEFAULTS


class Traefik(StackComponent):
    """Maneja la instalación de Traefik."""
    
    def __init__(self, state_manager, install_dir):
        super().__init__(
            name="traefik",
            description="Traefik - Reverse Proxy + SSL",
            state_manager=state_manager,
            compose_path=f"{install_dir}/traefik/docker-compose.yml"
        )
        self.install_dir = install_dir
        self.dependencies = ["prerequisites"]
    
    def install(self):
        """Instala Traefik."""
        self.print_header()
        
        # Verificar dependencias
        deps_ok, missing = self.check_dependencies()
        if not deps_ok:
            self.print_error(f"Faltan dependencias: {', '.join(missing)}")
            print("   Instala los prerequisitos primero (opción 2)")
            return False
        
        # Verificar si ya está instalado
        if self.is_installed():
            print("⚠️  Traefik ya está instalado")
            if not confirm_action("¿Deseas reinstalar?", default_yes=False):
                return False
            self.remove_stack()
        
        # Obtener configuración
        network = self.state_manager.get_network_name() or DEFAULTS['network']
        
        print("\n📧 Configuración SSL")
        print("   Let's Encrypt necesita un email válido")
        email = get_valid_input(
            "Email para certificados SSL:",
            validate_email,
            "❌ Email no válido"
        )
        
        # Verificar que existe el compose
        if not os.path.exists(self.compose_path):
            self.print_error(f"No se encontró {self.compose_path}")
            print("   Verifica que el repositorio esté clonado correctamente")
            return False
        
        # Reemplazar variables en el compose
        print("\n📝 Configurando Traefik...")
        if not self._replace_variables(network, email):
            self.print_error("Error configurando variables")
            return False
        
        # Desplegar stack
        print("\n🚀 Desplegando Traefik...")
        compose_dir = os.path.dirname(self.compose_path)
        
        if not self.deploy_via_cli(self.compose_path, "traefik"):
            self.print_error("Error desplegando Traefik")
            return False
        
        # Esperar a que esté listo
        print("\n⏳ Esperando a que Traefik esté operativo...")
        if not self.wait_for_stack(timeout=30):
            print("⚠️  Traefik tardó en iniciar, pero puede estar ok")
        
        # Guardar en state
        self.save_to_state({
            "network": network,
            "email": email,
            "compose_path": self.compose_path
        })
        
        self.print_success()
        print(f"\n📧 Email SSL: {email}")
        print(f"🌐 Red: {network}")
        print("\n⚠️  IMPORTANTE:")
        print("   • Los certificados SSL pueden tardar 1-2 minutos en generarse")
        print("   • Asegúrate que los puertos 80 y 443 estén abiertos en el firewall")
        
        return True
    
    def is_installed(self):
        """Verifica si Traefik está instalado."""
        # Verificar en state
        if not self.state_manager.is_installed(self.name):
            return False
        
        # Verificar que el stack esté corriendo
        result = run("docker stack ps traefik --format '{{.CurrentState}}'", capture=True, check=False)
        return result and "Running" in result
    
    def _replace_variables(self, network, email):
        """
        Reemplaza variables en el docker-compose.yml
        
        Args:
            network: Nombre de la red
            email: Email para SSL
        
        Returns:
            True si tuvo éxito
        """
        try:
            with open(self.compose_path, 'r') as f:
                content = f.read()
            
            # Reemplazar variables
            content = content.replace('${NETWORK}', network)
            content = content.replace('${EMAIL}', email)
            
            # Guardar
            with open(self.compose_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Variables configuradas en {self.compose_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def uninstall(self):
        """Desinstala Traefik."""
        print("\n⚠️  Esto eliminará Traefik y todos sus certificados SSL")
        
        if not confirm_action("¿Continuar?", default_yes=False):
            return False
        
        # Eliminar stack
        if self.remove_stack():
            # Eliminar del state
            self.state_manager.remove_component(self.name)
            print("✅ Traefik desinstalado")
            return True
        
        return False