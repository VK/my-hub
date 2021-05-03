from psutil import virtual_memory
import os

mem = virtual_memory()

c.ResourceUseDisplay.mem_limit = mem.total
c.ResourceUseDisplay.track_cpu_percent = True
c.ResourceUseDisplay.cpu_limit = os.cpu_count()

