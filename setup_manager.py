#!/usr/bin/env python3
import subprocess
import sys
import os

def run_command(command, shell=False):
    """Ejecuta un comando y retorna el resultado"""
    try:
        if shell:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command.split(), capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error ejecutando comando: {command}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Excepción ejecutando comando: {e}")
        return False

def check_root():
    """Verifica si el script se ejecuta como root"""
    if os.geteuid() != 0:
        print("Este script debe ejecutarse como root o con sudo")
        sys.exit(1)

def install_docker():
    """Instala Docker en Ubuntu"""
    print("🔧 Instalando Docker...")
    
    # Actualizar paquetes
    if not run_command("apt update"):
        return False
    
    # Instalar dependencias
    dependencies = [
        "apt-transport-https",
        "ca-certificates",
        "curl",
        "gnupg",
        "lsb-release"
    ]
    
    for dep in dependencies:
        if not run_command(f"apt install -y {dep}"):
            return False
    
    # Agregar clave GPG de Docker
    if not run_command("curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg", shell=True):
        return False
    
    # Agregar repositorio de Docker
    codename = subprocess.run("lsb_release -cs", shell=True, capture_output=True, text=True).stdout.strip()
    repo_cmd = f'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu {codename} stable" > /etc/apt/sources.list.d/docker.list'
    
    if not run_command(repo_cmd, shell=True):
        return False
    
    # Actualizar e instalar Docker
    if not run_command("apt update"):
        return False
    
    if not run_command("apt install -y docker-ce docker-ce-cli containerd.io"):
        return False
    
    # Iniciar y habilitar servicio Docker
    if not run_command("systemctl start docker"):
        return False
    
    if not run_command("systemctl enable docker"):
        return False
    
    # Agregar usuario actual al grupo docker (opcional)
    current_user = os.getenv('SUDO_USER')
    if current_user:
        if not run_command(f"usermod -aG docker {current_user}"):
            print("⚠️  No se pudo agregar el usuario al grupo docker, pero la instalación continuará")
    
    print("✅ Docker instalado correctamente")
    return True

def create_docker_network(network_name):
    """Crea una red Docker attachable"""
    print(f"🌐 Creando red Docker: {network_name}")
    
    # Verificar si la red ya existe
    check_cmd = f"docker network ls --filter name={network_name} --format '{{.Name}}'"
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    
    if network_name in result.stdout:
        print(f"⚠️  La red '{network_name}' ya existe")
        return True
    
    # Crear la red con attachable: true
    create_cmd = f"docker network create --driver overlay --attachable {network_name}"
    if run_command(create_cmd, shell=True):
        print(f"✅ Red '{network_name}' creada exitosamente")
        return True
    else:
        print(f"❌ Error creando la red '{network_name}'")
        return False

def init_swarm():
    """Inicializa Docker Swarm"""
    print("🐳 Inicializando Docker Swarm...")
    
    # Verificar si Swarm ya está inicializado
    check_cmd = "docker info --format '{{.Swarm.LocalNodeState}}'"
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    
    if 'active' in result.stdout:
        print("⚠️  Docker Swarm ya está inicializado")
        return True
    
    # Inicializar Swarm
    if run_command("docker swarm init", shell=True):
        print("✅ Docker Swarm inicializado correctamente")
        
        # Mostrar información del swarm
        print("\n📋 Información del Swarm:")
        run_command("docker node ls", shell=True)
        return True
    else:
        print("❌ Error inicializando Docker Swarm")
        return False

def main():
    """Función principal del script"""
    print("🚀 Script de instalación de Docker y configuración de Swarm")
    print("=" * 50)
    
    # Verificar permisos de root
    check_root()
    
    # Interacción para el nombre de la red
    while True:
        network_name = input("\n📝 Ingresa el nombre para la red Docker (debe seguir las convenciones de Docker): ").strip()
        
        if network_name:
            # Validación básica del nombre
            if all(c.isalnum() or c in '_-' for c in network_name) and not network_name.startswith(('-', '_')):
                break
            else:
                print("❌ El nombre debe contener solo letras, números, guiones y guiones bajos, y no puede empezar con guión")
        else:
            print("❌ El nombre no puede estar vacío")
    
    print(f"\n🔍 Resumen de la configuración:")
    print(f"   - Red Docker: {network_name}")
    print(f"   - Tipo: overlay")
    print(f"   - Attachable: true")
    
    confirm = input("\n¿Continuar con la instalación? (s/N): ").strip().lower()
    if confirm not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Instalación cancelada")
        sys.exit(0)
    
    # Proceso de instalación
    print("\n" + "=" * 50)
    
    # 1. Instalar Docker
    if not install_docker():
        print("❌ Error en la instalación de Docker")
        sys.exit(1)
    
    # 2. Inicializar Swarm
    if not init_swarm():
        print("❌ Error inicializando Swarm")
        sys.exit(1)
    
    # 3. Crear red Docker
    if not create_docker_network(network_name):
        print("❌ Error creando la red Docker")
        sys.exit(1)
    
    # Mostrar resumen final
    print("\n" + "=" * 50)
    print("🎉 ¡Instalación completada exitosamente!")
    print(f"📋 Resumen:")
    print(f"   ✅ Docker instalado y funcionando")
    print(f"   ✅ Docker Swarm inicializado")
    print(f"   ✅ Red '{network_name}' creada (attachable: true)")
    print("\n🔧 Comandos útiles:")
    print(f"   - Ver redes: docker network ls")
    print(f"   - Ver nodos: docker node ls")
    print(f"   - Inspeccionar red: docker network inspect {network_name}")
    print(f"   - Unirse al swarm (otros nodos): docker swarm join-token worker")

if __name__ == "__main__":
    main()