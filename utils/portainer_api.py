#!/usr/bin/env python3
"""
Cliente para la API de Portainer.
Permite desplegar stacks directamente desde el script.
"""

import requests
import urllib3
import time


# Suprimir warnings de SSL self-signed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PortainerAPI:
    """Cliente para la API de Portainer."""
    
    def __init__(self, url, verify_ssl=False):
        """
        Inicializa el cliente.
        
        Args:
            url: URL base de Portainer (ej: https://portainer.example.com)
            verify_ssl: Si True, verifica certificados SSL
        """
        self.url = url.rstrip('/')
        self.verify_ssl = verify_ssl
        self.token = None
    
    def authenticate(self, username, password, max_attempts=3):
        """
        Autentica en Portainer y obtiene token JWT.
        
        Args:
            username: Usuario de Portainer
            password: Contraseña
            max_attempts: Máximo de intentos
        
        Returns:
            True si autenticó exitosamente, False si no
        """
        print("\n🔐 Autenticando en Portainer...")
        
        for attempt in range(max_attempts):
            try:
                response = requests.post(
                    f"{self.url}/api/auth",
                    json={"username": username, "password": password},
                    verify=self.verify_ssl,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.token = response.json().get('jwt')
                    print("✅ Autenticación exitosa")
                    return True
                else:
                    print(f"❌ Error de autenticación: HTTP {response.status_code}")
                    if attempt < max_attempts - 1:
                        print(f"🔁 Reintentando... ({attempt + 2}/{max_attempts})")
                        time.sleep(5)
            except requests.exceptions.RequestException as e:
                print(f"❌ Error conectando a Portainer: {e}")
                if attempt < max_attempts - 1:
                    print(f"🔁 Reintentando... ({attempt + 2}/{max_attempts})")
                    time.sleep(5)
        
        print("❌ No se pudo autenticar en Portainer")
        return False
    
    def get_endpoints(self):
        """
        Obtiene la lista de endpoints (environments).
        
        Returns:
            Lista de endpoints o None si falla
        """
        if not self.token:
            print("❌ No autenticado. Llama a authenticate() primero")
            return None
        
        try:
            response = requests.get(
                f"{self.url}/api/endpoints",
                headers={"Authorization": f"Bearer {self.token}"},
                verify=self.verify_ssl,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error obteniendo endpoints: HTTP {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            return None
    
    def get_endpoint_id(self):
        """
        Obtiene el ID del primer endpoint disponible.
        
        Returns:
            ID del endpoint o None
        """
        endpoints = self.get_endpoints()
        
        if endpoints and len(endpoints) > 0:
            endpoint_id = endpoints[0]['Id']
            endpoint_name = endpoints[0]['Name']
            print(f"✅ Endpoint encontrado: {endpoint_name} (ID: {endpoint_id})")
            return endpoint_id
        else:
            print("⚠️  No se encontraron endpoints")
            return None
    
    def deploy_stack(self, endpoint_id, stack_name, compose_content, env_vars=None):
        """
        Despliega un stack usando la API de Portainer.
        
        Args:
            endpoint_id: ID del endpoint
            stack_name: Nombre del stack
            compose_content: Contenido del docker-compose.yml
            env_vars: Diccionario con variables de entorno
        
        Returns:
            True si desplegó exitosamente, False si no
        """
        print(f"\n🚀 Desplegando stack '{stack_name}' vía Portainer API...")
        
        if not self.token:
            print("❌ No autenticado")
            return False
        
        # Preparar variables de entorno
        env_list = []
        if env_vars:
            for key, value in env_vars.items():
                env_list.append({"name": key, "value": str(value)})
        
        payload = {
            "Name": stack_name,
            "SwarmID": "",
            "StackFileContent": compose_content,
            "Env": env_list
        }
        
        try:
            response = requests.post(
                f"{self.url}/api/stacks",
                params={
                    "type": 1,  # 1 = Swarm, 2 = Compose
                    "method": "string",
                    "endpointId": endpoint_id
                },
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                json=payload,
                verify=self.verify_ssl,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Stack '{stack_name}' desplegado correctamente")
                return True
            elif response.status_code == 409:
                print(f"⚠️  Stack '{stack_name}' ya existe")
                # Intentar actualizarlo
                return self.update_stack(endpoint_id, stack_name, compose_content, env_vars)
            else:
                print(f"❌ Error desplegando stack: HTTP {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            return False
    
    def get_stack_id(self, stack_name):
        """
        Obtiene el ID de un stack por su nombre.
        
        Args:
            stack_name: Nombre del stack
        
        Returns:
            ID del stack o None
        """
        if not self.token:
            return None
        
        try:
            response = requests.get(
                f"{self.url}/api/stacks",
                headers={"Authorization": f"Bearer {self.token}"},
                verify=self.verify_ssl,
                timeout=10
            )
            
            if response.status_code == 200:
                stacks = response.json()
                for stack in stacks:
                    if stack['Name'] == stack_name:
                        return stack['Id']
            return None
        except:
            return None
    
    def update_stack(self, endpoint_id, stack_name, compose_content, env_vars=None):
        """
        Actualiza un stack existente.
        
        Args:
            endpoint_id: ID del endpoint
            stack_name: Nombre del stack
            compose_content: Nuevo contenido del compose
            env_vars: Nuevas variables de entorno
        
        Returns:
            True si actualizó, False si no
        """
        print(f"\n🔄 Actualizando stack '{stack_name}'...")
        
        stack_id = self.get_stack_id(stack_name)
        if not stack_id:
            print(f"❌ No se encontró el stack '{stack_name}'")
            return False
        
        # Preparar variables
        env_list = []
        if env_vars:
            for key, value in env_vars.items():
                env_list.append({"name": key, "value": str(value)})
        
        payload = {
            "StackFileContent": compose_content,
            "Env": env_list,
            "Prune": False
        }
        
        try:
            response = requests.put(
                f"{self.url}/api/stacks/{stack_id}",
                params={"endpointId": endpoint_id},
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                json=payload,
                verify=self.verify_ssl,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Stack '{stack_name}' actualizado")
                return True
            else:
                print(f"❌ Error actualizando: HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            return False
    
    def wait_for_portainer(self, max_wait=60):
        """
        Espera a que Portainer esté disponible.
        
        Args:
            max_wait: Segundos máximos a esperar
        
        Returns:
            True si está disponible, False si timeout
        """
        print(f"\n⏳ Esperando a que Portainer esté disponible...")
        
        for i in range(max_wait):
            try:
                response = requests.get(
                    f"{self.url}/api/status",
                    verify=self.verify_ssl,
                    timeout=5
                )
                if response.status_code == 200:
                    print("✅ Portainer está listo")
                    return True
            except:
                pass
            
            if i % 10 == 0 and i > 0:
                print(f"   Esperando... ({i}s/{max_wait}s)")
            
            time.sleep(1)
        
        print("❌ Timeout esperando a Portainer")
        return False