
import logging
from snapconnect import snap
import time

def remoteCall(dim):
    print('Dim level is ',dim)

comm = snap.Snap(funcs={'remoteCall': remoteCall})
comm.open_serial(1,'/dev/snap0')
comm.rpc("\x08\x16\x0B","get_dim_level")
print('Looping')
timeout = time.time() + 1
while time.time() < timeout:
    comm.poll()
    
print('looping')