# This program is designed to measure the time difference between sending a bunch of queries to load a buffer up with data
# and then grab all of it versus doing single individual queries. It appears there is no difference in time.
# If this is true, it is preferable to do individual queries since there is no risk of overflowing buffers or dropping packets.

import threading
import sim900_communicator
import time

lock=threading.Lock()
comm=sim900_communicator.CleanComm(lock)


'''tic=time.time()
print comm.query_port(5,'TVAL? 0')
print comm.query_port(5,'VOLT? 0')
toc=time.time()
print toc-tic
print

tic=time.time()
comm.send('SNDT 5, "TVAL? 0"')
comm.send('SNDT 5, "VOLT? 0"')
print comm.custom_query(2,5)
toc=time.time()
print toc-tic'''

tic=time.time()
print comm.query_port(1,'TVAL?')
print comm.query_port(1,'TDEV?')
print comm.query_port(1,'RVAL?')
print comm.query_port(1,'RDEV?')
print comm.query_port(1,'PHAS?')
print comm.query_port(1,'FREQ?')
toc=time.time()
print toc-tic
print

tic=time.time()
comm.send('SNDT 1,"TVAL?"')
comm.send('SNDT 1,"TDEV?"')
comm.send('SNDT 1,"RVAL?"')
comm.send('SNDT 1,"RDEV?"')
comm.send('SNDT 1,"PHAS?"')
comm.send('SNDT 1,"FREQ?"')
print comm.custom_query(6,1)
toc=time.time()
print toc-tic





print
time.sleep(0.5)
print 'emptying buffers'
print comm.query_loop(5)
print comm.query_loop(5)
print comm.query_loop(5)
print comm.query_loop(5)


