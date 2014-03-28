import adr_controller
import Pyro4
import time

sim900=Pyro4.Proxy("PYRONAME:sim900server")
controller=adr_controller.AdrController(client=sim900,gui_input=False,gui_message_display=None,loop=False)

ramp_goal=0.8
ramp_rate=0.005
timelist=[]

def reset_pid():
    # Note that ramp MUST be set to false before setpoint is changed.
    controller.request_manual_output_on()
    set_and_verify_ramp(0)
    set_and_verify_setpoint(0)
    sim900.send(3,'MOUT 0')
    
    
def set_and_verify_setpoint(setpoint):
    sim900.set_pid_setpoint(setpoint)
    result=sim900.query_pid_setpoint()
    if result!=setpoint:
        print 'Result of setpoint query was %f'%(result)
        set_and_verify_setpoint(setpoint)
    
def set_and_verify_ramp(ramp_on):
    sim900.set_ramp_on(ramp_on)
    result=sim900.query_pid_ramp_on()
    if not isinstance(result,float):
        set_and_verify_ramp(ramp_on)
    if result!=ramp_on:
        set_and_verify_ramp(ramp_on)
        
def query():
    print 'Setpoint is %f'%(sim900.query_pid_setpoint())
    print 'PID ramp is %f'%(sim900.query_pid_ramp_on())
    print 'PID Control is %s'%(str(sim900.query_port(3,'AMAN?')))
    print 'PID manual output is %f'%(sim900.query_manual_output())
    
def loop():
    reset_pid()
    toc=time.time()
    controller.old_ramp(ramp_goal,ramp_rate)
    tic=time.time()
    timelist.append(tic-toc)

def test_up():
    i=0
    errors=0
    while i<500:
        loop()
        result=sim900.query_pid_setpoint()
        if result!=ramp_goal:
            print result
            print ramp_goal
            errors+=1
        i+=1

    print 'The number of errors found was %d'%(errors)
    print timelist
    
def test_up_and_down():
    i=0
    errors_up=0
    errors_down=0
    reset_pid()
    while i<500:
        controller.ramp(ramp_goal,ramp_rate)
        result=sim900.query_pid_setpoint()
        if result!=ramp_goal:
            print result
            print ramp_goal
            errors_up+=1
        controller.ramp(0,ramp_rate)
        result=sim900.query_pid_setpoint()
        if result!=0:
            print result
            print ramp_goal
            errors_down+=1
        reset_pid()
        i+=1
        
    print 'Errors up: %d'%(errors_up)
    print 'Errors down: %d'%(errors_down)
