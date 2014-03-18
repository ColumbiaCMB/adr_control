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
        
        #self.time_dim=self.nc.createDimension('time',None)
        #self.time_var=self.nc.createVariable('time',np.float32,dimensions=('time',))
        
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
                    self.nc.groups[group].createVariable(key,np.float32,dimensions=('time',))
                    # Create the variable
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
        
