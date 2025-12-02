from src.monitor.metrics import Sampler

def test_snapshot_has_basic_fields():
    s = Sampler().snapshot()
    assert "cpu_total" in s
    assert "mem" in s
    assert "top_procs" in s
