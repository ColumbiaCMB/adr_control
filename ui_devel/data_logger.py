import netCDF4
import time
import os
import numpy as np

class DataFile():
    def __init__(self,base_dir='/home/adclocal/data/garbage_cooldown_logs',suffix=''):
        base_dir=os.path.expanduser(base_dir)
        
        '''if not os.path.exists(base_dir):
            try:
                os.mkdir(base_dir)
            except Exception, e:
                raise Exception("Tried to make directory %s for data file, but failed. Error was %s" % (base_dir,str(e))'''
                #syntax error somewhere in here. Can't find it, and this code isn't essential.
                
                
        fn=time.strftime('%Y-%m-%d_%H-%M-%S')
        if suffix:
            suffix=suffix.replace(' ','_')
            fn+=('_'+suffix)
        fn+='.nc'
        fn = os.path.join(base_dir,fn)
        self.filename=fn
        # Creates filename based on timestamp (year,month,day,hr,min,sec,suffix)
        
        self.nc=netCDF4.Dataset(fn,mode='w')
        
        self.time_dim=self.nc.createDimension('time',None)
        
        self.time_var=self.nc.createVariable('time',np.float32,dimensions=('time',))
        self.fiftyk_temp=self.nc.createVariable('50k_temp',np.float32,dimensions=('time',))
        self.fourk_temp=self.nc.createVariable('4k_temp',np.float32,dimensions=('time',))
        self.mag_volt=self.nc.createVariable('mag_volt',np.float32,dimensions=('time',))
        self.mag_current=self.nc.createVariable('mag_current',np.float32,dimensions=('time',))
        # Add more variables here.
        
        self.bridge_temp_value=self.nc.createVariable('bridge_temp_value',np.float32,dimensions=('time',))
        self.bridge_temp_deviation=self.nc.createVariable('bridge_temp_deviation',np.float32,dimensions=('time',))
        self.bridge_res_value=self.nc.createVariable('bridge_res_value',np.float32,dimensions=('time',))
        self.bridge_res_deviation=self.nc.createVariable('bridge_res_deviation',np.float32,dimensions=('time',))
        self.bridge_phase=self.nc.createVariable('bridge_phase',np.float32,dimensions=('time',))
        self.bridge_frequency=self.nc.createVariable('bridge_frequency',np.float32,dimensions=('time',))
        self.bridge_range=self.nc.createVariable('bridge_range',np.float32,dimensions=('time',))
        self.bridge_excitation=self.nc.createVariable('bridge_excitation',np.float32,dimensions=('time',))
        self.bridge_excitation_on=self.nc.createVariable('bridge_excitation_on',np.float32,dimensions=('time',))
        self.bridge_excitation_mode=self.nc.createVariable('bridge_excitation_mode',np.float32,dimensions=('time',))
        self.bridge_excitation_current=self.nc.createVariable('bridge_excitation_current',np.float32,dimensions=('time',))
        self.bridge_excitation_volt=self.nc.createVariable('bridge_excitation_volt',np.float32,dimensions=('time',))
        self.bridge_output_temperature=self.nc.createVariable('bridge_output_temperature',np.float32,dimensions=('time',))
        self.bridge_res_setpoint=self.nc.createVariable('bridge_res_setpoint',np.float32,dimensions=('time',))
        self.bridge_temperature_setpoint=self.nc.createVariable('bridge_temperature_setpoint',np.float32,dimensions=('time',))
        self.bridge_volts_ohms=self.nc.createVariable('bridge_volts_ohms',np.float32,dimensions=('time',))
        self.bridge_volts_kelvin=self.nc.createVariable('bridge_volts_kelvin',np.float32,dimensions=('time',))
        self.bridge_output_model=self.nc.createVariable('bridge_output_mode',np.float32,dimensions=('time',))
        self.bridge_output_value=self.nc.createVariable('bridge_output_value',np.float32,dimensions=('time',))
        
        self.pid_setpoint_mon=self.nc.createVariable('pid_setpoint_mon',np.float32,dimensions=('time',))
        self.pid_setpoint=self.nc.createVariable('pid_setpoint',np.float32,dimensions=('time',))
        self.pid_measure_mon=self.nc.createVariable('pid_measure_mon',np.float32,dimensions=('time',))
        self.pid_error_mon=self.nc.createVariable('pid_error_mon',np.float32,dimensions=('time',))
        self.pid_output_mon=self.nc.createVariable('pid_output_mon',np.float32,dimensions=('time',))
        self.pid_propor_on=self.nc.createVariable('pid_propor_on',np.float32,dimensions=('time',))
        self.pid_integral_on=self.nc.createVariable('pid_integral_on',np.float32,dimensions=('time',))
        self.pid_deriv_on=self.nc.createVariable('pid_deriv_on',np.float32,dimensions=('time',))
        self.pid_offset_on=self.nc.createVariable('pid_offset_on',np.float32,dimensions=('time',))
        self.pid_propor_gain=self.nc.createVariable('pid_propor_gain',np.float32,dimensions=('time',))
        self.pid_polarity=self.nc.createVariable('pid_polarity',np.float32,dimensions=('time',))
        self.pid_integral_gain=self.nc.createVariable('pid_integral_gain',np.float32,dimensions=('time',))
        self.pid_deriv_gain=self.nc.createVariable('pid_deriv_gain',np.float32,dimensions=('time',))
        self.pid_offset=self.nc.createVariable('pid_offset',np.float32,dimensions=('time',))
        self.pid_ramp_rate=self.nc.createVariable('pid_ramp_rate',np.float32,dimensions=('time',))
        self.pid_ramp_on=self.nc.createVariable('pid_ramp_on',np.float32,dimensions=('time',))
        self.pid_ramp_status=self.nc.createVariable('pid_ramp_status',np.float32,dimensions=('time',))
        self.pid_manual_out=self.nc.createVariable('pid_manual_out',np.float32,dimensions=('time',))
        
        self.mx_channel=self.nc.createVariable('mx_channel',np.float32,dimensions=('time',))
        
        
        
        
        self.length=0
        
    def update(self,data):
        # Could also just not fill any data if one variable is missing.
        
        # Right now matches keys, and fills data from argument. If there is not match, fills with NaN
        # self.length makes sure all lists stay the same length (and synchronized to the timestamp).
        
        for key in self.nc.variables.keys():
            try:
                self.nc.variables[key][self.length]=data[key]
            except KeyError:
                print "Key not found. NaN inserted."
                self.nc.variables[key][self.length]=np.nan
        self.length+=1
        
    def close(self):
        self.nc.close()
        
    def sync(self):
        self.nc.sync()
        
