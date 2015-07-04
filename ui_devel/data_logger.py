import netCDF4
import time
import os
import numpy as np

class DataFile():
    def __init__(self,base_dir='/home/adclocal/data/garbage_cooldown_logs',suffix=''):
        base_dir=os.path.expanduser(base_dir)
                
        fn=time.strftime('%Y-%m-%d_%H-%M-%S')
        if suffix:
            suffix=suffix.replace(' ','_')
            fn+=('_'+suffix)
        fn+='.nc'
        fn = os.path.join(base_dir,fn)
        self.filename=fn
        # Creates filename based on timestamp (year,month,day,hr,min,sec,suffix)
        
        self.nc=netCDF4.Dataset(fn,mode='w')
        # Both cryomech server and sim900 server have the 'time' key, which should be a 64 bit float.
        self.recognized_keys=dict(time=np.float64)

        
    def update(self,data):
    
        # Creates groups and variables that should be created, or adds data to existing data.
    
        try:
            group=data['group']
        except ValueError as e:
            print 'Data has no key "group". Returning.'
            return
        
        if group in self.nc.groups:
    
            length=len(self.nc.groups[group].dimensions['time'])
            
            for key in data:
            
                if key == 'group':
                    # This was already used to make groups, so we don't need to add it to the data.
                    continue
            
                if key in self.nc.groups[group].variables.keys():
                    try:
                        # Error handling in case values in the dictionary can't be converted to the correct type.
                        self.nc.groups[group].variables[key][length]=data[key]
                    except ValueError as e:
                        print 'Value error in key %s. NaN inserted. Error printed below.'%(key)
                        print e
                        self.nc.groups[group].variables[key][length]=np.nan
                else:
                    recognize_key=False
                    if key in self.recognized_keys:
                        self.nc.groups[group].createVariable(key,self.recognized_keys[key],dimensions=('time',))
                        # Recognized keys gives me a manual override for what the data_type should be.
                        # This is important for time, since time must be float64 or it has ~ 2minute precision.
                    else:
                        self.nc.groups[group].createVariable(key,np.float32,dimensions=('time',))
                        # Create the variable default as float32.
                        
                    try:
                        # Error handling in case values in the dictionary can't be converted to the correct type.
                        self.nc.groups[group].variables[key][length]=data[key]
                    except ValueError as e:
                        print 'Value error in key %s. NaN inserted. Error printed below.'%(key)
                        print e
                        self.nc.groups[group].variables[key][length]=np.nan
                        
        else:
            group=self.nc.createGroup(group)
            time_dim=group.createDimension('time',None)
            self.update(data)
            # Creates the group, creates the time dimension, and calls update again.
            
                    
        self.sync()
        
    def close(self):
        self.nc.close()
        
    def sync(self):
        self.nc.sync()
        
