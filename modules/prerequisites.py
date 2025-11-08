#!/usr/bin/env python3
"""
Módulo de prerequisitos.
Instala Docker, inicializa Swarm, crea red y volúmenes base.
"""

import subprocess
import sys
from .base import Component
from utils import (
    run,
    get_public_ip,
    validate_ip,
    get_valid_input,
    confirm_action
)


class Prerequisites(Component):
    """Maneja la instalación de prerequisitos del sistema."""
    
    def __init__(self, state_manager, network_name="TriskelNET"):
        super().__init__(
            name="prerequisites",
            description="Prerequisitos (Docker + Swarm + Red)",
            state_manager=state_manager
        )
        self.network_name = network_name
    
    def install(self):
        """Instala todos los prerequisitos."""
        self.print_header()
        
        print("\nEste proceso instalará:")
        print("  1. Docker Engine")
        print("  2. Docker Swarm")
        print("  3. Red overlay")
        print("  4. Volúmenes base")
        
        if not confirm_action("\n¿Deseas continuar?", default_yes=True):
            print("\n❌ Instalación cancelada")
            return False
        
        # Paso 1: Instalar Docker
        if not self._install_docker():
            self.print_error("Error instalando Docker")
            return False
        
        # Paso 2: Inicializar Swarm
        if not self._init_swarm():
            self.print_error("Error inicializando Swarm")
            return False
        
        # Paso 3: Crear red
        if not self._create_network():
            self.print_error("Error creando red")
            return False
        
        # Paso 4: Crear volúmenes base
        if not self._create_base_volumes():
            self.print_error("Error creando volúmenes")
            return False
        
        # Guardar en state
        self.save_to_state({
            "docker_installed": True,
            "swarm_initialized": True,
            "network": self.network_name
        })
        
        self.print_success("Prerequisitos instalados correctamente")
        return True
    
    def is_installed(self):
        """Verifica si los prerequisitos están instalados."""
        # Verificar Docker
        if not run("which docker", capture=True, check=False):
            return False
        
        # Verificar Swarm
        state = run("docker info --format '{{.Swarm.LocalNodeState}}'", capture=True, check=False)
        if not state or state.lower() != "active":
            return False
        
        # Verificar red
        networks = run("docker network ls --format '{{.Name}}'", capture=True, check=False)
        if not networks or self.network_name not in networks:
            return False
        
        return True
    
    def _install_docker(self):
        """Instala Docker Engine."""
        print("\n" + "─"*60)
        print("📦 PASO 1/4: Instalando Docker")
        print("─"*60)
        
        # Verificar si ya está instalado
        if run("which docker", capture=True, check=False):
            version = run("docker --version", capture=True, check=False)
            print(f"✅ Docker ya está instalado: {version}")
            
            if not confirm_action("¿Deseas reinstalar Docker?", default_yes=False):
                return True
        
        print("\n🐳 Instalando Docker para Ubuntu 22.04 ARM (aarch64)...")
        
        try:
            # Actualizar sistema
            print("  📥 Actualizando repositorios...")
            subprocess.run("apt-get update", shell=True, check=True, stdout=subprocess.DEVNULL)
            
            # Instalar dependencias
            print("  📦 Instalando dependencias...")
            subprocess.run(
                "apt-get install -y ca-certificates curl gnupg apt-transport-https "
                "software-properties-common lsb-release apache2-utils",
                shell=True, check=True, stdout=subprocess.DEVNULL
            )
            
            # Agregar GPG key
            print("  🔑 Agregando GPG key de Docker...")
            subprocess.run("install -m 0755 -d /etc/apt/keyrings", shell=True, check=True)
            subprocess.run(
                "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | "
                "gpg --dearmor -o /etc/apt/keyrings/docker.gpg",
                shell=True, check=True
            )
            subprocess.run("chmod a+r /etc/apt/keyrings/docker.gpg", shell=True, check=True)
            
            # Agregar repositorio
            print("  📝 Agregando repositorio de Docker...")
            arch = subprocess.run(
                "dpkg --print-architecture",
                shell=True, text=True, capture_output=True
            ).stdout.strip()
            
            subprocess.run(
                f'echo "deb [arch={arch} signed-by=/etc/apt/keyrings/docker.gpg] '
                f'https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | '
                f'tee /etc/apt/sources.list.d/docker.list > /dev/null',
                shell=True, check=True
            )
            
            # Actualizar e instalar
            print("  📥 Actualizando repositorios...")
            subprocess.run("apt-get update", shell=True, check=True, stdout=subprocess.DEVNULL)
            
            print("  🐳 Instalando Docker Engine...")
            subprocess.run(
                "apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin",
                shell=True, check=True, stdout=subprocess.DEVNULL
            )
            
            # Verificar instalación
            version = run("docker --version", capture=True)
            print(f"\n✅ Docker instalado correctamente: {version}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Error instalando Docker: {e}")
            return False
    
    def _init_swarm(self):
        """Inicializa Docker Swarm."""
        print("\n" + "─"*60)
        print("🐝 PASO 2/4: Inicializando Docker Swarm")
        print("─"*60)
        
        # Verificar si ya está activo
        state = run("docker info --format '{{.Swarm.LocalNodeState}}'", capture=True, check=False)
        if state and state.lower() == "active":
            print("✅ Swarm ya está activo")
            node_info = run("docker node ls --format '{{.Hostname}} ({{.Status}})'", capture=True)
            print(f"   Nodo: {node_info}")
            
            if not confirm_action("¿Deseas reinicializar Swarm?", default_yes=False):
                return True
            
            print("\n⚠️  Saliendo del Swarm actual...")
            run("docker swarm leave --force")
        
        # Detectar IP pública
        detected_ip = get_public_ip()
        
        if detected_ip:
            # Verificar si es IP privada
            import ipaddress
            ip_obj = ipaddress.ip_address(detected_ip)
            
            if ip_obj.is_private or ip_obj.is_loopback:
                print(f"\n⚠️  Se detectó una IP privada: {detected_ip}")
                print("   Esto puede causar problemas en Swarm con múltiples nodos")
                
                if not confirm_action("¿Deseas usarla de todas formas?", default_yes=False):
                    detected_ip = None
        
        # Si no se detectó o el usuario rechazó, pedir manualmente
        if not detected_ip:
            detected_ip = get_valid_input(
                "🌍 Ingresa la IP pública del servidor:",
                validate_ip,
                "❌ IP no válida. Debe ser una dirección IPv4 válida"
            )
        else:
            # Confirmar IP detectada
            print(f"\n🌐 IP detectada: {detected_ip}")
            if not confirm_action("¿Es correcta esta IP?", default_yes=True):
                detected_ip = get_valid_input(
                    "🌍 Ingresa la IP pública correcta:",
                    validate_ip,
                    "❌ IP no válida"
                )
        
        # Inicializar Swarm
        print(f"\n📡 Inicializando Swarm con IP: {detected_ip}")
        if run(f"docker swarm init --advertise-addr {detected_ip}"):
            print("✅ Swarm inicializado correctamente")
            
            # Guardar IP en state
            self.state_manager.update_component_field("prerequisites", "swarm_ip", detected_ip)
            return True
        else:
            print("❌ Error inicializando Swarm")
            return False
    
    def _create_network(self):
        """Crea la red overlay."""
        print("\n" + "─"*60)
        print(f"🌐 PASO 3/4: Creando red overlay '{self.network_name}'")
        print("─"*60)
        
        # Verificar si ya existe
        networks = run("docker network ls --format '{{.Name}}'", capture=True, check=False)
        if networks and self.network_name in networks.split('\n'):
            print(f"✅ Red '{self.network_name}' ya existe")
            network_info = run(
                f"docker network inspect {self.network_name} --format '{{{{.Driver}}}} - {{{{.Scope}}}}'",
                capture=True
            )
            print(f"   Tipo: {network_info}")
            return True
        
        # Crear red
        print(f"   Creando red overlay attachable...")
        if run(f"docker network create --driver overlay --attachable {self.network_name}"):
            print(f"✅ Red '{self.network_name}' creada correctamente")
            return True
        else:
            print(f"❌ Error creando red '{self.network_name}'")
            return False
    
    def _create_base_volumes(self):
        """Crea volúmenes base necesarios."""
        print("\n" + "─"*60)
        print("💾 PASO 4/4: Creando volúmenes base")
        print("─"*60)
        
        base_volumes = [
            "volume_swarm_certificates",  # Para Traefik
            "pgvector",                    # Para PostgreSQL
            "portainer_data",              # Para Portainer
            "evolution_instances",         # Para Evolution API
            "evolution_redis",             # Para Evolution API Redis
            "chatwoot_storage",            # Para Chatwoot
            "chatwoot_public",             # Para Chatwoot
            "chatwoot_mailer",             # Para Chatwoot
            "chatwoot_mailers",            # Para Chatwoot
            "chatwoot_redis"               # Para Chatwoot Redis
        ]
        
        created = 0
        existing = 0
        
        for volume in base_volumes:
            # Verificar si existe
            result = run(f"docker volume inspect {volume}", capture=True, check=False)
            
            if result:
                existing += 1
                print(f"  ✓ {volume} (ya existe)")
            else:
                # Crear volumen
                if run(f"docker volume create {volume}", check=False):
                    created += 1
                    print(f"  ✅ {volume} (creado)")
                else:
                    print(f"  ❌ {volume} (error)")
        
        print(f"\n📊 Resumen: {created} creados, {existing} ya existían")
        return True
    
    def uninstall(self):
        """Desinstala prerequisitos (con confirmación)."""
        print("\n⚠️  ADVERTENCIA: Esto eliminará Docker, Swarm y todos los contenedores")
        
        if not confirm_action("¿Estás SEGURO de continuar?", default_yes=False):
            print("❌ Operación cancelada")
            return False
        
        # Salir de Swarm
        print("\n🐝 Saliendo del Swarm...")
        run("docker swarm leave --force", check=False)
        
        # Detener Docker
        print("🛑 Deteniendo Docker...")
        run("systemctl stop docker.socket", check=False)
        run("systemctl stop docker", check=False)
        
        # Desinstalar paquetes
        print("🗑️  Desinstalando Docker...")
        run(
            "apt-get purge -y docker-ce docker-ce-cli containerd.io "
            "docker-compose-plugin docker-buildx-plugin",
            check=False
        )
        run("apt-get autoremove -y --purge", check=False)
        
        # Limpiar archivos
        print("🧹 Limpiando archivos...")
        run("rm -rf /var/lib/docker", check=False)
        run("rm -rf /var/lib/containerd", check=False)
        run("rm -rf /etc/docker", check=False)
        
        # Eliminar del state
        self.state_manager.remove_component(self.name)
        
        print("✅ Prerequisitos desinstalados")
        return True