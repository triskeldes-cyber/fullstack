#!/usr/bin/env python3
"""
Funciones auxiliares generales.
"""

import subprocess
import secrets
import string
import os


def run(cmd, capture=False, check=True):
    """
    Ejecuta un comando en shell.
    
    Args:
        cmd: Comando a ejecutar
        capture: Si True, retorna la salida
        check: Si True, lanza excepción en error
    
    Returns:
        True/False o la salida del comando
    """
    print(f"\n🔧 {cmd}")
    try:
        if capture:
            result = subprocess.run(
                cmd, 
                shell=True, 
                check=check, 
                text=True, 
                capture_output=True
            )
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True, check=check)
            return True
    except subprocess.CalledProcessError as e:
        if check:
            print(f"❌ Error: {e.stderr if e.stderr else e}")
            return False
        raise


def gen_secret(length=32, hex_only=False):
    """
    Genera una clave segura aleatoria.
    
    Args:
        length: Longitud de la clave
        hex_only: Si True, genera solo caracteres hexadecimales
    
    Returns:
        String con la clave generada
    """
    if hex_only:
        return secrets.token_hex(length // 2)
    else:
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))


def gen_secret_key_base():
    """
    Genera un SECRET_KEY_BASE para Rails (128 caracteres hex).
    """
    return secrets.token_hex(64)  # 128 caracteres


def get_public_ip():
    """
    Detecta automáticamente la IP pública del servidor.
    
    Returns:
        String con la IP pública o None si falla
    """
    print("\n🌍 Detectando IP pública del servidor...")
    
    # Método 1: ifconfig.me
    try:
        ip = subprocess.run(
            "curl -s --max-time 5 ifconfig.me",
            shell=True,
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
        
        if ip and validate_ip(ip):
            print(f"✅ IP pública detectada: {ip}")
            return ip
    except:
        pass
    
    # Método 2: ipify (fallback)
    try:
        ip = subprocess.run(
            "curl -s --max-time 5 https://api.ipify.org",
            shell=True,
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
        
        if ip and validate_ip(ip):
            print(f"✅ IP pública detectada: {ip}")
            return ip
    except:
        pass
    
    print("⚠️  No se pudo detectar la IP automáticamente")
    return None


def validate_ip(ip):
    """
    Valida que sea una IP válida.
    
    Args:
        ip: String con la IP a validar
    
    Returns:
        True si es válida, False si no
    """
    try:
        import ipaddress
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def confirm_action(message, default_yes=False):
    """
    Solicita confirmación del usuario.
    
    Args:
        message: Mensaje a mostrar
        default_yes: Si True, el default es 'sí'
    
    Returns:
        True si confirma, False si no
    """
    suffix = " (S/n): " if default_yes else " (s/N): "
    response = input(f"\n{message}{suffix}").strip().lower()
    
    if not response:
        return default_yes
    
    return response in ['s', 'si', 'sí', 'yes', 'y']


def create_directory(path):
    """
    Crea un directorio si no existe.
    
    Args:
        path: Ruta del directorio
    
    Returns:
        True si se creó o ya existía
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        print(f"❌ Error creando directorio {path}: {e}")
        return False


def require_root():
    """Verifica que se ejecute como root."""
    if os.geteuid() != 0:
        print("⚠️  Este script debe ejecutarse como root")
        print("   Ejecuta: sudo python3 setup_manager.py")
        import sys
        sys.exit(1)


def install_git():
    """Instala git si no está disponible."""
    if run("which git", capture=True, check=False):
        print("✅ Git ya está instalado")
        return True
    
    print("\n📦 Instalando Git...")
    return run("apt-get update && apt-get install -y git", check=True)


def clone_repo(url, dest):
    """
    Clona un repositorio git.
    
    Args:
        url: URL del repositorio
        dest: Directorio destino
    
    Returns:
        True si se clonó exitosamente
    """
    if os.path.exists(dest):
        print(f"\n⚠️  El directorio {dest} ya existe")
        if confirm_action("¿Deseas eliminarlo y clonar de nuevo?", default_yes=True):
            run(f"rm -rf {dest}")
        else:
            print("✅ Usando directorio existente")
            return True
    
    return run(f"git clone {url} {dest}")


def save_credentials(file_path, data):
    """
    Guarda credenciales en un archivo de texto.
    
    Args:
        file_path: Ruta del archivo
        data: Diccionario con las credenciales
    """
    try:
        with open(file_path, "w") as f:
            f.write("="*60 + "\n")
            f.write("CREDENCIALES DEL SISTEMA\n")
            f.write(f"Generado: {subprocess.run('date', shell=True, capture_output=True, text=True).stdout.strip()}\n")
            f.write("="*60 + "\n\n")
            
            for section, values in data.items():
                f.write(f"{section}:\n")
                for key, value in values.items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n")
        
        print(f"💾 Credenciales guardadas en: {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error guardando credenciales: {e}")
        return False