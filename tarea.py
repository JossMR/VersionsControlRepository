import os
import shutil
import json
import datetime
import msvcrt
import uuid
from cmd import Cmd

class FileManagementSystem:

    def __init__(self, root_path):
        self.root_path = os.path.abspath(root_path)
        self.users_file = os.path.join(self.root_path, ".usuarios.json")
        self.versions_dir = os.path.join(self.root_path, ".versiones")
        self.users = {}
        self.current_user = None
        
        # Crear la estructura inicial si no existe
        self._initialize_system()
    
    def _initialize_system(self):
        # Crear carpeta raíz si no existe
        if not os.path.exists(self.root_path):
            os.makedirs(self.root_path)
            print(f"Carpeta raíz creada en: {self.root_path}")
        
        # Crear directorio de versiones
        if not os.path.exists(self.versions_dir):
            os.makedirs(self.versions_dir)
        
        # Cargar información de usuarios si existe
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            except json.JSONDecodeError:
                print("Error al cargar el archivo de usuarios. Creando nuevo archivo.")
                self.users = {}
                self._save_users()
        else:
            self._save_users()
    
    def _save_users(self):
        # Guarda la información de los usuarios en el archivo .json
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, indent=4)
    
    def register_user(self, username, password):
        # Registra un nuevo usuario
        if username in self.users:
            return False, "El nombre de usuario ya existe."
        
        # Crear estructura de usuario
        self.users[username] = {
            "password": password,
            "temporal_dir": os.path.join(self.root_path, username, "temporal"),
            "permanente_dir": os.path.join(self.root_path, username, "permanente"),
            "permissions": {}  # permisos a otras carpetas
        }
        
        # Crear carpetas del usuario temporal y permanente
        os.makedirs(self.users[username]["temporal_dir"], exist_ok=True)
        os.makedirs(self.users[username]["permanente_dir"], exist_ok=True)
        
        self._save_users()
        return True, f"Usuario {username} registrado correctamente."
    
    def login(self, username, password):
        # Inicia sesión con un usuario existente
        if username not in self.users:
            return False, "Usuario no encontrado."
        
        if password != self.users[username]["password"]:
            return False, "Contraseña incorrecta."
        
        self.current_user = username
        return True, f"Sesión iniciada como {username}."
    
    def logout(self):
        # Cerrar la sesión actual
        if not self.current_user:
            return False, "No hay sesión activa."
        
        self.current_user = None
        return True, "Sesión cerrada correctamente."
    
    def grant_permission(self, target_user, permission_type):
        # Otorga permisos a otro usuario sobre la carpeta del usuario actual "lectura" o "escritura"
        if not self.current_user:
            return False, "Iniciar sesión primero"
        
        if target_user not in self.users:
            return False, f"El usuario {target_user} no existe."
        
        if target_user == self.current_user:
            return False, "No puede cambiar sus propios permisos."
        
        if permission_type not in ["lectura", "escritura"]:
            return False, "Tipo de permiso no válido usar 'lectura' o 'escritura'."
        
        # Actualizar permisos del usuario objetivo
        self.users[self.current_user]["permissions"][target_user] = permission_type
        
        # Crear carpeta temporal para este usuario
        access_temporal_dir = os.path.join(self.root_path, target_user, "access", self.current_user)
        os.makedirs(access_temporal_dir, exist_ok=True)
        
        self._save_users()
        return True, f"Permiso '{permission_type}' otorgado a {target_user}."
    
    def revoke_permission(self, target_user):
        # Quita los permisos dados a un usuario
        if not self.current_user:
            return False, "Debe iniciar sesión primero."
        
        if target_user not in self.users:
            return False, f"El usuario {target_user} no existe."
        
        if target_user not in self.users[self.current_user]["permissions"]:
            return False, f"{target_user} no tiene permisos sobre su carpeta."
        
        # Eliminar permisos
        del self.users[self.current_user]["permissions"][target_user]
        
        # Eliminar carpeta de acceso temporal
        access_temporal_dir = os.path.join(self.root_path, target_user, "access",self.current_user)
        if os.path.exists(access_temporal_dir):
            shutil.rmtree(access_temporal_dir)
        
        # Verificar si la carpeta "access" está vacía y eliminarla también
        access_dir = os.path.join(self.root_path, target_user, "access")
        if os.path.exists(access_dir) and not os.listdir(access_dir):
            os.rmdir(access_dir)
        
        self._save_users()
        return True, f"Permisos revocados para {target_user}."
    
    def list_files(self, dir_type="temporal"):
        # Lista los archivos en una carpeta del usuario actual
        if not self.current_user:
            return False, "Debe iniciar sesión primero."
        
        if dir_type not in ["temporal", "permanente"]:
            return False, "Tipo de directorio no válido. Use 'temporal' o 'permanente'."
        
        directory = self.users[self.current_user][f"{dir_type}_dir"]
        files = []
        
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path):
                    files.append(item)
        except Exception as e:
            return False, f"Error al listar archivos: {str(e)}"
        
        return True, files
    
    def list_accessible_folders(self):
        # Lista las carpetas a las que el usuario actual tiene acceso
        if not self.current_user:
            return False, "Iniciar sesión primero."
        
        accessible = []
        for user, data in self.users.items():
            if self.current_user in data.get("permissions", {}):
                perm_type = data["permissions"][self.current_user]
                accessible.append((user, perm_type))

        return True, accessible
    
    def create_file(self, filename, content, owner=None):
        if not self.current_user:
            return False, "Iniciar sesión primero."

        # Si no se especifica un dueño, crear el archivo en la carpeta temporal del usuario actual
        if not owner:
            directory = self.users[self.current_user]["temporal_dir"]
            file_path = os.path.join(directory, filename)
        else:
            # Verificar que el owner (otro usuario) existe
            if owner not in self.users:
                return False, f"El usuario '{owner}' no existe."
            
            # Verificar si el usuario actual tiene permisos de escritura para el dueño especificado
            if self.current_user not in self.users.get(owner, {}).get("permissions", {}) or \
            self.users[owner]["permissions"][self.current_user] != "escritura":
                return False, f"No tienes permisos de escritura sobre los archivos de {owner}."
            
            # Ruta para la carpeta access/owner del usuario actual
            access_owner_dir = os.path.join(self.root_path, self.current_user, "access", owner)

            # Verificar si la carpeta existe, si no, crearla
            if not os.path.exists(access_owner_dir):
                try:
                    os.makedirs(access_owner_dir)
                except Exception as e:
                    return False, f"Error al crear directorio de acceso: {str(e)}"
            
            file_path = os.path.join(access_owner_dir, filename)

        # Crear el archivo (vacío o con contenido)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            return False, f"Error al crear archivo: {str(e)}"

        # Mensaje de confirmación según donde se creó el archivo
        if not owner:
            return True, f"Archivo '{filename}' creado correctamente en carpeta temporal."
        else:
            return True, f"Archivo '{filename}' creado correctamente en carpeta access/{owner}."
    
    def modify_file(self, filename, dir_type="temporal", owner=None):
        # Actualiza la fecha de modificación de un archivo existente
        if not self.current_user:
            return False, "Debe iniciar sesión primero."
        
        if dir_type == "temporal":
            directory = self.users[self.current_user]["temporal_dir"]
        elif dir_type == "access":
            if not owner:
                return False, "Debe especificar el dueño para modificar archivos en 'access'."
            if owner not in self.users:
                return False, f"El usuario '{owner}' no existe."
            if self.current_user not in self.users[owner]["permissions"] or \
               self.users[owner]["permissions"][self.current_user] != "escritura":
                return False, f"No tienes permisos de escritura sobre los archivos de {owner}."
            directory = os.path.join(self.root_path, self.current_user, "access", owner)
        else:
            return False, "Tipo de directorio no válido. Use 'temporal' o 'access'."
        
        file_path = os.path.join(directory, filename)
        
        if not os.path.exists(file_path):
            return False, f"El archivo '{filename}' no existe."
        
        try:
            # Actualizar la fecha de modificación del archivo
            current_time = datetime.datetime.now().timestamp()
            os.utime(file_path, (current_time, current_time))
        except Exception as e:
            return False, f"Error al actualizar la fecha del archivo: {str(e)}"
        
        return True, f"Archivo '{filename}' modificado correctamente."
    
    def delete_file(self, filename, dir_type="temporal", owner=None):
        # Elimina un archivo
        if not self.current_user:
            return False, "Debe iniciar sesión primero."
        
        if dir_type not in ["temporal", "access"]:
            return False, "Tipo de directorio no válido. Use 'temporal' o 'access'."
        
        if dir_type == "temporal":
            directory = self.users[self.current_user]["temporal_dir"]
        elif dir_type == "access":
            if not owner:
                return False, "Debe especificar el dueño para eliminar archivos en 'access'."
            if owner not in self.users:
                return False, f"El usuario '{owner}' no existe."
            if self.current_user not in self.users[owner]["permissions"] or \
               self.users[owner]["permissions"][self.current_user] != "escritura":
                return False, f"No tienes permisos de escritura sobre los archivos de {owner}."
            directory = os.path.join(self.root_path, self.current_user, "access", owner)
        
        file_path = os.path.join(directory, filename)
        
        if not os.path.exists(file_path):
            return False, f"El archivo '{filename}' no existe."
        
        try:
            os.remove(file_path)
        except Exception as e:
            return False, f"Error al eliminar archivo: {str(e)}"
        
        return True, f"Archivo '{filename}' eliminado correctamente."
    
    def commit(self, owner=None):
        if not self.current_user:
            return False, "Debe iniciar sesión primero."
        
        # Modo: commit <dueño>
        if owner:
            # Carpeta access específica del usuario actual hacia el dueño indicado
            access_path = os.path.join(self.root_path, self.current_user, "access", owner)
            if not os.path.exists(access_path):
                return False, f"No hay carpeta de acceso para el usuario '{owner}'."
            
            # Verificar si el usuario actual tiene permisos de escritura sobre el dueño
            if self.current_user not in self.users.get(owner, {}).get("permissions", {}) or \
               self.users[owner]["permissions"][self.current_user] != "escritura":
                return False, f"No tienes permisos de escritura sobre los archivos de {owner}."
            
            # Obtener carpeta permanente del dueño
            owner_info = self.users.get(owner)
            if not owner_info:
                return False, f"No se encontró información del usuario '{owner}'."
            
            permanente_dir = owner_info["permanente_dir"]

            # Crear una versión de la carpeta permanente del dueño
            if os.path.exists(permanente_dir) and os.listdir(permanente_dir):
                version_id = str(uuid.uuid4())
                version_dir = os.path.join(self.versions_dir, owner, version_id)
                os.makedirs(version_dir, exist_ok=True)
                
                version_info = {
                    "version_id": version_id,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "user": self.current_user,
                    "source": "access"
                }
                
                with open(os.path.join(version_dir, "metadata.json"), 'w', encoding='utf-8') as f:
                    json.dump(version_info, f, indent=4)
                
                for item in os.listdir(permanente_dir):
                    item_path = os.path.join(permanente_dir, item)
                    if os.path.isfile(item_path):
                        shutil.copy2(item_path, version_dir)

            try:
                # Sincronizar archivos: eliminar los que no están en access y actualizar los existentes
                access_files = set(os.listdir(access_path))
                permanente_files = set(os.listdir(permanente_dir))

                # Eliminar archivos que ya no están en access
                for file in permanente_files - access_files:
                    file_path = os.path.join(permanente_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)

                # Copiar o actualizar archivos desde access a permanente
                for file in access_files:
                    src_path = os.path.join(access_path, file)
                    dst_path = os.path.join(permanente_dir, file)
                    shutil.copy2(src_path, dst_path)

            except Exception as e:
                return False, f"Error al sincronizar archivos: {str(e)}"

            return True, f"Commit realizado para la carpeta permanente de '{owner}'."

        # Modo: commit (sin argumentos) => pasar temporal propio a permanente
        else:
            temporal_dir = self.users[self.current_user]["temporal_dir"]
            permanente_dir = self.users[self.current_user]["permanente_dir"]
            
            # Crear una versión de la carpeta permanente propia
            if os.path.exists(permanente_dir) and os.listdir(permanente_dir):
                version_id = str(uuid.uuid4())
                version_dir = os.path.join(self.versions_dir, self.current_user, version_id)
                os.makedirs(version_dir, exist_ok=True)
                
                version_info = {
                    "version_id": version_id,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "user": self.current_user,
                    "source": "temporal"
                }
                
                with open(os.path.join(version_dir, "metadata.json"), 'w', encoding='utf-8') as f:
                    json.dump(version_info, f, indent=4)
                
                for item in os.listdir(permanente_dir):
                    item_path = os.path.join(permanente_dir, item)
                    if os.path.isfile(item_path):
                        shutil.copy2(item_path, version_dir)
        
            # Limpiar permanente y pasar archivos desde temporal
            for item in os.listdir(permanente_dir):
                item_path = os.path.join(permanente_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
        
            for item in os.listdir(temporal_dir):
                item_path = os.path.join(temporal_dir, item)
                if os.path.isfile(item_path):
                    shutil.copy2(item_path, permanente_dir)
        
            return True, "Commit completo realizado correctamente."

    def update(self, target_user=None):
        if not self.current_user:
            return False, "Debe iniciar sesión primero."

        # actualizar access/usuario
        if target_user:
            if target_user not in self.users:
                return False, f"El usuario '{target_user}' no existe."

            if self.current_user not in self.users[target_user]["permissions"]:
                return False, f"No tiene permisos para acceder a los archivos de {target_user}."

            access_temporal_dir = os.path.join(self.root_path, self.current_user, "access", target_user)
            os.makedirs(access_temporal_dir, exist_ok=True)

            target_perm_dir = self.users[target_user]["permanente_dir"]

            # Limpiar carpeta access
            for item in os.listdir(access_temporal_dir):
                item_path = os.path.join(access_temporal_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)

            # Copiar archivos de permanente a access
            for item in os.listdir(target_perm_dir):
                item_path = os.path.join(target_perm_dir, item)
                if os.path.isfile(item_path):
                    shutil.copy2(item_path, access_temporal_dir)

            return True, f"Archivos de {target_user} actualizados correctamente."

        # actualizar la carpeta temporal propia
        temporal_dir = self.users[self.current_user]["temporal_dir"]
        permanente_dir = self.users[self.current_user]["permanente_dir"]

        for item in os.listdir(temporal_dir):
            item_path = os.path.join(temporal_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)

        for item in os.listdir(permanente_dir):
            item_path = os.path.join(permanente_dir, item)
            if os.path.isfile(item_path):
                shutil.copy2(item_path, temporal_dir)

        return True, "Update realizado correctamente."
 
    def list_versions(self):
        # Lista las versiones disponibles para el usuario actual
        if not self.current_user:
            return False, "Debe iniciar sesión primero."
        
        user_versions_dir = os.path.join(self.versions_dir, self.current_user)
        if not os.path.exists(user_versions_dir):
            return True, []
        
        versions = []
        try:
            for version_id in os.listdir(user_versions_dir):
                metadata_path = os.path.join(user_versions_dir, version_id, "metadata.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        versions.append(metadata)
        except Exception as e:
            return False, f"Error al listar versiones: {str(e)}"
        
        # Ordenar por fecha, más reciente primero
        versions.sort(key=lambda x: x["timestamp"], reverse=True)
        return True, versions
    
    def recover_version(self, recover_type="carpeta"):
        # Recupera una versión anterior de los archivos
        # recover_type: 'carpeta' para recuperar toda la carpeta, 'archivo' para un archivo específico
        if not self.current_user:
            return False, "Debe iniciar sesión primero."

        # Obtener todas las versiones disponibles
        success, versions = self.list_versions()
        if not success:
            return False, versions

        if not versions:
            return False, "No hay versiones disponibles."

        # Mostrar las versiones disponibles
        print("Versiones disponibles:")
        for i, version in enumerate(versions):
            timestamp = datetime.datetime.fromisoformat(version["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            print(f"{i + 1}. ID: {version['version_id']} - Fecha: {timestamp}")

        # Solicitar al usuario el número de versión
        try:
            version_index = int(input("Ingrese el número de la versión que desea recuperar: ")) - 1
            if version_index < 0 or version_index >= len(versions):
                return False, "Número de versión inválido."
        except ValueError:
            return False, "El índice debe ser un número válido."

        # Obtener el ID de la versión seleccionada
        version_id = versions[version_index]["version_id"]
        version_dir = os.path.join(self.versions_dir, self.current_user, version_id)

        if not os.path.exists(version_dir):
            return False, f"La versión {version_id} no existe."

        permanente_dir = self.users[self.current_user]["permanente_dir"]

        if recover_type == "carpeta":
            # Recuperar toda la carpeta
            # Eliminar archivos actuales en la carpeta permanente
            for item in os.listdir(permanente_dir):
                item_path = os.path.join(permanente_dir, item)
                if os.path.isfile(item_path) and item != "metadata.json":
                    os.remove(item_path)

            # Copiar todos los archivos de la versión a la carpeta permanente
            for item in os.listdir(version_dir):
                item_path = os.path.join(version_dir, item)
                if os.path.isfile(item_path) and item != "metadata.json":
                    shutil.copy2(item_path, permanente_dir)

            return True, f"Carpeta permanente recuperada de la versión {version_id}."

        elif recover_type == "archivo":
            # Recuperar un archivo específico
            # Listar los archivos disponibles en la versión seleccionada
            print("Archivos disponibles en la versión seleccionada:")
            files = [file for file in os.listdir(version_dir) if file != "metadata.json"]
            for file in files:
                print(f"  - {file}")

            # Solicitar al usuario el nombre del archivo
            filename = input("Ingrese el nombre del archivo que desea recuperar: ").strip()
            if filename not in files:
                return False, f"El archivo '{filename}' no existe en la versión seleccionada."

            # Recuperar el archivo específico
            src_path = os.path.join(version_dir, filename)
            dst_path = os.path.join(permanente_dir, filename)
            shutil.copy2(src_path, dst_path)

            return True, f"Archivo '{filename}' recuperado de la versión {version_id}."

        else:
            return False, "Tipo de recuperación no válido."

    def listar_archivos_version(self, version_index):
        # Lista los archivos de una versión específica por índice
        if not self.current_user:
            return False, "Debe iniciar sesión primero."
        
        # Obtener todas las versiones disponibles
        success, versions = self.list_versions()
        if not success:
            return False, versions
        
        if not versions:
            return False, "No hay versiones disponibles."
        
        # Verificar si el índice es válido
        try:
            version_index = int(version_index) - 1  # Convertir a índice (1 basado en 0)
            if version_index < 0 or version_index >= len(versions):
                return False, "Número de versión inválido."
        except ValueError:
            return False, "El índice debe ser un número válido."
        
        # Obtener el ID de la versión
        version_id = versions[version_index]["version_id"]
        version_dir = os.path.join(self.versions_dir, self.current_user, version_id)
        
        if not os.path.exists(version_dir):
            return False, f"La versión {version_id} no existe."
        
        # Listar los archivos en la carpeta de la versión
        try:
            files = [file for file in os.listdir(version_dir) if file != "metadata.json"]
            return True, files
        except Exception as e:
            return False, f"Error al listar archivos de la versión: {str(e)}"

    def access_user_files(self, target_user, dir_type="permanente"):
        # Accede a los archivos de otro usuario si se tienen permisos
        if not self.current_user:
            return False, "Debe iniciar sesión primero."
        
        if target_user not in self.users:
            return False, f"El usuario {target_user} no existe."
        
        if self.current_user not in self.users[target_user]["permissions"]:
            return False, f"No tiene permisos para acceder a los archivos de {target_user}."
        
        # Solo permitir acceso a la carpeta permanente del otro usuario
        if dir_type != "permanente":
            return False, "Solo se puede acceder a la carpeta permanente de otros usuarios."
        
        target_dir = self.users[target_user]["permanente_dir"]
        files = []
        
        try:
            for item in os.listdir(target_dir):
                item_path = os.path.join(target_dir, item)
                if os.path.isfile(item_path):
                    files.append(item)
        except Exception as e:
            return False, f"Error al listar archivos: {str(e)}"
        
        return True, files

    @staticmethod
    def input_con_asteriscos(prompt=''):
        # Muestra las contraseñas con asteriscos en la consola
        print(prompt, end='', flush=True)
        password = ''
        while True:
            char = msvcrt.getch()
            if char in {b'\r', b'\n'}:  # Enter
                print()
                break
            elif char == b'\x08':  # Backspace
                if len(password) > 0:
                    password = password[:-1]
                    print('\b \b', end='', flush=True)
            elif char == b'\x03':  # Ctrl+C
                raise KeyboardInterrupt
            else:
                password += char.decode('utf-8')
                print('*', end='', flush=True)
        return password   

class CommandLineInterface(Cmd):
    prompt = 'ControlArchivos> '
    intro = 'Sistema de Control de Archivos\n' \
            'Escriba "ayuda" para ver la lista de comandos disponibles.\n'
    
    def __init__(self, root_path):# inicializar
        super().__init__()
        self.system = FileManagementSystem(root_path)
    
    def do_registrar(self, arg):
        # Registra un nuevo usuario
        # uso: registrar <nombre_usuario>
        username = arg.strip()
        if not username:
            print("Debe proporcionar un nombre de usuario, registrar <nombre_usuario>")
            return

        password = self.system.input_con_asteriscos("Contraseña: ")

        success, message = self.system.register_user(username, password)
        print(message)
    
    def do_iniciar(self, arg):
       # Inicia sesión
       # uso: iniciar <nombre_usuario>
        username = arg.strip()
        if not username:
            print("Debe escribir un nombre de usuario, iniciar <nombre_usuario>")
            return

        password = self.system.input_con_asteriscos("Contraseña: ")
        success, message = self.system.login(username, password)
        print(message)

        if success:
            self.prompt = f'FileSystem ({username})> '

    def do_cerrar_sesion(self, arg):
        # Cierra sesion
        # uso: cerrar_sesion
        success, message = self.system.logout()
        print(message)
        
        if success:
            self.prompt = 'FileSystem> '
    
    def do_otorgar_permiso(self, arg):
        # Otorga permisos a otro usuario.
        # uso: otorgar_permiso <nombre_usuario> <tipo_permiso>
        # tipo_permiso: "lectura" o "escritura"
        args = arg.strip().split()
        if len(args) != 2:
            print("Uso: otorgar_permiso <nombre_usuario> <tipo_permiso>")
            return
        
        target_user, permission_type = args
        success, message = self.system.grant_permission(target_user, permission_type)
        print(message)
    
    def do_revocar_permiso(self, arg):
        # Revoca los permisos otorgados a un usuario
        # uso: revocar_permiso <nombre_usuario>
        target_user = arg.strip()
        if not target_user:
            print("Debe proporcionar un nombre de usuario, revocar_permiso <nombre_usuario>")
            return
        
        success, message = self.system.revoke_permission(target_user)
        print(message)
    
    def do_mis_archivos(self, arg):
        # Lista los archivos en una carpeta
        # uso: mis_archivos [tipo_directorio]
        # tipo_directorio: "temporal" (temporal, por defecto) o "permanente"
        dir_type = arg.strip() or "temporal"
        success, result = self.system.list_files(dir_type)
        
        if success:
            if not result:
                print(f"No hay archivos en la carpeta {dir_type}.")
            else:
                print(f"Archivos en la carpeta {dir_type}:")
                for file in result:
                    print(f"  - {file}")
        else:
            print(result)
    
    def do_carpetas_accesibles(self, arg):
        # Lista las carpetas a las que el usuario tiene acceso
        # uso: carpetas_accesibles
        success, result = self.system.list_accessible_folders()
        
        if success:
            if not result:
                print("No tiene acceso a carpetas de otros usuarios.")
            else:
                print("Carpetas accesibles:")
                for user, permanente in result:
                    print(f"  - {user} (permiso: {permanente})")
        else:
            print(result)
    
    def do_crear_archivo(self, arg):
        # Crea un nuevo archivo
        # Uso:
        # - crear_archivo <nombre_archivo.formato> (crea en carpeta temporal propia)
        # - crear_archivo <nombre_archivo.formato> <dueño> (crea en carpeta access/dueño)
        args = arg.strip().split()
        if not args:
            print("Uso:\n- crear_archivo <nombre_archivo.formato> (crea en carpeta temporal)\n- crear_archivo <nombre_archivo.formato> <dueño> (crea en carpeta access/dueño)")
            return

        filename = args[0]
        owner = args[1] if len(args) > 1 else None

        content = " "
        success, message = self.system.create_file(filename, content, owner)
        print(message)

    def do_modificar_archivo(self, arg):
        # Modifica la fecha de un archivo existente
        # uso: modificar_archivo <nombre_archivo> [dueño]
        # Si no se especifica dueño, se modifica en la carpeta temporal del usuario actual.
        args = arg.strip().split()
        if not args:
            print("Debe proporcionar un nombre de archivo,modificar_archivo <nombre_archivo> o modificar_archivo <nombre_archivo> [dueño]")
            return
        
        filename = args[0]
        owner = args[1] if len(args) > 1 else None
        dir_type = "access" if owner else "temporal"
        
        success, message = self.system.modify_file(filename, dir_type, owner)
        print(message)
    
    def do_eliminar_archivo(self, arg):
        # Elimina un archivo
        # uso: eliminar_archivo <nombre_archivo> [dueño]
        args = arg.strip().split()
        if not args:
            print("Debe proporcionar un nombre de archivo, eliminar_archivo <nombre_archivo> [dueño]")
            return
        
        filename = args[0]
        owner = args[1] if len(args) > 1 else None
        dir_type = "access" if owner else "temporal"
        
        success, message = self.system.delete_file(filename, dir_type, owner)
        print(message)
    
    def do_commit(self, arg):
        # Realiza un commit.
        # Uso: 
        # - commit                    # Transfiere todo de temporal a permanente
        # - commit <dueño>            # Transfiere toda la carpeta de acceso a la permanente del dueño
        args = arg.strip().split()
        
        if len(args) == 0:
            # Commit completo: temporal -> permanente
            success, message = self.system.commit()
        elif len(args) == 1:
            # Commit de toda la carpeta de acceso de un dueño
            owner = args[0]
            success, message = self.system.commit(owner=owner)
        else:
            print("Uso incorrecto. Use:\n - commit\n - commit <dueño>")
            return
        
        print(message)
    
    def do_update(self, arg):
        # Actualiza archivos:
        # - update                    -> actualiza carpeta temporal del usuario actual
        # - update <nombre_usuario>   -> actualiza access/<nombre_usuario>
        target_user = arg.strip() or None
        success, message = self.system.update(target_user)
        print(message)
    
    def do_listar_archivos_version(self, arg):
        # Lista los archivos de una versión específica
        # uso: listar_archivos_version <número_de_versión>
        version_index = arg.strip()
        if not version_index:
            print("Debe proporcionar el número de versión, listar_archivos_version <número_de_versión>")
            return
        
        success, result = self.system.listar_archivos_version(version_index)
        if success:
            if not result:
                print(f"No hay archivos en la versión {version_index}.")
            else:
                print(f"Archivos en la versión {version_index}:")
                for file in result:
                    print(f"  - {file}")
        else:
            print(result)

    def do_listar_versiones(self, arg):
        # Lista las versiones disponibles.
        # uso: listar_versiones
        success, versions = self.system.list_versions()
        
        if success:
            if not versions:
                print("No hay versiones disponibles.")
            else:
                print("Versiones disponibles:")
                for i, version in enumerate(versions):
                    timestamp = datetime.datetime.fromisoformat(version["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{i+1}. ID: {version['version_id']} - Fecha: {timestamp}")
        else:
            print(versions)
    
    def do_recuperar_version(self, arg):
        # Recupera una versión anterior
        # uso: recuperar_version carpeta | archivo
        recover_type = arg.strip().lower()
        if recover_type not in ["carpeta", "archivo"]:
            print("Uso incorrecto. Use:\n - recuperar_version carpeta\n - recuperar_version archivo")
            return

        success, message = self.system.recover_version(recover_type)
        print(message)
    
    def do_archivos_accesibles(self, arg):
        # Accede a los archivos de otro usuario
        # uso: archivos_accesibles <nombre_usuario>
        target_user = arg.strip()
        if not target_user:
            print("Debe proporcionar un nombre de usuario, archivos_accesibles <nombre_usuario>")
            return
        
        success, result = self.system.access_user_files(target_user)
        
        if success:
            if not result:
                print(f"No hay archivos en la carpeta permanente de {target_user}.")
            else:
                print(f"Archivos de {target_user}:")
                for file in result:
                    print(f"  - {file}")
        else:
            print(result)

    def do_cls(self, arg):
        # Limpia la consola.
        # uso: cls
        os.system('cls' if os.name == 'nt' else 'clear')

    def do_ayuda(self, arg):
        # Muestra la ayuda para los comandos
        if arg:
            print("\nNo se aceptan argumentos para el comando ayuda.")
        else:
            # Mostrar lista de comandos agrupados
            print("\nComandos disponibles:")
            
            print("\nGestión de usuarios:")
            print("  registrar           - Registra un nuevo usuario ()(registrar <nombre_usuario>)")
            print("  iniciar             - Inicia sesión (iniciar <nombre_usuario>)")
            print("  cerrar_sesion        - Cierra la sesión actual (cerrar_sesion)")
            print("  otorgar_permiso     - Otorga permisos a otro usuario (otorgar_permiso <nombre_usuario> <tipo_permiso>)")
            print("  revocar_permiso     - Revoca permisos a otro usuario (revocar_permiso <nombre_usuario>)")
            
            print("\nGestión de archivos:")
            print("  crear_archivo       - Crea un nuevo archivo (crear_archivo <nombre_archivo> [dueño] o crear_archivo <nombre_archivo>)")
            print("  modificar_archivo   - Modifica un archivo (modificar_archivo <nombre_archivo> [dueño] o modificar_archivo <nombre_archivo>)")
            print("  eliminar_archivo    - Elimina un archivo (eliminar_archivo <nombre_archivo> [dueño] o eliminar_archivo <nombre_archivo>)")
            
            print("\nControl de versiones:")
            print("  commit              - Transfiere de temporal a permanente y crea versión (commit o commit <dueño>)")
            print("  update              - Actualiza temporal con contenido de permanente (update o update <dueño>)")
            print("  listar_versiones    - Lista versiones disponibles")
            print("  listar_archivos_version    - Lista los archivos de una version")
            print("  recuperar_version   - Recupera una versión anterior de archivo o carpeta (recuperar_version <carpeta|archivo>)")
            
            print("\nListado de archivos y carpetas:")
            print("  mis_archivos     - Lista archivos en carpeta temporal o permanente (mis_archivos [tipo])")
            print("  carpetas_accesibles   - Lista carpetas a las que tiene acceso (carpetas_accesibles <nombre_usuario>)")
            print("  archivos_accesibles    - Accede a archivos de otro usuario (archivos_accesibles <nombre_usuario>)")
            
            print("\nOtros comandos:")
            print("  ayuda               - Muestra esta ayuda")
            print("  salir               - Sale del programa")
            print("  cls                 - Limpia la consola")   
    
    def do_salir(self, arg):
        # Sale del programa.
        # uso: salir
        print("¡Hasta luego!")
        return True

def main():
    # Función principal
    print("Sistema de Control de Archivos")
    print("=" * 50)
    
    # Ubicación del raiz raíz
    while True:
        root_path = os.path.join(os.getcwd(), "raiz")      
        if not os.path.exists(root_path):
            try:
                os.makedirs(root_path)
                break
            except Exception as e:
                print(f"Error al crear el directorio: {str(e)}")
                continue
        else:
            break
    
    print(f"Usando repositorio en: {root_path}")
    
    # Iniciar la interfaz de línea de comandos
    cli = CommandLineInterface(root_path)
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\n¡Hasta luego!")
    except Exception as e:
        print(f"Error inesperado: {str(e)}")

if __name__ == "__main__":
    main()