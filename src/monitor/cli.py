from __future__ import annotations
import time
import psutil
from rich.live import Live
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from .metrics import Sampler

console = Console()

def _format_bytes(n: float) -> str:
    # Formato legible para discos/red
    step = 1024.0
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(n) < step:
            return f"{n:,.1f} {unit}"
        n /= step
    return f"{n:,.1f} PB"

def _header(snapshot) -> Panel:
    cpu = snapshot["cpu_total"]
    mem = snapshot["mem"]
    disk = snapshot["disk_rates"]
    net = snapshot["net_rates"]

    lines = [
        f"[bold]CPU total:[/bold] {cpu:.1f} %",
        f"[bold]Memoria:[/bold] {mem['percent']:.1f}%  (Usada: {_format_bytes(mem['used'])} / Total: {_format_bytes(mem['total'])})",
        f"[bold]Disco:[/bold] Lectura { _format_bytes(disk['read_Bps']) }/s · Escritura { _format_bytes(disk['write_Bps']) }/s",
        f"[bold]Red:[/bold] Subida { _format_bytes(net['up_Bps']) }/s · Bajada { _format_bytes(net['down_Bps']) }/s",
    ]
    return Panel(Text.from_markup("\n".join(lines)), title="Monitor de Sistema", expand=True)


def _proc_table(snapshot) -> Table:
    n = psutil.cpu_count(logical=True) or 1
    table = Table(title="Procesos (Top por %CPU)", expand=True)
    table.add_column("PID", justify="right", no_wrap=True)
    table.add_column("Nombre", overflow="fold")
    table.add_column("%CPU", justify="right")
    table.add_column("%MEM", justify="right")

    for p in snapshot["top_procs"]:
        raw = p.get("cpu_percent", 0.0)  
        cpu_norm = raw / n               
        table.add_row(str(p["pid"]), str(p["name"]),
                      f"{cpu_norm:.1f}", f'{p.get("memory_percent",0.0):.1f}')
    return table

def main():
    sampler = Sampler()

    for proc in psutil.process_iter():
        try:
            proc.cpu_percent(None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    time.sleep(0.4)

    try:
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                snap = sampler.snapshot()
                layout = Table.grid(padding=(0, 1))
                layout.add_row(_header(snap))
                layout.add_row(_proc_table(snap))
                live.update(layout)
                time.sleep(1)
    except KeyboardInterrupt:

        console.print("\nSaliendo…")
        return

if __name__ == "__main__":
    main()
