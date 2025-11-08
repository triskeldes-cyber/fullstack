#!/usr/bin/env python3
"""
Módulo de PostgreSQL con pgvector.
Instala PostgreSQL con la extensión pgvector para IA/embeddings.
"""

import os
from .base import StackComponent
from utils import (
    run,
    gen_secret,
    confirm_action
)
from config import DEFAULTS


class PgVector(StackComponent):
    """Maneja la instalación de PostgreSQL con pgvector."""
    
    def __init__(self, state_manager, install_dir):
        super().__init__(
            name="pgvector",
            description="PostgreSQL con pgvector",
            state_manager=state_manager,
            compose_path=f"{install_dir}/pgvector/docker-compose.yml"
        )
        self.install_dir = install_dir
        self.dependencies = ["prerequisites"]
    
    def install(self):
        """Instala PostgreSQL con pgvector."""
        self.print_header()
        
        # Verificar dependencias
        deps_ok, missing = self.check_dependencies()
        if not deps_ok:
            self.print_error(f"Faltan dependencias: {', '.join(missing)}")
            return False
        
        # Verificar si ya está instalado
        if self.is_installed():
            print("⚠️  PostgreSQL ya está instalado")
            if not confirm_action("¿Deseas reinstalar? (PERDERÁS TODOS LOS DATOS)", default_yes=False):
                return False
            
            print("\n⚠️  ADVERTENCIA FINAL: Todos los datos de las bases serán eliminados")
            if not confirm_action("¿Estás SEGURO?", default_yes=False):
                return False
            
            self.remove_stack()
        
        # Obtener configuración
        network = self.state_manager.get_network_name() or DEFAULTS['network']
        
        # Generar contraseña segura
        print("\n🔐 Generando contraseña de PostgreSQL...")
        postgres_password = gen_secret(32)
        print(f"✅ Contraseña generada: {postgres_password[:8]}... (guardada en state)")
        
        # Verificar compose
        if not os.path.exists(self.compose_path):
            self.print_error(f"No se encontró {self.compose_path}")
            return False
        
        # Reemplazar variables
        print("\n📝 Configurando PostgreSQL...")
        if not self._replace_variables(network, postgres_password):
            self.print_error("Error configurando variables")
            return False
        
        # Desplegar stack
        print("\n🚀 Desplegando PostgreSQL...")
        if not self.deploy_via_cli(self.compose_path, "pgvector"):
            self.print_error("Error desplegando PostgreSQL")
            return False
        
        # Esperar a que esté listo
        print("\n⏳ Esperando a que PostgreSQL esté operativo...")
        if not self.wait_for_stack(timeout=60):
            print("⚠️  PostgreSQL tardó en iniciar")
        
        # Guardar en state
        self.save_to_state({
            "network": network,
            "password": postgres_password,
            "host": "pgvector",
            "port": 5432,
            "user": "postgres",
            "version": "pgvector:pg16",
            "compose_path": self.compose_path
        })
        
        self.print_success()
        print(f"\n🗄️  PostgreSQL configurado:")
        print(f"   Host: pgvector")
        print(f"   Puerto: 5432")
        print(f"   Usuario: postgres")
        print(f"   Password: {postgres_password}")
        print(f"   Versión: pgvector:pg16 (PostgreSQL 16 + pgvector)")
        print("\n📝 IMPORTANTE:")
        print("   • La contraseña ha sido guardada en el state")
        print("   • Las apps la usarán automáticamente")
        print("   • Cada app creará su propia base de datos")
        
        return True
    
    def is_installed(self):
        """Verifica si PostgreSQL está instalado."""
        if not self.state_manager.is_installed(self.name):
            return False
        
        result = run("docker stack ps pgvector --format '{{.CurrentState}}'", capture=True, check=False)
        return result and "Running" in result
    
    def _replace_variables(self, network, password):
        """Reemplaza variables en el docker-compose.yml"""
        try:
            with open(self.compose_path, 'r') as f:
                content = f.read()
            
            # Reemplazar variables
            content = content.replace('${NETWORK}', network)
            content = content.replace('${POSTGRES_PASSWORD}', password)
            
            # Guardar
            with open(self.compose_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Variables configuradas")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def uninstall(self):
        """Desinstala PostgreSQL."""
        print("\n⚠️  ADVERTENCIA CRÍTICA:")
        print("   Esto eliminará PostgreSQL y TODAS las bases de datos")
        print("   • Evolution API perderá todos los datos")
        print("   • Chatwoot perderá todos los datos")
        print("   • Esta acción NO se puede deshacer")
        
        if not confirm_action("¿Estás SEGURO de continuar?", default_yes=False):
            return False
        
        print("\n⚠️  Última confirmación")
        confirm_text = input("Escribe 'ELIMINAR TODO' para confirmar: ").strip()
        
        if confirm_text != "ELIMINAR TODO":
            print("❌ Operación cancelada")
            return False
        
        if self.remove_stack():
            # Opcional: eliminar volumen
            if confirm_action("¿Deseas eliminar también el volumen de datos?", default_yes=False):
                run("docker volume rm pgvector", check=False)
            
            self.state_manager.remove_component(self.name)
            print("✅ PostgreSQL desinstalado")
            return True
        
        return False
    
    def get_connection_string(self, database="postgres"):
        """
        Genera string de conexión a PostgreSQL.
        
        Args:
            database: Nombre de la base de datos
        
        Returns:
            String de conexión o None
        """
        data = self.get_from_state()
        if not data:
            return None
        
        password = data.get("password")
        host = data.get("host", "pgvector")
        port = data.get("port", 5432)
        user = data.get("user", "postgres")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def test_connection(self):
        """
        Prueba la conexión a PostgreSQL.
        
        Returns:
            True si conecta, False si no
        """
        print("\n🔍 Probando conexión a PostgreSQL...")
        
        result = run(
            "docker exec $(docker ps | grep pgvector_postgres | awk '{print $1}') "
            "psql -U postgres -c 'SELECT version();'",
            capture=True,
            check=False
        )
        
        if result and "PostgreSQL" in result:
            print("✅ Conexión exitosa")
            print(f"   {result.split('(')[0].strip()}")
            return True
        else:
            print("❌ No se pudo conectar")
            return False