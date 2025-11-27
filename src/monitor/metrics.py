from __future__ import annotations
import psutil
import time
from typing import Dict, Any, Optional, Tuple

def _rate(prev: Optional[Tuple[float, int]], current_value: int) -> Tuple[float, Tuple[float, int]]:
    """
    Calcula tasa por segundo dado un contador acumulado.
    prev: (timestamp_prev, value_prev) o None
    Devuelve (rate_per_sec, (timestamp_now, current_value))
    """
    now = time.time()
    if prev is None:
        return (0.0, (now, current_value))
    t_prev, v_prev = prev
    dt = max(now - t_prev, 1e-6)
    rate = (current_value - v_prev) / dt
    return (max(rate, 0.0), (now, current_value))

class Sampler:
    """
    Guarda estado mínimo para calcular tasas de disco/red.
    """
    def __init__(self) -> None:
        self._disk_read_prev: Optional[Tuple[float, int]] = None
        self._disk_write_prev: Optional[Tuple[float, int]] = None
        self._net_sent_prev: Optional[Tuple[float, int]] = None
        self._net_recv_prev: Optional[Tuple[float, int]] = None

    def snapshot(self) -> Dict[str, Any]:
        # CPU % total y por CPU (interval=None para no bloquear)
        cpu_total = psutil.cpu_percent(interval=None)
        cpu_percpu = psutil.cpu_percent(interval=None, percpu=True)

        # Memoria
        mem = psutil.virtual_memory()._asdict()

        # Procesos: top por CPU
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        procs.sort(key=lambda x: x.get("cpu_percent", 0.0), reverse=True)
        top_procs = procs[:20]

        # Disco (contadores acumulados) -> tasas
        dio = psutil.disk_io_counters()
        rps, self._disk_read_prev  = _rate(self._disk_read_prev,  int(dio.read_bytes))
        wps, self._disk_write_prev = _rate(self._disk_write_prev, int(dio.write_bytes))

        # Red (contadores acumulados) -> tasas
        nio = psutil.net_io_counters()
        ups, self._net_sent_prev   = _rate(self._net_sent_prev,  int(nio.bytes_sent))
        dps, self._net_recv_prev   = _rate(self._net_recv_prev, int(nio.bytes_recv))

        return {
            "cpu_total": cpu_total,
            "cpu_percpu": cpu_percpu,
            "mem": {
                "total": mem.get("total", 0),
                "available": mem.get("available", 0),
                "used": mem.get("used", 0),
                "percent": mem.get("percent", 0.0),
            },
            "top_procs": top_procs,
            "disk_rates": {
                "read_Bps": rps,
                "write_Bps": wps,
            },
            "net_rates": {
                "up_Bps": ups,
                "down_Bps": dps,
            },
        }

