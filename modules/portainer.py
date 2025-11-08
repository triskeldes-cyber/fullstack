#!/usr/bin/env python3
"""
Módulo de Portainer.
Instala Portainer para gestión visual de contenedores.
"""

import os
import shlex
import subprocess
from .base import StackComponent
from utils import (
    run,
    get_valid_input,
    get_secure_password,
    validate_domain,
    confirm_action
)
from config import DEFAULTS


class Portainer(StackComponent):
    """Maneja la instalación de Portainer."""
    
    def __init__(self, state_manager, install_dir):
        super().__init__(
            name="portainer",
            description="Portainer - Gestión Visual",
            state_manager=state_manager,
            compose_path=f"{install_dir}/portainer/docker-compose.yml"
        )
        self.install_dir = install_dir
        self.dependencies = ["prerequisites", "traefik"]
    
    def install(self):
        """Instala Portainer."""
        self.print_header()
        
        # Verificar dependencias
        deps_ok, missing = self.check_dependencies()
        if not deps_ok:
            self.print_error(f"Faltan dependencias: {', '.join(missing)}")
            print(f"   Instala primero: {', '.join(missing)}")
            return False
        
        # Verificar si ya está instalado
        if self.is_installed():
            print("⚠️  Portainer ya está instalado")
            if not confirm_action("¿Deseas reinstalar?", default_yes=False):
                return False
            self.remove_stack()
        
        # Obtener configuración
        network = self.state_manager.get_network_name() or DEFAULTS['network']
        
        print("\n🌍 Configuración de dominio")
        domain = get_valid_input(
            "Dominio para Portainer (ej: portainer.tudominio.com):",
            validate_domain,
            "❌ Dominio no válido",
            default="portainer.localhost"
        )
        
        print("\n🔐 Configuración de usuario admin")
        password = get_secure_password("Contraseña para admin de Portainer")
        
        # Generar hash de la contraseña
        print("\n🔒 Generando hash de contraseña...")
        password_hash = self._generate_password_hash(password)
        
        if not password_hash:
            self.print_error("Error generando hash de contraseña")
            return False
        
        # Verificar compose
        if not os.path.exists(self.compose_path):
            self.print_error(f"No se encontró {self.compose_path}")
            return False
        
        # Reemplazar variables
        print("\n📝 Configurando Portainer...")
        if not self._replace_variables(network, domain, password_hash):
            self.print_error("Error configurando variables")
            return False
        
        # Desplegar stack
        print("\n🚀 Desplegando Portainer...")
        if not self.deploy_via_cli(self.compose_path, "portainer"):
            self.print_error("Error desplegando Portainer")
            return False
        
        # Esperar a que esté listo
        print("\n⏳ Esperando a que Portainer esté operativo...")
        if not self.wait_for_stack(timeout=45):
            print("⚠️  Portainer tardó en iniciar, verifica los logs")
        
        # Guardar en state
        self.save_to_state({
            "network": network,
            "domain": domain,
            "url": f"https://{domain}",
            "username": "admin",
            "compose_path": self.compose_path
        })
        
        self.print_success()
        print(f"\n🔗 URL: https://{domain}")
        print(f"👤 Usuario: admin")
        print(f"🔐 Contraseña: (la que configuraste)")
        print("\n⚠️  NOTAS:")
        print("   • Espera 1-2 minutos para que el certificado SSL se genere")
        print("   • Si el navegador muestra advertencia SSL, es temporal")
        print("   • Usa modo incógnito si tienes problemas de caché")
        
        return True
    
    def is_installed(self):
        """Verifica si Portainer está instalado."""
        if not self.state_manager.is_installed(self.name):
            return False
        
        result = run("docker stack ps portainer --format '{{.CurrentState}}'", capture=True, check=False)
        return result and "Running" in result
    
    def _generate_password_hash(self, password):
        """
        Genera hash bcrypt de la contraseña usando htpasswd.
        
        Args:
            password: Contraseña en texto plano
        
        Returns:
            String con el hash o None si falla
        """
        safe_password = shlex.quote(password)
        
        try:
            cmd = f"htpasswd -nbB admin {safe_password}"
            output = subprocess.run(
                cmd,
                shell=True,
                check=True,
                text=True,
                capture_output=True
            ).stdout.strip()
            
            # Extraer solo el hash (después del :)
            hash_value = output.split(":", 1)[1]
            
            # Escapar $ para YAML (duplicar $$)
            hash_escaped = hash_value.replace('$', '$$')
            
            print("✅ Hash generado correctamente")
            return hash_escaped
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error generando hash: {e}")
            print("   Asegúrate de que apache2-utils esté instalado")
            return None
    
    def _replace_variables(self, network, domain, password_hash):
        """Reemplaza variables en el docker-compose.yml"""
        try:
            with open(self.compose_path, 'r') as f:
                content = f.read()
            
            # Reemplazar variables
            content = content.replace('${NETWORK}', network)
            content = content.replace('${PORTAINER_DOMAIN}', domain)
            content = content.replace('${PORTAINER_PASSWORD_HASH}', password_hash)
            
            # Guardar
            with open(self.compose_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Variables configuradas")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def uninstall(self):
        """Desinstala Portainer."""
        print("\n⚠️  Esto eliminará Portainer y su configuración")
        
        if not confirm_action("¿Continuar?", default_yes=False):
            return False
        
        if self.remove_stack():
            self.state_manager.remove_component(self.name)
            print("✅ Portainer desinstalado")
            return True
        
        return False
    
    def get_admin_credentials(self):
        """
        Obtiene las credenciales de admin desde el state.
        
        Returns:
            dict con url y username, o None
        """
        data = self.get_from_state()
        if data:
            return {
                "url": data.get("url"),
                "username": data.get("username", "admin")
            }
        return None