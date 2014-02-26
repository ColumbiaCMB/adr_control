# This test involves testing the conn method against the old query_port method. Conn seems to take more time on the first query, but much less on subsequent queries.

import threading
import experimental_sim900_communicator
import time

lock=threading.Lock()
comm=experimental_sim900_communicator.CleanComm(lock)

command_list=['TVAL?','TDEV?','RVAL?','RDEV?','PHAS?','FREQ?','RANG?','EXCI?','EXON?','MODE?','IEXC?','VEXC?','ATEM?','RSET?','TSET?','VOHM?','VKEL?','AMAN?','AOUT?']

start=time.time()
for i in command_list:
    tic=time.time()
    print comm.query_port(1,i)
    toc=time.time()
    print '%s took %f seconds'%(i,(toc-tic))
end=time.time()
print 'All query_port processes took %f seconds' %(end-start)

start=time.time()
comm.send('CONN 1, "xyx"')
for i in command_list:
    tic=time.time()
    print comm.fast_send_and_receive(i)
    toc=time.time()
    print '%s took %f seconds'%(i,(toc-tic))
comm.send('xyx')
end=time.time()
print 'All fast_send_and_receive processes took %f seconds' %(end-start)
