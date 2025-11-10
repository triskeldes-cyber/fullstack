#!/usr/bin/env python3
import subprocess
import sys
import os

def run_command(command, shell=False):
    """Ejecuta un comando y muestra el output en tiempo real"""
    try:
        if shell:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        else:
            process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # Mostrar output en tiempo real
        for line in process.stdout:
            print(line, end='')
        
        process.wait()
        return process.returncode == 0
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
        return False

def check_root():
    """Verifica si el script se ejecuta como root"""
    if os.geteuid() != 0:
        print("❌ Este script debe ejecutarse como root o con sudo")
        sys.exit(1)

def install_docker_simple():
    """Instala Docker usando el método simple"""
    print("🚀 Instalando Docker...")
    print("=" * 50)
    
    # Paso 1: Actualizar sistema e instalar apparmor-utils
    print("📦 Paso 1: Actualizando sistema e instalando dependencias...")
    if not run_command("apt-get update"):
        return False
    
    if not run_command("apt-get install -y apparmor-utils"):
        print("⚠️  Continuando sin apparmor-utils...")
    
    # Paso 2: Configurar hostname (opcional)
    print("\n🏷️  Paso 2: Configurando hostname...")
    hostname = input("¿Quieres configurar un hostname? (ej: manager1) [s/N]: ").strip().lower()
    if hostname in ['s', 'si', 'sí', 'y', 'yes']:
        new_hostname = input("Ingresa el hostname: ").strip()
        if new_hostname:
            run_command(f"hostnamectl set-hostname {new_hostname}")
            print(f"✅ Hostname configurado como: {new_hostname}")
    
    # Paso 3: Instalar Docker con el script oficial
    print("\n🐳 Paso 3: Instalando Docker con script oficial...")
    print("📥 Descargando e instalando Docker...")
    if run_command("curl -fsSL https://get.docker.com | bash", shell=True):
        print("✅ Docker instalado correctamente")
    else:
        print("❌ Error instalando Docker")
        return False
    
    return True

def configure_swarm_and_network():
    """Configura Swarm y crea la red"""
    print("\n🔧 Paso 4: Configurando Docker Swarm y red...")
    
    # Inicializar Swarm
    print("🐳 Inicializando Docker Swarm...")
    if run_command("docker swarm init"):
        print("✅ Docker Swarm inicializado")
    else:
        print("❌ Error inicializando Swarm (puede que ya esté inicializado)")
    
    # Crear red overlay
    network_name = input("\n📝 Ingresa el nombre para la red overlay: ").strip()
    if not network_name:
        network_name = "network_public"
        print(f"🔧 Usando nombre por defecto: {network_name}")
    
    print(f"🌐 Creando red: {network_name}")
    if run_command(f"docker network create --driver=overlay --attachable {network_name}"):
        print(f"✅ Red '{network_name}' creada exitosamente")
    else:
        print("❌ Error creando la red (puede que ya exista)")
    
    return True

def show_final_info():
    """Muestra información final"""
    print("\n" + "=" * 50)
    print("🎉 ¡Configuración completada!")
    print("=" * 50)
    
    # Mostrar información del sistema
    print("\n📊 Información del sistema:")
    run_command("docker --version")
    print()
    run_command("docker node ls")
    print()
    run_command("docker network ls")
    
    print("\n🔧 Comandos útiles:")
    print("   - Ver nodos: docker node ls")
    print("   - Ver redes: docker network ls")
    print("   - Unir otro nodo: docker swarm join-token worker")
    print("   - Ver servicios: docker service ls")
    
    print("\n⚠️  Recuerda:")
    print("   - Si agregaste un usuario al grupo docker, cierra y abre la sesión")
    print("   - Para usar swarm en otros nodos, usa: docker swarm join-token worker")

def main():
    """Función principal"""
    print("🚀 Script de instalación simple de Docker y Swarm")
    print("Basado en tu método probado y efectivo")
    print("=" * 50)
    
    # Verificar permisos
    check_root()
    
    # Confirmar instalación
    confirm = input("¿Continuar con la instalación? [s/N]: ").strip().lower()
    if confirm not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Instalación cancelada")
        sys.exit(0)
    
    # Instalar Docker
    if not install_docker_simple():
        print("❌ Error en la instalación de Docker")
        sys.exit(1)
    
    # Configurar Swarm y red
    if not configure_swarm_and_network():
        print("❌ Error configurando Swarm y red")
        sys.exit(1)
    
    # Mostrar información final
    show_final_info()

if __name__ == "__main__":
    main()