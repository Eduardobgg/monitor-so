from __future__ import annotations
import time
import psutil
import os
import signal
from rich.live import Live
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, IntPrompt
from rich import box
from .metrics import Sampler

# Objeto principal para imprimir en pantalla
consola = Console()

# --- Función para convertir números grandes a más legibles --- 
def bytesLegibles (n : float) -> str:
    step = 1024.0
    for u in ["B", "KB", "MB", "GB", "TB"]:
        if abs(n) < step:
            return f"{n:,.1f} {u}"
        n /= step
    return f"{n:,.1f} PB"


# --- Cabecera ---
def cabecera(snap) -> Panel:
    # Desempaquetamos los datos de metrics.py
    cpu = snap["cpu"]
    mem = snap["memoria"]
    swap = snap["swap"]
    disco = snap["discos"]
    red = snap["red"]
    procesos = snap["procesoStats"]

    # Si el Swap esta en niveles normales, se muestra en verde. 
    # Si se usa mucho, alertamos con amarillo/rojo porque la paginación excesiva es mala.
    colorSwap = "green" if swap["percent"] < 5 else "yellow" if swap["percent"] < 50 else "red"
    # Si no hay procesos zombies, se imprime en verde.
    # Si los hay, se imprime en rojo porque esto un error de programación en el sistema.
    colorZombie = "green" if procesos["zombie"] == 0 else "bold red"
    
    load = cpu["loadAvg"] 

    # Filas de la cabecera.
    
    # Fila 1. CPU total, Load avg y switches.
    f1 = f"[bold cyan]CPU Total:[/bold cyan] {cpu['total']:5.1f}% | " \
         f"[bold]Load Avg:[/bold] {load[0]:.2f}, {load[1]:.2f}, {load[2]:.2f} | " \
         f"[bold]Ctx Switches:[/bold] {cpu['switches']:,.0f}/s"

    # Fila 2. Memoria, cantidad usada y swap.
    f2 = f"[bold cyan]Memoria:[/bold cyan]   {mem['percent']:5.1f}% | " \
         f"Usada: {bytesLegibles(mem['used'])} | " \
         f"[{colorSwap}]Swap: {swap['percent']}% ({bytesLegibles(swap['used'])})[/{colorSwap}]"

    # Fila 3. Discos.
    f3 = f"[bold cyan]Disco I/O:[/bold cyan] R: {bytesLegibles(disco['lectura'])}/s W: {bytesLegibles(disco['escritura'])}/s"
    
    # Fila 4. Red.
    f4 = f"[bold cyan]Red:[/bold cyan]       ↑ {bytesLegibles(red['envio'])}/s ↓ {bytesLegibles(red['recibo'])}/s"
    
    # Fila 5. Procesos.
    f5 = f"[bold cyan]Procesos:[/bold cyan]  Run: {procesos['running']} | Sleep: {procesos['sleeping']} | " \
         f"[{colorZombie}]Zombies: {procesos['zombie']}[/{colorZombie}]"
    
    # Fila 6. Instrucciones para el menú. 
    f6 = "\n[bold white on blue] CTRL + C para ver menú de acciones[/bold white on blue]"

    grid_text = Text.from_markup(f"{f1}\n{f2}\n{f3}\n{f4}\n{f5}\n{f6}")
    return Panel(grid_text, title="[bold]Monitor de Sistema[/bold]", border_style="blue", expand=True)



# --- Función que construye la tabla de procesos ---
def tablaProcesos(snap) -> Table:
    table = Table(expand = True, box = box.SIMPLE_HEAD, show_lines = False)
    # Definición de columnas.
    table.add_column("PID", justify="right", style="cyan", no_wrap=True, width=6)
    table.add_column("Nombre", style="white", no_wrap=True)
    table.add_column("Estado", justify="center", width=10)
    table.add_column("%CPU", justify="right", width=6)
    table.add_column("%MEM", justify="right", width=6)

    # Llenamos filas con los datos del Top 20
    for p in snap["topProcesos"]:
        status = p.get("status", "?")
        # Coloreamos el texto según el estado. Running -> Verde |||  Zombie -> Rojo.
        st_style = "green" if status == "running" else "red" if status == "zombie" else "dim"
        
        table.add_row(
            str(p["pid"]),
            str(p["name"]),
            f"[{st_style}]{status}[/{st_style}]",
            f"{p.get('cpu_percent', 0.0):.1f}",
            f"{p.get('memory_percent', 0.0):.1f}"
        )
    return table



# ---  Función que pausa el monitor y abre un menu para gestionar procesos ---
def menu():

    consola.clear()
    consola.print(Panel("[bold yellow] *** Control de Procesos *** [/bold yellow]", border_style = "yellow"))
    
    while True:
        consola.print("\n[bold cyan]Seleccionar una acción:[/bold cyan]")
        consola.print("[1] [bold red]Matar un proceso[/bold red]")
        consola.print("[2] [bold yellow]Suspender un proceso[/bold yellow]")
        consola.print("[3] [bold green]Reanudar proceso[/bold green]")
        consola.print("[4] Volver al Monitor")
        consola.print("[5] Salir del programa")
        
        #Input del usuario.
        eleccion = Prompt.ask("Opción", choices = ["1", "2", "3", "4", "5"], default = "4")

        # Continuar ejecutando monitor.
        if eleccion == "4":
            return True
        # Apagar todo.
        elif eleccion == "5":
            return False

        # Lógica de selección
        try:
            pid = IntPrompt.ask("Introduce el [cyan]PID[/cyan] del proceso")
            # Objeto proceso.
            proc = psutil.Process(pid)
            
            # Eliminar proceso.
            if eleccion == "1":
                proc.kill()
                consola.print(f"[bold red] Proceso {pid} ({proc.name()}) eliminado.[/bold red]")
            
            # Pausa proceso.
            elif eleccion == "2":
                proc.suspend()
                consola.print(f"[bold yellow]Proceso {pid} ({proc.name()}) suspendido.[/bold yellow]")
            
            # Regresamos a la vida un proceso.
            elif choice == "3":
                proc.resume()
                consola.print(f"[bold green]Proceso {pid} ({proc.name()}) reanudado.[/bold green]")
        
            time.sleep(1.5)
            
        # Manejo de errores.
        except psutil.NoSuchProcess:
            consola.print(f"[bold yellow]El proceso con PID {pid} ya no existe.[/bold yellow]")
        except psutil.AccessDenied:
            consola.print(f"[bold red]Acceso denegado. Necesitas permisos de administrador.[/bold red]")
        except Exception as e:
            consola.print(f"[red]Error:[/red] {e}")
      
      
      
      
def main():

    # Instanciamos nuestro recolector de métricas.
    sampler = Sampler()

    print("Inicializando sensores...")
    
    # Primera lectura. 
    psutil.cpu_percent(None)
    time.sleep(1)

    corriendo = True

    while corriendo:
        try:
            # Layout principal.
            layout = Table.grid(expand = True)
            layout.add_column()
            
            with Live(layout, console = consola, refresh_per_second = 2) as live:
                while True:
                    # Obtenemos datos e imprimimos los datos.
                    snap = sampler.snapshot()
                    header = cabecera(snap)
                    proc_tbl = tablaProcesos(snap)
                    # Ensamblar y mostrar.
                    layout = Table.grid(expand = True)
                    layout.add_row(header)
                    layout.add_row(proc_tbl)
                    live.update(layout)
                    # Frecuencia con la que se actualiza.
                    time.sleep(0.5)

        except KeyboardInterrupt:
            # Aquí capturamos el Ctrl + c y enseñamos el menu.
            continuar = menu()
            if not continuar:
                print("Cerrando monitor...")
                break
            else:
                print("Reiniciando monitor...")

if __name__ == "__main__":
    main()
