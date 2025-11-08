#!/usr/bin/env python3
"""
Gestor de estado de la instalación.
Guarda y recupera información sobre componentes instalados.
"""

import json
import os
from datetime import datetime


class StateManager:
    """Gestiona el estado de la instalación."""
    
    def __init__(self, state_file):
        """
        Inicializa el gestor de estado.
        
        Args:
            state_file: Ruta al archivo de estado JSON
        """
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self):
        """Carga el estado desde el archivo."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️  Archivo de estado corrupto, creando nuevo")
                return self._create_default_state()
        else:
            return self._create_default_state()
    
    def _create_default_state(self):
        """Crea un estado por defecto."""
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "components": {}
        }
    
    def _save_state(self):
        """Guarda el estado en el archivo."""
        self.state["last_updated"] = datetime.now().isoformat()
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error guardando estado: {e}")
            return False
    
    def set_component(self, component_name, data):
        """
        Guarda información de un componente.
        
        Args:
            component_name: Nombre del componente (ej: 'docker', 'postgres')
            data: Diccionario con la información
        """
        if "components" not in self.state:
            self.state["components"] = {}
        
        self.state["components"][component_name] = {
            **data,
            "installed_at": datetime.now().isoformat(),
            "installed": True
        }
        
        return self._save_state()
    
    def get_component(self, component_name):
        """
        Recupera información de un componente.
        
        Args:
            component_name: Nombre del componente
        
        Returns:
            Diccionario con la info o None si no existe
        """
        return self.state.get("components", {}).get(component_name)
    
    def is_installed(self, component_name):
        """
        Verifica si un componente está instalado.
        
        Args:
            component_name: Nombre del componente
        
        Returns:
            True si está instalado, False si no
        """
        component = self.get_component(component_name)
        return component is not None and component.get("installed", False)
    
    def remove_component(self, component_name):
        """
        Elimina un componente del estado.
        
        Args:
            component_name: Nombre del componente
        """
        if component_name in self.state.get("components", {}):
            del self.state["components"][component_name]
            return self._save_state()
        return True
    
    def get_all_installed(self):
        """
        Obtiene todos los componentes instalados.
        
        Returns:
            Lista de nombres de componentes instalados
        """
        return [
            name for name, data in self.state.get("components", {}).items()
            if data.get("installed", False)
        ]
    
    def get_postgres_password(self):
        """
        Recupera la contraseña de PostgreSQL del estado.
        
        Returns:
            String con la contraseña o None
        """
        pgvector = self.get_component("pgvector")
        if pgvector:
            return pgvector.get("password")
        return None
    
    def get_network_name(self):
        """
        Recupera el nombre de la red Docker del estado.
        
        Returns:
            String con el nombre de la red o None
        """
        network = self.get_component("network")
        if network:
            return network.get("name")
        return None
    
    def update_component_field(self, component_name, field, value):
        """
        Actualiza un campo específico de un componente.
        
        Args:
            component_name: Nombre del componente
            field: Campo a actualizar
            value: Nuevo valor
        """
        if component_name in self.state.get("components", {}):
            self.state["components"][component_name][field] = value
            return self._save_state()
        return False
    
    def export_state(self, export_path):
        """
        Exporta el estado a otro archivo.
        
        Args:
            export_path: Ruta del archivo de exportación
        """
        try:
            with open(export_path, 'w') as f:
                json.dump(self.state, f, indent=2)
            print(f"✅ Estado exportado a: {export_path}")
            return True
        except Exception as e:
            print(f"❌ Error exportando estado: {e}")
            return False
    
    def get_summary(self):
        """
        Obtiene un resumen del estado actual.
        
        Returns:
            String con el resumen formateado
        """
        components = self.state.get("components", {})
        installed = [name for name, data in components.items() if data.get("installed")]
        
        summary = []
        summary.append("="*60)
        summary.append("ESTADO DEL SISTEMA")
        summary.append("="*60)
        summary.append(f"Componentes instalados: {len(installed)}")
        summary.append("")
        
        for name in installed:
            data = components[name]
            summary.append(f"✅ {name}")
            if "version" in data:
                summary.append(f"   Versión: {data['version']}")
            if "installed_at" in data:
                summary.append(f"   Instalado: {data['installed_at']}")
        
        summary.append("="*60)
        return "\n".join(summary)