#!/usr/bin/env python3
"""
Validadores de entrada del usuario.
"""

import re
import ipaddress
import sys


def validate_ip(ip):
    """Valida que sea una IP válida."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_domain(domain):
    """Valida formato de dominio."""
    # Permitir localhost para testing
    if domain.lower() in ['localhost', 'portainer.localhost', 'evolution.localhost', 'chatwoot.localhost']:
        return True
    
    # Validar dominio real (sin protocolo, sin path, sin puerto)
    pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return re.match(pattern, domain) is not None


def validate_email(email):
    """Valida formato de email."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_network_name(name):
    """Valida nombre de red Docker."""
    # Docker network names: alfanuméricos, guiones, guiones bajos
    # No pueden empezar con guión
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9_-]{0,62}$'
    return re.match(pattern, name) is not None


def validate_password(password):
    """
    Valida requisitos de seguridad de contraseña.
    
    Returns:
        Lista de errores (vacía si es válida)
    """
    errors = []
    
    if len(password) < 12:
        errors.append("❌ Debe tener al menos 12 caracteres")
    if not re.search(r'[A-Z]', password):
        errors.append("❌ Debe contener al menos una mayúscula")
    if not re.search(r'[a-z]', password):
        errors.append("❌ Debe contener al menos una minúscula")
    if not re.search(r'[0-9]', password):
        errors.append("❌ Debe contener al menos un número")
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:,.<>?]', password):
        errors.append("❌ Debe contener al menos un carácter especial")
    
    return errors


def validate_port(port):
    """Valida que sea un puerto válido."""
    try:
        port_int = int(port)
        return 1 <= port_int <= 65535
    except (ValueError, TypeError):
        return False


def get_valid_input(prompt, validator, error_message, max_attempts=3, default=None):
    """
    Solicita input del usuario con validación.
    
    Args:
        prompt: Mensaje a mostrar
        validator: Función que valida el input
        error_message: Mensaje de error
        max_attempts: Máximo de intentos
        default: Valor por defecto
    
    Returns:
        Input válido del usuario
    """
    if default:
        print(f"\n{prompt}")
        print(f"   Presiona ENTER para usar: {default}")
    else:
        print(f"\n{prompt}")
    
    for attempt in range(max_attempts):
        value = input("\n➡️  ").strip()
        
        # Si está vacío y hay default, usar default
        if not value and default:
            print(f"✅ Usando valor por defecto: {default}")
            return default
        
        # Validar
        if value and validator(value):
            print(f"✅ Valor válido: {value}")
            return value
        
        # Error
        print(f"\n{error_message}")
        if attempt < max_attempts - 1:
            print(f"🔁 Intento {attempt + 2} de {max_attempts}")
    
    # Máximo de intentos alcanzado
    print(f"\n❌ Máximo de intentos alcanzado")
    if default:
        print(f"⚠️  Usando valor por defecto: {default}")
        return default
    
    print("❌ No se pudo obtener un valor válido")
    sys.exit(1)


def get_secure_password(prompt_text, max_attempts=3):
    """
    Solicita contraseña segura con validación y confirmación.
    
    Args:
        prompt_text: Mensaje a mostrar
        max_attempts: Máximo de intentos
    
    Returns:
        Contraseña válida
    """
    import getpass
    
    print("\n🔐 Requisitos de contraseña:")
    print("   • Mínimo 12 caracteres")
    print("   • Al menos 1 mayúscula, 1 minúscula, 1 número")
    print("   • Al menos 1 carácter especial (@, #, $, %, etc.)")
    
    for attempt in range(max_attempts):
        password = getpass.getpass(f"\n{prompt_text}: ")
        
        # Validar requisitos
        errors = validate_password(password)
        if errors:
            print("\n⚠️  Contraseña no cumple requisitos:")
            for error in errors:
                print(f"   {error}")
            if attempt < max_attempts - 1:
                print(f"\n🔁 Intento {attempt + 2} de {max_attempts}")
            continue
        
        # Confirmar contraseña
        confirm = getpass.getpass("🔐 Confirma la contraseña: ")
        if password != confirm:
            print("❌ Las contraseñas no coinciden")
            if attempt < max_attempts - 1:
                print(f"\n🔁 Intento {attempt + 2} de {max_attempts}")
            continue
        
        print("✅ Contraseña válida y confirmada")
        return password
    
    print("\n❌ Máximo de intentos alcanzado")
    sys.exit(1)