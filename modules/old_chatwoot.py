#!/usr/bin/env python3
"""
Módulo de Chatwoot.
Instala Chatwoot para atención al cliente omnicanal.
"""

import os
import time
from .base import StackComponent
from utils import (
    run,
    gen_secret_key_base,
    get_valid_input,
    validate_domain,
    validate_email,
    validate_port,
    confirm_action
)
from config import DEFAULTS


class Chatwoot(StackComponent):
    """Maneja la instalación de Chatwoot."""
    
    def __init__(self, state_manager, install_dir):
        super().__init__(
            name="chatwoot",
            description="Chatwoot - Atención al Cliente",
            state_manager=state_manager,
            compose_path=f"{install_dir}/chatwoot/docker-compose.yml"
        )
        self.install_dir = install_dir
        self.dependencies = ["prerequisites", "traefik", "pgvector"]
    
    def install(self):
        """Instala Chatwoot."""
        self.print_header()
        
        # Verificar dependencias
        deps_ok, missing = self.check_dependencies()
        if not deps_ok:
            self.print_error(f"Faltan dependencias: {', '.join(missing)}")
            print(f"   Instala primero: {', '.join(missing)}")
            return False
        
        # Verificar si ya está instalado
        if self.is_installed():
            print("⚠️  Chatwoot ya está instalado")
            if not confirm_action("¿Deseas reinstalar?", default_yes=False):
                return False
            self.remove_stack()
        
        # Obtener configuración base
        network = self.state_manager.get_network_name() or DEFAULTS['network']
        
        # CORRECCIÓN: Recuperar password de PostgreSQL correctamente
        print("\n🔍 Recuperando configuración de PostgreSQL...")
        pgvector_data = self.state_manager.get_component('pgvector')
        
        if not pgvector_data:
            self.print_error("PostgreSQL (pgvector) no está instalado")
            print("   Instala PostgreSQL primero (opción 5)")
            return False
        
        postgres_password = pgvector_data.get('password')
        
        if not postgres_password:
            self.print_error("No se encontró la contraseña de PostgreSQL en el state")
            print("   Reinstala PostgreSQL (opción 5)")
            print(f"\n   Debug - State de pgvector: {pgvector_data}")
            return False
        
        print(f"✅ Contraseña de PostgreSQL recuperada del state")
        print(f"   Password: {postgres_password[:8]}... (primeros 8 caracteres)")
        
        # Solicitar configuración al usuario
        print("\n" + "═"*60)
        print("CONFIGURACIÓN DE CHATWOOT")
        print("═"*60)
        
        print("\n🏢 Información de la empresa")
        nombre_empresa = input("Nombre de la empresa: ").strip()
        if not nombre_empresa:
            nombre_empresa = "Mi Empresa"
        
        print("\n🌍 Configuración de dominio")
        domain = get_valid_input(
            "Dominio para Chatwoot (ej: chatwoot.tudominio.com):",
            validate_domain,
            "❌ Dominio no válido",
            default="chatwoot.localhost"
        )
        
        # Configuración SMTP
        print("\n📧 Configuración SMTP (para envío de emails)")
        print("   Ejemplos de proveedores:")
        print("   • Gmail: smtp.gmail.com, puerto 587, SSL=false")
        print("   • Outlook: smtp-mail.outlook.com, puerto 587, SSL=false")
        print("   • SendGrid: smtp.sendgrid.net, puerto 587, SSL=false")
        
        email = get_valid_input(
            "\nEmail del remitente:",
            validate_email,
            "❌ Email no válido"
        )
        
        dominio_email = input("Dominio del email (ej: tudominio.com): ").strip()
        if not dominio_email:
            dominio_email = domain.split('.', 1)[-1] if '.' in domain else "localhost"
        
        smtp_address = input("Host SMTP (ej: smtp.gmail.com): ").strip()
        if not smtp_address:
            smtp_address = "smtp.gmail.com"
        
        port = get_valid_input(
            "Puerto SMTP (587 o 465):",
            validate_port,
            "❌ Puerto no válido",
            default="587"
        )
        
        ssl = "false"
        if port == "465":
            ssl = "true"
        else:
            ssl_choice = input("¿Usar SSL? (s/n) [n]: ").strip().lower()
            if ssl_choice == 's':
                ssl = "true"
        
        usuario = input(f"Usuario SMTP [{email}]: ").strip()
        if not usuario:
            usuario = email
        
        import getpass
        smtp_password = getpass.getpass("Contraseña SMTP: ")
        
        # Generar SECRET_KEY_BASE
        print("\n🔐 Generando SECRET_KEY_BASE...")
        secret_key_base = gen_secret_key_base()
        print(f"✅ Secret generado: {secret_key_base[:16]}...")
        
        # Verificar compose
        if not os.path.exists(self.compose_path):
            self.print_error(f"No se encontró {self.compose_path}")
            return False
        
        # Reemplazar variables
        print("\n📝 Configurando Chatwoot...")
        variables = {
            'NETWORK': network,
            'NOMBRE_EMPRESA': nombre_empresa,
            'URL_CHATWOOT': domain,
            'SECRET_KEY_BASE': secret_key_base,
            'EMAIL': email,
            'DOMINIO_EMAIL': dominio_email,
            'SMTP_ADDRESS': smtp_address,
            'PORT': port,
            'SSL': ssl,
            'USUARIO': usuario,
            'SMTP_PASSWORD': smtp_password,
            'POSTGRES_PASSWORD': postgres_password
        }
        
        print(f"\n📊 Variables configuradas:")
        print(f"   Network: {network}")
        print(f"   Domain: {domain}")
        print(f"   Postgres Password: {postgres_password[:8]}...")
        
        if not self._replace_variables(variables):
            self.print_error("Error configurando variables")
            return False
        
        # Desplegar stack
        print("\n🚀 Desplegando Chatwoot...")
        if not self.deploy_via_cli(self.compose_path, "chatwoot"):
            self.print_error("Error desplegando Chatwoot")
            return False
        
        # Esperar a que esté listo
        print("\n⏳ Esperando a que Chatwoot esté operativo...")
        if not self.wait_for_stack(timeout=90):
            print("⚠️  Chatwoot tardó en iniciar")
        
        # Guardar en state
        self.save_to_state({
            "network": network,
            "domain": domain,
            "url": f"https://{domain}",
            "empresa": nombre_empresa,
            "email": email,
            "database": "chatwoot",
            "secret_key_base": secret_key_base,
            "compose_path": self.compose_path
        })
        
        # Mostrar instrucciones post-instalación
        self._show_post_install_instructions(domain)
        
        return True
    
    def is_installed(self):
        """Verifica si Chatwoot está instalado."""
        if not self.state_manager.is_installed(self.name):
            return False
        
        result = run("docker stack ps chatwoot --format '{{.CurrentState}}'", capture=True, check=False)
        return result and "Running" in result
    
    def _replace_variables(self, variables):
        """Reemplaza variables en el docker-compose.yml"""
        try:
            with open(self.compose_path, 'r') as f:
                content = f.read()
            
            # Reemplazar todas las variables
            for key, value in variables.items():
                content = content.replace(f'${{{key}}}', str(value))
            
            # Guardar
            with open(self.compose_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Variables configuradas")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def _show_post_install_instructions(self, domain):
        """Muestra instrucciones post-instalación."""
        print("\n" + "═"*60)
        print("✅ CHATWOOT DESPLEGADO")
        print("═"*60)
        print(f"\n🔗 URL: https://{domain}")
        
        print("\n⚠️  PASO ADICIONAL REQUERIDO - MIGRACIÓN DE BASE DE DATOS")
        print("═"*60)
        print("Chatwoot necesita preparar la base de datos.")
        print("Este proceso puede tardar varios minutos.")
        print("═"*60)
        
        # Preguntar si quiere ejecutar automáticamente
        auto = confirm_action(
            "\n¿Ejecutar migraciones automáticamente?",
            default_yes=True
        )
        
        if auto:
            self._run_migrations()
        else:
            self._show_manual_migration_instructions()
    
    def _run_migrations(self):
        """Ejecuta las migraciones automáticamente."""
        print("\n⏳ Esperando 90 segundos a que Chatwoot inicie completamente...")
        time.sleep(90)
        
        print("\n🔍 Buscando contenedor de Chatwoot...")
        container_id = run(
            "docker ps | grep chatwoot_app | awk '{print $1}'",
            capture=True,
            check=False
        )
        
        if not container_id:
            print("❌ No se encontró el contenedor de Chatwoot")
            self._show_manual_migration_instructions()
            return False
        
        print(f"✅ Contenedor encontrado: {container_id}")
        print("\n🚀 Ejecutando migraciones...")
        print("   (Esto puede tardar 5-10 minutos, por favor espera...)")
        
        # Ejecutar migraciones
        result = run(
            f"docker exec {container_id} bundle exec rails db:chatwoot_prepare",
            capture=True,
            check=False
        )
        
        if result:
            print("\n✅ Migraciones completadas exitosamente")
            print("\n🎉 Chatwoot está listo para usar")
            return True
        else:
            print("\n❌ Error ejecutando migraciones")
            self._show_manual_migration_instructions()
            return False
    
    def _show_manual_migration_instructions(self):
        """Muestra instrucciones manuales para migraciones."""
        print("\n📋 INSTRUCCIONES MANUALES")
        print("═"*60)
        print("\n1. Espera 1-2 minutos a que Chatwoot inicie")
        print("\n2. Ejecuta estos comandos:")
        print("\n   # Entrar al contenedor:")
        print("   docker exec -it $(docker ps | grep chatwoot_app | awk '{print $1}') sh")
        print("\n   # Ejecutar migraciones (dentro del contenedor):")
        print("   bundle exec rails db:chatwoot_prepare")
        print("\n   # Salir del contenedor:")
        print("   exit")
        print("\n3. Espera a que termine (puede tardar 5-10 minutos)")
        print("\n4. Accede a Chatwoot y crea tu primera cuenta")
        print("═"*60)
    
    def run_migrations_manually(self):
        """Ejecuta las migraciones manualmente (para llamar desde el menú)."""
        print("\n🔧 EJECUTAR MIGRACIONES DE CHATWOOT")
        print("═"*60)
        
        if not self.is_installed():
            print("❌ Chatwoot no está instalado")
            return False
        
        return self._run_migrations()
    
    def uninstall(self):
        """Desinstala Chatwoot."""
        print("\n⚠️  Esto eliminará Chatwoot y todos sus datos")
        print("   • Conversaciones")
        print("   • Contactos")
        print("   • Configuraciones")
        
        if not confirm_action("¿Continuar?", default_yes=False):
            return False
        
        if self.remove_stack():
            # Opcional: eliminar volúmenes
            if confirm_action("¿Deseas eliminar también los volúmenes de datos?", default_yes=False):
                run("docker volume rm chatwoot_storage", check=False)
                run("docker volume rm chatwoot_public", check=False)
                run("docker volume rm chatwoot_mailer", check=False)
                run("docker volume rm chatwoot_mailers", check=False)
                run("docker volume rm chatwoot_redis", check=False)
            
            self.state_manager.remove_component(self.name)
            print("✅ Chatwoot desinstalado")
            return True
        
        return False