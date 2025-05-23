# Características

- **Gestión de usuarios**: Registro, login y logout
- **Control de permisos**: Otorgar y revocar permisos de lectura/escritura entre usuarios
- **Carpetas diferenciadas**: Sistema de carpetas temporales y permanentes
- **Control de versiones**: Historial completo de cambios con recuperación de versiones anteriores
- **Colaboración**: Trabajo compartido en archivos con otros usuarios

# Requisitos del Sistema

- Python 3.6 o superior
- Sistema operativo Windows (para funcionalidad de contraseñas con asteriscos)
- Librerías estándar de Python: `os`, `shutil`, `json`, `datetime`, `msvcrt`, `uuid`, `cmd`

# Instalación

1. Descargar el archivo `tarea.py`
2. Tener Python instalado en el sistema
3. Ejecutar el programa desde la terminal:

## Estructura del Sistema

El sistema crea automáticamente la siguiente estructura de carpetas:

raiz/
├── .usuarios.json          # Información de usuarios y permisos
├── .versiones/            # Historial de versiones
│   └── [usuario]/
│       └── [version_id]/
└── [usuario]/
    ├── temporal/          # Archivos de trabajo temporal
    ├── permanente/        # Archivos confirmados
    └── access/           # Acceso a archivos de otros usuarios
        └── [otro_usuario]/

## Guía de Uso

### 1. Gestión de Usuarios

#### Registrar un nuevo usuario

ControlArchivos> registrar juan
Contraseña: ********
Usuario juan registrado correctamente.

#### Iniciar sesión

ControlArchivos> iniciar juan
Contraseña: ********
Sesión iniciada como juan.
ControlArchivos (juan)>

#### Cerrar sesión

ControlArchivos (juan)> cerrar_sesion
Sesión cerrada correctamente.
ControlArchivos>

### 2. Gestión de Archivos

#### Crear archivos

# Crear archivo en la carpeta temporal
ControlArchivos (juan)> crear_archivo documento.txt

# Crear archivo en la carpeta de acceso de otro usuario (necesita permisos de escritura),maria seria otro usuario
ControlArchivos (juan)> crear_archivo reporte.txt maria

#### Modificar archivos

# Modificar archivo propio
ControlArchivos (juan)> modificar_archivo documento.txt

# Modificar archivo de otro usuario (debe tener permisos de escritura)
ControlArchivos (juan)> modificar_archivo reporte.txt maria

#### Eliminar archivos

# Eliminar archivo propio
ControlArchivos (juan)> eliminar_archivo documento.txt

# Eliminar archivo de otro usuario (debe tener permiso de escritura)
ControlArchivos (juan)> eliminar_archivo reporte.txt maria

### 3. Sistema de Permisos

#### Otorgar permisos

# Otorgar permiso de lectura
ControlArchivos (juan)> otorgar_permiso maria lectura

# Otorgar permiso de escritura
ControlArchivos (juan)> otorgar_permiso pedro escritura

#### Revocar permisos

ControlArchivos (juan)> revocar_permiso maria

### 4. Control de Versiones

#### Commit (guardar lo de la carpeta temporal a la permanente)

# Transferir archivos temporales a permanente
ControlArchivos (juan)> commit

# Transferir archivos de access a permanente de otro usuario (debe tener permiso de escritura)
ControlArchivos (juan)> commit maria

#### Update (Actualizar archivos)

# Actualizar la carpeta temporal propia con los archivos de la permanente
ControlArchivos (juan)> update

# Actualizar access con archivos de la permanente de otro usuario (debe tener permiso de lectura o escritura)
ControlArchivos (juan)> update maria

#### Gestión de versiones

# Listar todas las versiones disponibles
ControlArchivos (juan)> listar_versiones

# Ver archivos de una versión específica
ControlArchivos (juan)> listar_archivos_version 1

# Recuperar versión anterior (carpeta completa)
ControlArchivos (juan)> recuperar_version carpeta

# Recuperar archivo específico de una versión
ControlArchivos (juan)> recuperar_version archivo

### 5. Listado y Consulta

#### Ver los propios archivos

# Ver archivos temporales
ControlArchivos (juan)> mis_archivos temporal

# Ver archivos permanentes
ControlArchivos (juan)> mis_archivos permanente

#### Ver archivos de otros usuarios (debe tener permisos de escritura o lectura)

ControlArchivos (juan)> archivos_accesibles maria

#### Ver carpetas accesibles (debe tener permisos de escritura o lectura)

ControlArchivos (juan)> carpetas_accesibles
Carpetas accesibles:
  - maria (permiso: lectura)
  - pedro (permiso: escritura)

### 6. Comandos de Utilidad

#### Limpiar consola

ControlArchivos (juan)> cls

#### Ver ayuda

ControlArchivos (juan)> ayuda

#### Salir del programa

ControlArchivos (juan)> salir