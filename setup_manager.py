#!/usr/bin/env python3
"""
Instalador Modular - Docker Swarm Stack
Gestión de aplicaciones en Docker Swarm con Traefik y Portainer.
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import VERSIONS, DEFAULTS
from utils import (
    require_root,
    install_git,
    clone_repo,
    create_directory,
    StateManager,
    confirm_action,
    save_credentials
)
from modules import (
    Prerequisites,
    Traefik,
    Portainer,
    PgVector,
    EvolutionAPI,
    Chatwoot
)


class SetupManager:
    """Gestor principal del instalador."""
    
    def __init__(self):
        """Inicializa el gestor."""
        self.state_file = DEFAULTS['state_file']
        self.state_manager = StateManager(self.state_file)
        self.install_dir = DEFAULTS['install_dir']
        self.repo_url = DEFAULTS['repo_url']
        
        # Inicializar módulos
        self.prerequisites = Prerequisites(self.state_manager)
        self.traefik = None
        self.portainer = None
        self.pgvector = None
        self.evolution = None
        self.chatwoot = None
    
    def _init_modules(self):
        """Inicializa módulos que requieren install_dir."""
        self.traefik = Traefik(self.state_manager, self.install_dir)
        self.portainer = Portainer(self.state_manager, self.install_dir)
        self.pgvector = PgVector(self.state_manager, self.install_dir)
        self.evolution = EvolutionAPI(self.state_manager, self.install_dir)
        self.chatwoot = Chatwoot(self.state_manager, self.install_dir)
    
    def print_banner(self):
        """Muestra el banner del instalador."""
        print("\n" + "╔" + "═"*58 + "╗")
        print("║" + " "*58 + "║")
        print("║" + "  INSTALADOR MODULAR - DOCKER SWARM STACK".center(58) + "║")
        print("║" + "  by TriskelDes".center(58) + "║")
        print("║" + " "*58 + "║")
        print("╚" + "═"*58 + "╝")
    
    def print_menu(self):
        """Muestra el menú principal."""
        print("\n" + "═"*60)
        print("MENÚ PRINCIPAL")
        print("═"*60)
        
        # Indicadores de estado
        prereq_status = "✅" if self.prerequisites.is_installed() else "⬜"
        traefik_status = "✅" if self.traefik and self.traefik.is_installed() else "⬜"
        portainer_status = "✅" if self.portainer and self.portainer.is_installed() else "⬜"
        pgvector_status = "✅" if self.pgvector and self.pgvector.is_installed() else "⬜"
        evolution_status = "✅" if self.evolution and self.evolution.is_installed() else "⬜"
        chatwoot_status = "✅" if self.chatwoot and self.chatwoot.is_installed() else "⬜"
        
        print("\n🚀 INICIO RÁPIDO:")
        print("  1. Quick Start (instala todo el stack completo)")
        
        print("\n⚙️  PREREQUISITOS:")
        print(f"  2. {prereq_status} Preparar entorno (Docker + Swarm + Red + Volúmenes)")
        
        print("\n🏗️  INFRAESTRUCTURA:")
        print(f"  3. {traefik_status} Instalar Traefik (Reverse Proxy + SSL)")
        print(f"  4. {portainer_status} Instalar Portainer (Gestión visual)")
        
        print("\n📦 APLICACIONES:")
        print(f"  5. {pgvector_status} Instalar PostgreSQL (con pgvector)")
        print(f"  6. {evolution_status} Instalar Evolution API")
        print(f"  7. {chatwoot_status} Instalar Chatwoot")
        print("  8. ⬜ Instalar n8n (próximamente)")
        
        print("\n📊 INFORMACIÓN:")
        print("  9. Ver estado del sistema")
        print("  10. Ver credenciales guardadas")
        
        print("\n🔧 MANTENIMIENTO:")
        print("  11. Ejecutar migraciones de Chatwoot")
        print("  12. Eliminar stack")
        print("  13. Backup de configuración")
        print("  14. Reset completo del sistema")
        
        print("\n  0. Salir")
        print("\n" + "═"*60)
    
    def setup_repository(self):
        """Clona el repositorio si no existe."""
        if not os.path.exists(self.install_dir):
            print("\n📦 Clonando repositorio de configuración...")
            
            # Instalar git si no está
            install_git()
            
            # Crear directorio padre
            create_directory(os.path.dirname(self.install_dir))
            
            # Clonar repo
            if clone_repo(self.repo_url, self.install_dir):
                print(f"✅ Repositorio clonado en {self.install_dir}")
                return True
            else:
                print("❌ Error clonando repositorio")
                return False
        else:
            print(f"✅ Repositorio ya existe en {self.install_dir}")
            
            # Preguntar si quiere actualizar
            if confirm_action("¿Deseas actualizar desde GitHub?", default_yes=False):
                print("\n🔄 Actualizando repositorio...")
                from utils import run
                if run(f"cd {self.install_dir} && git pull"):
                    print("✅ Repositorio actualizado")
                else:
                    print("⚠️  Error actualizando, usando versión local")
            
            return True
    
    def handle_quick_start(self):
        """Instalación rápida completa."""
        print("\n" + "═"*60)
        print("🚀 QUICK START - Instalación completa")
        print("═"*60)
        print("\nEsto instalará en orden:")
        print("  1. Docker + Swarm + Red")
        print("  2. Traefik (Reverse Proxy)")
        print("  3. Portainer (Gestión)")
        print("  4. PostgreSQL (Base de datos)")
        print("  5. Evolution API (WhatsApp)")
        print("  6. Chatwoot (Atención al cliente)")
        
        if not confirm_action("\n¿Deseas continuar?", default_yes=True):
            print("\n❌ Instalación cancelada")
            return
        
        # Configurar repositorio
        if not self.setup_repository():
            print("❌ No se pudo configurar el repositorio")
            return
        
        # Inicializar módulos
        self._init_modules()
        
        # Instalar en orden
        steps = [
            ("Prerequisitos", self.prerequisites),
            ("Traefik", self.traefik),
            ("Portainer", self.portainer),
            ("PostgreSQL", self.pgvector),
            ("Evolution API", self.evolution),
            ("Chatwoot", self.chatwoot)
        ]
        
        for i, (name, module) in enumerate(steps, 1):
            print(f"\n{'═'*60}")
            print(f"PASO {i}/{len(steps)}: {name}")
            print(f"{'═'*60}")
            
            # Verificar si ya está instalado
            if module.is_installed():
                print(f"✅ {name} ya está instalado")
                if not confirm_action(f"¿Deseas reinstalar {name}?", default_yes=False):
                    continue
            
            # Instalar
            if not module.install():
                print(f"\n❌ Error instalando {name}")
                if not confirm_action("¿Deseas continuar con el siguiente?", default_yes=True):
                    break
            
            # Pausa entre instalaciones
            if i < len(steps):
                input("\nPresiona ENTER para continuar con el siguiente componente...")
        
        # Resumen final
        self._show_final_summary()
    
    def handle_prerequisites(self):
        """Instala prerequisitos."""
        if not self.prerequisites.install():
            input("\nPresiona ENTER para continuar...")
    
    def handle_traefik(self):
        """Instala Traefik."""
        if not self.setup_repository():
            return
        
        self._init_modules()
        
        if not self.traefik.install():
            input("\nPresiona ENTER para continuar...")
    
    def handle_portainer(self):
        """Instala Portainer."""
        if not self.setup_repository():
            return
        
        self._init_modules()
        
        if not self.portainer.install():
            input("\nPresiona ENTER para continuar...")
    
    def handle_pgvector(self):
        """Instala PostgreSQL."""
        if not self.setup_repository():
            return
        
        self._init_modules()
        
        if not self.pgvector.install():
            input("\nPresiona ENTER para continuar...")
    
    def handle_evolution(self):
        """Instala Evolution API."""
        if not self.setup_repository():
            return
        
        self._init_modules()
        
        if not self.evolution.install():
            input("\nPresiona ENTER para continuar...")
    
    def handle_chatwoot(self):
        """Instala Chatwoot."""
        if not self.setup_repository():
            return
        
        self._init_modules()
        
        if not self.chatwoot.install():
            input("\nPresiona ENTER para continuar...")
    
    def handle_view_status(self):
        """Muestra el estado del sistema."""
        print("\n" + self.state_manager.get_summary())
    
    def handle_view_credentials(self):
        """Muestra las credenciales guardadas."""
        creds_file = DEFAULTS['credentials_file']
        
        if os.path.exists(creds_file):
            print("\n" + "="*60)
            with open(creds_file, 'r') as f:
                print(f.read())
            print("="*60)
        else:
            print("\n⚠️  No se encontró el archivo de credenciales")
            print(f"   Ubicación esperada: {creds_file}")
            
            # Ofrecer generar credenciales
            if confirm_action("¿Deseas generar el archivo de credenciales?", default_yes=True):
                self._generate_credentials_file()
    
    def handle_chatwoot_migrations(self):
        """Ejecuta migraciones de Chatwoot."""
        if not self.chatwoot:
            self._init_modules()
        
        if not self.chatwoot.is_installed():
            print("\n❌ Chatwoot no está instalado")
            print("   Instala Chatwoot primero (opción 7)")
            return
        
        self.chatwoot.run_migrations_manually()
    
    def handle_remove_stack(self):
        """Elimina un stack específico."""
        print("\n🗑️  ELIMINAR STACK")
        print("═"*60)
        
        installed = self.state_manager.get_all_installed()
        
        if not installed:
            print("\n⚠️  No hay componentes instalados")
            return
        
        print("\nComponentes instalados:")
        for i, component in enumerate(installed, 1):
            print(f"  {i}. {component}")
        
        print("\n  0. Cancelar")
        
        try:
            choice = int(input("\n➡️  Selecciona componente a eliminar: "))
            
            if choice == 0:
                return
            
            if 1 <= choice <= len(installed):
                component_name = installed[choice - 1]
                
                # Obtener módulo correspondiente
                self._init_modules()
                modules = {
                    'prerequisites': self.prerequisites,
                    'traefik': self.traefik,
                    'portainer': self.portainer,
                    'pgvector': self.pgvector,
                    'evolution': self.evolution,
                    'chatwoot': self.chatwoot
                }
                
                module = modules.get(component_name)
                if module:
                    module.uninstall()
                else:
                    print(f"❌ Módulo {component_name} no encontrado")
        except ValueError:
            print("❌ Opción inválida")
    
    def handle_backup(self):
        """Crea backup de la configuración."""
        print("\n💾 BACKUP DE CONFIGURACIÓN")
        print("═"*60)
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"/root/backup_swarm_{timestamp}"
        
        print(f"\nCreando backup en: {backup_dir}")
        
        if create_directory(backup_dir):
            # Exportar state
            state_backup = f"{backup_dir}/installation_state.json"
            self.state_manager.export_state(state_backup)
            
            # Copiar credenciales
            creds_file = DEFAULTS['credentials_file']
            if os.path.exists(creds_file):
                from utils import run
                run(f"cp {creds_file} {backup_dir}/")
            
            # Copiar configs de docker
            if os.path.exists(self.install_dir):
                from utils import run
                run(f"cp -r {self.install_dir} {backup_dir}/docker-config")
            
            print(f"\n✅ Backup creado en: {backup_dir}")
            print("\nContenido del backup:")
            print("  • Estado de instalación")
            print("  • Credenciales")
            print("  • Configuraciones Docker")
        else:
            print("❌ Error creando backup")
    
    def handle_reset(self):
        """Reset completo del sistema."""
        print("\n🔥 RESET COMPLETO DEL SISTEMA")
        print("═"*60)
        print("\n⚠️  ADVERTENCIA CRÍTICA:")
        print("   Esto eliminará COMPLETAMENTE:")
        print("   • Docker y todos los contenedores")
        print("   • Swarm")
        print("   • Todas las redes")
        print("   • Todos los volúmenes (DATOS PERMANENTES)")
        print("   • Todas las configuraciones")
        print("\n   ESTA ACCIÓN NO SE PUEDE DESHACER")
        
        if not confirm_action("\n¿Estás ABSOLUTAMENTE seguro?", default_yes=False):
            print("❌ Reset cancelado")
            return
        
        # Confirmación adicional
        confirm_text = input("\nEscribe 'RESET COMPLETO' para confirmar: ").strip()
        if confirm_text != "RESET COMPLETO":
            print("❌ Reset cancelado")
            return
        
        # Ejecutar reset
        self._init_modules()
        
        print("\n🗑️  Eliminando componentes...")
        
        # Eliminar en orden inverso
        components = [
            self.chatwoot,
            self.evolution,
            self.pgvector,
            self.portainer,
            self.traefik,
            self.prerequisites
        ]
        
        for component in components:
            if component and component.is_installed():
                print(f"\n  Eliminando {component.name}...")
                component.uninstall()
        
        # Limpiar estado
        print("\n🧹 Limpiando archivos de estado...")
        if os.path.exists(self.state_file):
            os.remove(self.state_file)
        
        print("\n✅ Reset completo finalizado")
        print("   El sistema está limpio y listo para una nueva instalación")
    
    def _generate_credentials_file(self):
        """Genera archivo de credenciales desde el state."""
        creds_data = {}
        
        # Portainer
        portainer_data = self.state_manager.get_component('portainer')
        if portainer_data:
            creds_data['Portainer'] = {
                'URL': portainer_data.get('url'),
                'Usuario': 'admin',
                'Contraseña': '(la que configuraste)'
            }
        
        # PostgreSQL
        pgvector_data = self.state_manager.get_component('pgvector')
        if pgvector_data:
            creds_data['PostgreSQL'] = {
                'Host': 'pgvector',
                'Puerto': 5432,
                'Usuario': 'postgres',
                'Password': pgvector_data.get('password')
            }
        
        # Evolution API
        evolution_data = self.state_manager.get_component('evolution')
        if evolution_data:
            creds_data['Evolution API'] = {
                'URL': evolution_data.get('url'),
                'API Key': evolution_data.get('api_key')
            }
        
        # Chatwoot
        chatwoot_data = self.state_manager.get_component('chatwoot')
        if chatwoot_data:
            creds_data['Chatwoot'] = {
                'URL': chatwoot_data.get('url'),
                'Empresa': chatwoot_data.get('empresa')
            }
        
        # Guardar
        if save_credentials(DEFAULTS['credentials_file'], creds_data):
            print("✅ Archivo de credenciales generado")
    
    def _show_final_summary(self):
        """Muestra resumen final de la instalación."""
        print("\n" + "╔" + "═"*58 + "╗")
        print("║" + " "*58 + "║")
        print("║" + "✅ INSTALACIÓN COMPLETADA".center(58) + "║")
        print("║" + " "*58 + "║")
        print("╚" + "═"*58 + "╝")
        
        # Mostrar URLs
        print("\n🔗 ACCESOS:")
        
        portainer_data = self.state_manager.get_component('portainer')
        if portainer_data:
            print(f"   Portainer: {portainer_data.get('url')}")
        
        evolution_data = self.state_manager.get_component('evolution')
        if evolution_data:
            print(f"   Evolution API: {evolution_data.get('url')}")
        
        chatwoot_data = self.state_manager.get_component('chatwoot')
        if chatwoot_data:
            print(f"   Chatwoot: {chatwoot_data.get('url')}")
        
        print("\n📋 Ver credenciales completas: Opción 10 del menú")
        print("\n⚠️  NOTAS IMPORTANTES:")
        print("   • Los certificados SSL pueden tardar 1-2 minutos")
        print("   • Si el navegador muestra advertencia SSL, es temporal")
        print("   • Usa modo incógnito si tienes problemas de caché")
        
        # Generar archivo de credenciales
        self._generate_credentials_file()
    
    def run(self):
        """Ejecuta el instalador."""
        self.print_banner()
        
        # Loop principal
        while True:
            self.print_menu()
            
            try:
                option = input("\n➡️  Selecciona una opción: ").strip()
                
                if option == "0":
                    print("\n👋 ¡Hasta luego!")
                    sys.exit(0)
                
                elif option == "1":
                    self.handle_quick_start()
                
                elif option == "2":
                    self.handle_prerequisites()
                
                elif option == "3":
                    self.handle_traefik()
                
                elif option == "4":
                    self.handle_portainer()
                
                elif option == "5":
                    self.handle_pgvector()
                
                elif option == "6":
                    self.handle_evolution()
                
                elif option == "7":
                    self.handle_chatwoot()
                
                elif option == "8":
                    print("\n⚠️  n8n - Próximamente")
                
                elif option == "9":
                    self.handle_view_status()
                
                elif option == "10":
                    self.handle_view_credentials()
                
                elif option == "11":
                    self.handle_chatwoot_migrations()
                
                elif option == "12":
                    self.handle_remove_stack()
                
                elif option == "13":
                    self.handle_backup()
                
                elif option == "14":
                    self.handle_reset()
                
                else:
                    print("\n❌ Opción inválida")
                
                # Pausa antes de mostrar el menú
                input("\nPresiona ENTER para continuar...")
                
            except KeyboardInterrupt:
                print("\n\n👋 Instalación interrumpida por el usuario")
                sys.exit(0)
            except Exception as e:
                print(f"\n❌ Error inesperado: {e}")
                import traceback
                traceback.print_exc()
                input("\nPresiona ENTER para continuar...")


def main():
    """Función principal."""
    require_root()
    
    manager = SetupManager()
    manager.run()


if __name__ == "__main__":
    main()