# app/infra/profiling.py
import time, json, functools

class StepTimer:
    def __init__(self): 
        self.t0 = time.perf_counter(); self.marks = []
    def mark(self, name): 
        now = time.perf_counter(); 
        self.marks.append((name, now - self.t0)); 
        self.t0 = now
    def to_dict(self): 
        return [{"name": n, "duration_ms": round(dt*1000, 2)} for n, dt in self.marks]

def profiled(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        timer = StepTimer()
        kwargs["_timer"] = timer
        try:
            result = fn(*args, **kwargs)
            return result
        finally:
            try:
                print(json.dumps({"profile": timer.to_dict()}, ensure_ascii=False))
            except Exception:
                pass
    return wrapper
