# monitor-so

**Equipo 6**

- Eduardo Biali García Gómez  
- Mendiola Montes Victor Manuel  
- Flores Muñoz Mauricio  
- Hurtado Aponte Joshua Abel  

## Descripción
`monitor-so` es un **monitor del sistema** en terminal hecho en Python. Muestra métricas del sistema operativo en tiempo real como:

- **CPU**: uso total, por núcleo, *load average* (1/5/15 min), cambios de contexto/s e interrupciones/s
- **Memoria**: total/used/available y porcentaje
- **Swap**: total/used y porcentaje
- **Disco**: lectura/s y escritura/s
- **Red**: subida/s y bajada/s
- **Procesos**: top procesos por %CPU (PID, nombre, estado, %CPU, %MEM) y conteo de procesos por estado

La interfaz está hecha con **Rich** para actualizarse en vivo y ser legible.

## Lenguaje y librerías
- **Python**
- **psutil**: leer métricas del sistema (CPU, memoria, procesos) 
- **rich** o **textual**: interfaz en la terminal y con actualización en vivo.
- **pytest**, **ruff** o **flake8**: pruebas y estilo para mantener el código ordenado

## Instalar dependencias
### 1) Crear y activar un entorno virtual (recomendado)

**Linux/macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Instalar dependencias
```bash
pip install -r requirements.txt
```

## Ejecutar el programa

Como el paquete `monitor` está dentro de `src/`, hay que agregar `src` al ejecutar.

### Linux/macOS
```bash
python -m src.monitor.cli
```

### Windows (PowerShell)
```powershell
$ python -m src.monitor.cli
```
## Cómo usar el monitor
Al iniciar, verás una cabecera con métricas (CPU/memoria/swap/disco/red) y debajo una tabla con procesos. La pantalla se actualiza aproximadamente cada **0.5 s**.

Notas importantes:
- Los valores de disco/red se muestran como **tasas por segundo** (B/s, KB/s, etc.).
- El **%CPU por proceso** puede ser mayor a 100% en equipos multicore (porque un proceso puede usar varios núcleos).
- Puede aparecer `AccessDenied` al leer algunos procesos si no hay permisos; el monitor continúa funcionando.

## Menú de control de procesos (Ctrl + C)
Cuando presionas **Ctrl + C**, el programa **no se cierra inmediatamente**: entra al **Modo Intervención del Sistema** y muestra un menú.

Opciones del menú:
1. **MATAR Proceso (SIGKILL)**: termina el proceso inmediatamente.
2. **SUSPENDER Proceso (SIGSTOP)**: congela el proceso (deja de ejecutarse).
3. **REANUDAR Proceso (SIGCONT)**: continúa un proceso suspendido.
4. **Volver al Monitor**: regresa a la vista principal.
5. **Salir del programa**: cierra el monitor.

Flujo de uso:
1) Presiona **Ctrl + C**  
2) Elige una opción (1–5)  
3) Si elegiste 1–3, escribe el **PID** del proceso cuando te lo pida  
4) El programa mostrará un mensaje de éxito/error y podrás volver al monitor o salir

## Recomendaciones
- Ten cuidado con **SIGKILL**: es irreversible y puede cerrar programas importantes.
- Si te aparece “Acceso denegado”, ejecuta con permisos de administrador (según tu SO) o elige otro PID.

## Estructura del proyecto (resumen)
- `src/monitor/metrics.py`: muestreo y construcción del snapshot (métricas del sistema)
- `src/monitor/cli.py`: interfaz en terminal con Rich + menú de Ctrl+C
- `requirements.txt`: dependencias
