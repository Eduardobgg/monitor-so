# monitor-so

**Equipo 6**

- Eduardo Biali García Gómez  
- Mendiola Montes Victor Manuel  
- Flores Muñoz Mauricio  
- Hurtado Aponte Joshua Abel  

## Descripción
Desarrollaremos un **monitor del sistema**, la idea es mostrar, información del SO: uso de **CPU**, **memoria** y **procesos**.

## Lenguaje y librerías
- **Python**
- **psutil**: leer métricas del sistema (CPU, memoria, procesos) 
- **rich** o **textual**: interfaz en la terminal y con actualización en vivo.
- **pytest**, **ruff** o **flake8**: pruebas y estilo para mantener el código ordenado

## Instalación
- python3 -m venv .venv
- source .venv/bin/activate
- pip install -r requirements.txt

## Ejecución
- python -m src.monitor.cli
