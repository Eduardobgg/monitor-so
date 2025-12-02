from __future__ import annotations
# Para acceder al kernel.
import psutil
# Para marcas de tiempo.
import time
# Tipado estático.
from typing import Dict, Any, Optional, Tuple

# --- Función para calcular la tasa de cambio. Esto para saber la velocidad actual ---

# Recibimos el estado anterior de la memoria, que podría ser una tupla con el tiempo exacto de la
# lectura anterior y el valor del contador anterior, y el valor actual leído. Lo que regresamos
# es la tasa calculada y el nuevo estado a guardas.
def tasa (previo : Optional[Tupla[float, int]], actual : int) -> Tupla[float, Tupla[float, int]]:

    # Hora actual exacta.
    presente = time.time()
    
    # Si es la primera vez que medimos, no tenemos con que comparar,
    # entonces devolvemos 0.
    if previo is None:
        return (0.0, (presente, actual))
    
    # Estado anterior.
    tiempoPrevio, valorPrevio = previo
    
    # Calculamos el tiempo transcurrido. Vamos a usar max() para evitar división por cero.
    tiempoTrans = max(presente - tiempoPrevio, 1e-6)
    
    # Si el sistema se reinició, el contador actual será menor al previo, entonces en ese
    # caso reiniciamos el cálculo para no dar números negativos.
    if actual < valorPrevio:
        return (0.0, (presente, actual))

    # Calculo final de la tasa.
    tasaF = (actual - valorPrevio) / tiempoTrans
    
    # Regresamos la tasa  Y el nuevo estado para la próxima vuelta
    return (tasaF, (presente, actual))



# Clase que mantiene la memoria entre mediciones.
class Sampler:

    def __init__(self) -> None:
        # Inicializamos todas las variables de estado en None.
        # Esto porque cuando arrancamos el programa la memoria está vacía.
        
        # Estado previo para discos.
        self.lecturaDisco_previa : Optional[Tuple[float, int]] = None
        self.escrituraDisco_previa : Optional[Tuple[float, int]] = None
        
        # Estado previo para red.
        self.envioRed_previo : Optional[Tuple[float, int]] = None
        self.recibirRed_previo : Optional[Tuple[float, int]] = None

        # Estado previo para CPU.
        self.switches_previo : Optional[Tuple[float, int]] = None
        self.interrupts_previo : Optional[Tuple[float, int]] = None



    # --- Función para capturar los datos de todo el sistema operativo en este momento ---
    def snapshot(self) -> Dict[str, Any]:
    
        # ~~ CPU ~~
        # Uso de la CPU en porcentaje.
        cpuTotal = psutil.cpu_percent(interval = None)
        cpuPercpu = psutil.cpu_percent(interval = None, percpu = True)
        # Carga promedio del sistema en los últimos 1, 5 y 15 minutos como una tupla.
        loadAvg = psutil.getloadavg()
        # Switches & Interrupts.
        cpuStats = psutil.cpu_stats()
        # Calculamos cuantos cambios de contexto e interrupciones hubo en el ultimo segundo.
        tasaSwitches, self.switches_previo = tasa(self.switches_previo, cpuStats.ctx_switches)
        tasaInterrupts, self.interrupts_previo = tasa(self.interrupts_previo, cpuStats.interrupts)


        # ~~ Memoria ~~
        # Memoria RAM.
        memRAM = psutil.virtual_memory()
        # Memoria de intercambio.
        swap = psutil.swap_memory()


        # ~~ Procesos ~~
        procesos = []
        # Diccionario para contar cuantos procesos hay en cada estado.
        status = {
            "running": 0, 
            "sleeping": 0, 
            "stopped": 0, 
            "zombie": 0, 
            "disk-sleep": 0
        }

        # Iteramos sobre todos los procesos activos.
        for p in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']):
            try:
                # Contamos el estado para el resumen.
                st = p.info['status']
                if st in status:
                    status[st] += 1
                
                # Guardar info para la tabla.
                procesos.append(p.info)
                
            # Si un proceso muere mientras lo leemos, capturamos la excepción.
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Ordenamos la lista por uso de CPU y nos quedamos con los Top 20.
        procesos.sort(key = lambda x: x.get("cpu_percent", 0.0), reverse = True)
        top_procesos = procesos[:20]


        # ~~ Discos ~~
        # Datos estadísticos de entrada y salida.
        discosIO = psutil.disk_io_counters()
        # Nota: dio puede ser None en algunos sistemas sin discos físicos accesibles
        if discosIO:
            # Convertimos contadores totales a Bytes por segundo.
            lectura, self.lecturaDisco_previa  = tasa(self.lecturaDisco_previa , discosIO.read_bytes)
            escritura, self.escrituraDisco_previa = tasa(self.escrituraDisco_previa , discosIO.write_bytes)
        else:
            lectura, escritura = 0.0, 0.0

        # ~~ Red ~~
        # Datos estadísticos de entrada y salida.
        redIO = psutil.net_io_counters()
        # Convertimos contadores totales a Bytes por segundo.
        envio, self.envioRed_previo = tasa(self.envioRed_previo , redIO.bytes_sent)
        recibo, self.recibirRed_previo = tasa(self.recibirRed_previo , redIO.bytes_recv)
        
        # Por ulitmo, empaquetamos todo para que lo use cli.py
        return {
            "cpu": {
                "total": cpuTotal,
                "cpuPercpu": cpuPercpu,
                "loadAvg": loadAvg,
                "switches": tasaSwitches,
                "interrupts": tasaInterrupts
            },
            "memoria": {
                "total": memRAM.total,
                "available": memRAM.available,
                "used": memRAM.used,
                "percent": memRAM.percent
            },
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "percent": swap.percent
            },
            "discos": {
                "lectura": lectura,
                "escritura": escritura
            },
            "red": {
                "envio": envio,
                "recibo": recibo
            },
            "procesoStats": status,
            "topProcesos": top_procesos
        }
