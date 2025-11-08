#!/usr/bin/env python3
"""
Clase base para componentes del instalador.
Todos los módulos heredan de esta clase.
"""

from abc import ABC, abstractmethod


class Component(ABC):
    """
    Clase base abstracta para componentes instalables.
    
    Cada componente (Docker, Traefik, Portainer, etc.) debe heredar
    de esta clase e implementar los métodos abstractos.
    """
    
    def __init__(self, name, description, state_manager):
        """
        Inicializa el componente.
        
        Args:
            name: Nombre del componente (ej: 'docker', 'traefik')
            description: Descripción del componente
            state_manager: Instancia de StateManager
        """
        self.name = name
        self.description = description
        self.state_manager = state_manager
        self.dependencies = []
    
    @abstractmethod
    def install(self):
        """
        Instala el componente.
        
        Returns:
            True si instaló exitosamente, False si no
        """
        pass
    
    @abstractmethod
    def is_installed(self):
        """
        Verifica si el componente está instalado.
        
        Returns:
            True si está instalado, False si no
        """
        pass
    
    def update(self):
        """
        Actualiza el componente.
        Por defecto, desinstala y reinstala.
        
        Returns:
            True si actualizó exitosamente
        """
        print(f"\n🔄 Actualizando {self.name}...")
        if self.uninstall():
            return self.install()
        return False
    
    def uninstall(self):
        """
        Desinstala el componente.
        Por defecto, solo elimina del state.
        Los componentes específicos deben sobrescribir esto.
        
        Returns:
            True si desinstaló exitosamente
        """
        print(f"\n🗑️ Desinstalando {self.name}...")
        self.state_manager.remove_component(self.name)
        print(f"✅ {self.name} eliminado del estado")
        return True
    
    def get_status(self):
        """
        Obtiene el estado actual del componente.
        
        Returns:
            Diccionario con información del estado
        """
        component_data = self.state_manager.get_component(self.name)
        
        if component_data:
            return {
                "installed": True,
                "data": component_data
            }
        else:
            return {
                "installed": False,
                "data": None
            }
    
    def check_dependencies(self):
        """
        Verifica que todas las dependencias estén instaladas.
        
        Returns:
            tuple: (bool, list) - (todas_ok, lista_de_faltantes)
        """
        missing = []
        
        for dep in self.dependencies:
            if not self.state_manager.is_installed(dep):
                missing.append(dep)
        
        return (len(missing) == 0, missing)
    
    def print_header(self):
        """Imprime un header bonito para el componente."""
        print("\n" + "="*60)
        print(f"📦 {self.description}")
        print("="*60)
    
    def print_success(self, message=None):
        """Imprime mensaje de éxito."""
        if message:
            print(f"\n✅ {message}")
        else:
            print(f"\n✅ {self.name} instalado correctamente")
    
    def print_error(self, message=None):
        """Imprime mensaje de error."""
        if message:
            print(f"\n❌ {message}")
        else:
            print(f"\n❌ Error instalando {self.name}")
    
    def save_to_state(self, data):
        """
        Guarda información del componente en el state.
        
        Args:
            data: Diccionario con la información a guardar
        
        Returns:
            True si guardó exitosamente
        """
        return self.state_manager.set_component(self.name, data)
    
    def get_from_state(self):
        """
        Recupera información del componente del state.
        
        Returns:
            Diccionario con la información o None
        """
        return self.state_manager.get_component(self.name)


class StackComponent(Component):
    """
    Clase base para componentes que se despliegan como stacks.
    Hereda de Component y agrega funcionalidad específica de stacks.
    """
    
    def __init__(self, name, description, state_manager, compose_path):
        """
        Inicializa el componente de stack.
        
        Args:
            name: Nombre del componente
            description: Descripción
            state_manager: Instancia de StateManager
            compose_path: Ruta al docker-compose.yml
        """
        super().__init__(name, description, state_manager)
        self.compose_path = compose_path
        self.stack_name = name
    
    def deploy_via_cli(self, compose_file, stack_name=None):
        """
        Despliega el stack usando Docker CLI.
        
        Args:
            compose_file: Ruta al docker-compose.yml
            stack_name: Nombre del stack (usa self.stack_name si no se especifica)
        
        Returns:
            True si desplegó exitosamente
        """
        from utils.helpers import run
        import os
        
        if not os.path.exists(compose_file):
            self.print_error(f"No se encontró el archivo: {compose_file}")
            return False
        
        stack = stack_name or self.stack_name
        
        return run(f"docker stack deploy -c {compose_file} {stack}")
    
    def deploy_via_portainer(self, portainer_api, endpoint_id, compose_content, env_vars):
        """
        Despliega el stack usando la API de Portainer.
        
        Args:
            portainer_api: Instancia de PortainerAPI
            endpoint_id: ID del endpoint
            compose_content: Contenido del docker-compose.yml
            env_vars: Diccionario con variables de entorno
        
        Returns:
            True si desplegó exitosamente
        """
        return portainer_api.deploy_stack(
            endpoint_id,
            self.stack_name,
            compose_content,
            env_vars
        )
    
    def remove_stack(self):
        """
        Elimina el stack usando Docker CLI.
        
        Returns:
            True si eliminó exitosamente
        """
        from utils.helpers import run
        
        print(f"\n🗑️ Eliminando stack {self.stack_name}...")
        if run(f"docker stack rm {self.stack_name}"):
            print(f"✅ Stack {self.stack_name} eliminado")
            return True
        return False
    
    def is_stack_running(self):
        """
        Verifica si el stack está corriendo.
        
        Returns:
            True si está corriendo, False si no
        """
        from utils.helpers import run
        
        result = run(f"docker stack ps {self.stack_name} --format '{{{{.CurrentState}}}}'", capture=True, check=False)
        
        if result and "Running" in result:
            return True
        return False
    
    def get_stack_services(self):
        """
        Obtiene la lista de servicios del stack.
        
        Returns:
            Lista de nombres de servicios o lista vacía
        """
        from utils.helpers import run
        
        result = run(f"docker stack services {self.stack_name} --format '{{{{.Name}}}}'", capture=True, check=False)
        
        if result:
            return result.split('\n')
        return []
    
    def wait_for_stack(self, timeout=60):
        """
        Espera a que el stack esté completamente desplegado.
        
        Args:
            timeout: Segundos máximos a esperar
        
        Returns:
            True si está listo, False si timeout
        """
        import time
        
        print(f"⏳ Esperando a que {self.stack_name} esté listo...")
        
        for i in range(timeout):
            if self.is_stack_running():
                print(f"✅ {self.stack_name} está operativo")
                return True
            
            if i % 10 == 0 and i > 0:
                print(f"   Esperando... ({i}s/{timeout}s)")
            
            time.sleep(1)
        
        print(f"⚠️  Timeout esperando a {self.stack_name}")
        return False