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
        self.bridge_temp=self.nc.createVariable('bridge_temp',np.float32,dimensions=('time',))
        self.fiftyk_temp=self.nc.createVariable('50k_temp',np.float32,dimensions=('time',))
        self.fourk_temp=self.nc.createVariable('4k_temp',np.float32,dimensions=('time',))
        self.mag_volt=self.nc.createVariable('mag_volt',np.float32,dimensions=('time',))
        self.mag_current=self.nc.createVariable('mag_current',np.float32,dimensions=('time',))
        # Add more variables here.
        
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
        
