import psutil
def get_cpu_usage():
    """Get current CPU usage in percentage"""
    return psutil.cpu_percent(interval=1)


def get_memory_usage():
    """Get current memory usage in MB"""
    return psutil.virtual_memory().used / 1024 / 1024