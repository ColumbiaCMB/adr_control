import gui
from superplot import Superplot
import adr_controller
import data_logger
import message_logger
# Custom modules


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib
import numpy as np
import IPython
import time
import threading
import logging

import Pyro4

import sys


class PlotDialog(QDialog,gui.Ui_Form):
    # Connects GUI pieces to functions. Grabs data from sim900 and updates gui.
    def __init__(self, qApp, parent=None):
        super(PlotDialog, self).__init__(parent)
        
        self.sim900 = Pyro4.Proxy("PYRONAME:sim900server")
        self.cryomech = Pyro4.Proxy("PYRONAME:cryomechserver")
        self.relay = Pyro4.Proxy("PYRONAME:relayserver")
        
        self.message_queue = []
        self.message_logger = message_logger.MessageFile(method=self.push_message)
        # This is for queued messages from the controller.
        
        self.controller = adr_controller.AdrController(client=self.sim900,gui_input=True,gui_message_display=self.pass_to_logger)
        self.data_logger = data_logger.DataFile()
        # Sets up sim900 pyro proxy, AdrController, and data_logger - which records data in a netcdf format.
        
        self.last_sim900_timestamp = 0
        self.last_cryomech_timestamp = 0
        # Used to make sure dictionaries are fully populated before the GUI logs them.
        
        self.__app = qApp
        self.setupUi(self)
        self.setupLists()
        self.active_lists = [self.temp_list,self.magnet_current_list]
        self.setupTimer()
        # Timer for update
        self.setupTimer2()
        # Timer for checking alerts from controller
        self.setupTimer3()
        # Timer for displaying queued messages from controller
        
        self.plot = Superplot(self)
        self.plotLayout.insertWidget(0,self.plot.canvas)
        self.toolbar=NavigationToolbar(self.plot.canvas,self)
        self.navbar_layout.insertWidget(0,self.toolbar)
        # Needed for starting the plots.
        
        self.setupSlots()
    
           
    def setupTimer(self):
        #Create a QT Timer that will timeout every half-a-second
        #The timeout is connected to the update function
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(3000)
    
        
    def setupSlots(self):
        #QObject.connect(self.bridge_setpoint_command_value,SIGNAL("editingFinished()"),self.set_bridge_setpoint)
        
        QObject.connect(self.regenerate_button,SIGNAL("clicked()"), self.request_regenerate)
        QObject.connect(self.regulate_button,SIGNAL("clicked()"), self.request_regulate)
        QObject.connect(self.stop_button,SIGNAL("clicked()"), self.request_standby)
        
        QObject.connect(self.plotoptions,SIGNAL("activated(const QString&)"),self.plot_toggle1)
        QObject.connect(self.plotoptions2,SIGNAL("activated(const QString&)"),self.plot_toggle2)
        
        self.toggle_controller_button.clicked.connect(self.toggle_controller)
        self.clear_history_button.clicked.connect(self.clear_history)
        self.update_setpoint_button.clicked.connect(self.request_update_setpoint)
        self.update_setpoint_button.setEnabled(False)
        
    def clear_history(self):
        self.setupLists()
        # Clears lists
        command1=self.plotoptions.currentText()
        command2=self.plotoptions2.currentText()
        self.plot_toggle1(command1)
        self.plot_toggle2(command2)
        #self.plot.plot_toggle(0,command1)
        #self.plot.plot_toggle(1,command2)
        # Makes sure the plot is looking at the most recent lists.
        # Note, why does the uncommented code above work, and the commented out code not work? They should call the same methods.
        # Perhaps superplot can't look at the parent lists?
        
    def setupLists(self):
        #Create lists in which bridge-temperature and bridge-setpoint values will be stored
        self.temp_list = []
        self.pid_setpoint_list = []
        self.pid_setpoint_input_monitor_list=[]
        self.magnet_current_list=[]
        self.magnet_voltage_list=[]
        
        self.magnet_diode_temp_list=[]
        self.fiftyk_stage_temp_list=[]
        self.floating_diode_temp_list=[]
        
        self.time_list=[]
        
    def update(self):
        sim900_data = self.sim900.fetch_dict()
        if sim900_data['time']==self.last_sim900_timestamp:
            # Throws out the dictionary and ends if the timestamp hasn't changed.
            return
        else:
            self.last_sim900_timestamp=sim900_data['time']
            self.data_logger.update(sim900_data)
            
        cryomech_data=self.cryomech.fetch_dict()
        if cryomech_data['time']==self.last_cryomech_timestamp:
            return
        else:
            self.last_cryomech_timestamp=sim900_data['time']
            self.data_logger.update(cryomech_data)
            
            
        relay_data = self.relay.fetch_dict()
        if relay_data['time']==self.last_relay_timestamp:
            return
        else:
            self.last_relay_timestamp=sim900_data['time']
            self.data_logger.update(relay_data)
            
        # Is this a bug? We probably only want to worry about sim900 timestamp.
        
        
        temp_bridge = sim900_data['bridge_temp_value']
        self.temp_bridge_value.setText(str(temp_bridge))
        temp_floating_diode_value = sim900_data['therm_temperature2']
        self.temp_floating_diode_value.setText(str(temp_floating_diode_value))
        temp_magnet_diode_value = sim900_data['therm_temperature1']
        self.temp_magnet_diode_value.setText(str(temp_magnet_diode_value))
        temp_50K = sim900_data['therm_temperature0']
        self.temp_50k_value.setText(str(temp_50K))
        current = sim900_data['dvm_volts1']
        self.magnet_current_value.setText(str(current))
        voltage = sim900_data['dvm_volts0']
        self.magnet_voltage_value.setText(str(voltage))
        
        
        if sim900_data['cryostat_pressure']>=1:
            msg='%.2f'%(sim900_data['cryostat_pressure'])
            self.cryo_pressure_value.setText(msg)
        if sim900_data['cryostat_pressure']<1:
            msg='%.2g'%(sim900_data['cryostat_pressure'])
            self.cryo_pressure_value.setText(msg)
        
        self.bridge_overload_status_value.setText(str(sim900_data['bridge_overload_status']))
        self.bridge_autorange_gain_value.setText(str(sim900_data['bridge_autorange_gain']))
        
        self.pid_output_value.setText(str(sim900_data['pid_output_mon']))
        pid_setpoint = sim900_data['pid_setpoint']
        self.pid_setpoint_value.setText(str(pid_setpoint))
        self.pid_setpoint_input_monitor_value.setText(str(sim900_data['pid_setpoint_mon']))
        self.pid_manual_output_value.setText(str(sim900_data['pid_manual_out']))
        if sim900_data['pid_manual_status'] == 1:
            self.pid_mode_value.setText('PID')
        if sim900_data['pid_manual_status'] == 0:
            self.pid_mode_value.setText('MAN')
            
        if sim900_data['pid_ramp_on'] == 1:
            self.pid_ramp_on_value.setText('ON')
        if sim900_data['pid_ramp_on'] == 0:
            self.pid_ramp_on_value.setText('OFF')
            
        if sim900_data['pid_ramp_status'] == 0:
            self.pid_ramp_status_value.setText('IDLE')
        if sim900_data['pid_ramp_status'] == 1:
            self.pid_ramp_status_value.setText('PENDING')
        if sim900_data['pid_ramp_status'] == 2:
            self.pid_ramp_status_value.setText('RAMPING')
        if sim900_data['pid_ramp_status'] == 3:
            self.pid_ramp_status_value.setText('PAUSED')
        
        if self.controller.loop_thread.is_alive():
            self.state_value.setText(self.controller.state)
        if not self.controller.loop_thread.is_alive():
            self.state_value.setText('disconnected')
        if self.update_setpoint_button.isEnabled():
            if self.controller.state!='regulate':
                self.update_setpoint_button.setEnabled(False)
        if not self.update_setpoint_button.isEnabled():
            if self.controller.state=='regulate':
                self.update_setpoint_button.setEnabled(True)
        
        # Cryomech values
        self.temp_water_in_value.setText(str(cryomech_data['temp_water_in']))
        self.temp_water_out_value.setText(str(cryomech_data['temp_water_out']))
        self.temp_helium_value.setText(str(cryomech_data['temp_helium']))
        self.temp_oil_value.setText(str(cryomech_data['temp_oil']))
        self.avg_pressure_high_value.setText(str(cryomech_data['avg_pressure_high']))
        self.avg_pressure_low_value.setText(str(cryomech_data['avg_pressure_low']))
        if cryomech_data['comp_on']==1:
            self.comp_on_value.setText('ON')
        if cryomech_data['comp_on']==0:
            self.comp_on_value.setText('OFF')
        self.motor_current_value.setText(str(cryomech_data['motor_current']))
        
        #Update Temperature and Setpoint Lists
        if len(self.temp_list) < 1000:
            self.temp_list.append(temp_bridge)
        elif len(self.temp_list) >= 1000:
            if not (self.active_lists[0]==self.temp_list or self.active_lists[1]==self.temp_list):
            # Keeps the list length to 1000 if not an active list, lets it grow otherwise.
                del self.temp_list[0]
            self.temp_list.append(temp_bridge)

        if len(self.pid_setpoint_list) < 1000:
            self.pid_setpoint_list.append(pid_setpoint)
        elif len(self.pid_setpoint_list) >= 1000:
            if not (self.active_lists[0]==self.pid_setpoint_list or self.active_lists[1]==self.pid_setpoint_list):
                del self.pid_setpoint_list[0]
            self.pid_setpoint_list.append(pid_setpoint)
            
        if len(self.pid_setpoint_input_monitor_list) < 1000:
            self.pid_setpoint_input_monitor_list.append(sim900_data['pid_setpoint_mon'])
        elif len(self.pid_setpoint_input_monitor_list) >= 1000:
            if not (self.active_lists[0]==self.pid_setpoint_input_monitor_list or self.active_lists[1]==self.pid_setpoint_input_monitor_list):
                del self.pid_setpoint_input_monitor_list[0]
            self.pid_setpoint_input_monitor_list.append(sim900_data['pid_setpoint_mon'])
            
        if len(self.magnet_current_list) < 1000:
            self.magnet_current_list.append(current)
        elif len(self.magnet_current_list) >= 1000:
            if not (self.active_lists[0]==self.magnet_current_list or self.active_lists[1]==self.magnet_current_list):
                del self.magnet_current_list[0]
            self.magnet_current_list.append(current)
            
        if len(self.magnet_voltage_list) < 1000:
            self.magnet_voltage_list.append(voltage)
        elif len(self.magnet_voltage_list) >= 1000:
            if not (self.active_lists[0]==self.magnet_voltage_list or self.active_lists[1]==self.magnet_voltage_list):
                del self.magnet_voltage_list[0]
            self.magnet_voltage_list.append(voltage)
            
        self.update_list(self.magnet_diode_temp_list,sim900_data['therm_temperature1'])
        self.update_list(self.fiftyk_stage_temp_list,sim900_data['therm_temperature0'])
        self.update_list(self.floating_diode_temp_list,sim900_data['therm_temperature2'])
        
            
            
        self.time_list.append(sim900_data["time"])
        longer_active_list_length=max(len(self.active_lists[0]),len(self.active_lists[1]))
        if len(self.time_list)>longer_active_list_length:
            del self.time_list[:-longer_active_list_length]
        # Keeps time to the same length as the longer active_list
           
            
        #Update plots by calling the draw function.
        
        if self.autoscale_x.isChecked():
            self.plot.autoscale_x=True
        else:
            self.plot.autoscale_x=False
        if self.autoscale_y.isChecked():
            self.plot.autoscale_y=True
        else:
            self.plot.autoscale_y=False
        self.plot.draw()

    def update_list(self,list_to_update, data):
        if len(list_to_update) < 1000:
            list_to_update.append(data)
        elif len(self.magnet_voltage_list) >= 1000:
            if not (self.active_lists[0]==list_to_update or self.active_lists[1]==list_to_update):
                del list_to_update[0]
            list_to_update.append(data)
        
    def plot_toggle1(self, command):
        # Calls the plot_toggle method of the superplot with the correct command and index.
        old_active_list=self.active_lists[0]
        
        if command=="Bridge Temperature":
            self.active_lists[0]=self.temp_list
        elif command=="Magnet Current":
            self.active_lists[0]=self.magnet_current_list
        elif command=="Magnet Voltage":
            self.active_lists[0]=self.magnet_voltage_list
        elif command=="PID Setpoint":
            self.active_lists[0]=self.pid_setpoint_list
        elif command=="PID Setpoint Input Monitor":
            self.active_lists[0]=self.pid_setpoint_input_monitor_list
        elif command=='Magnet Diode Temperature':
            self.active_lists[0]=self.magnet_diode_temp_list
        elif command=='50K Stage Temperature':
            self.active_lists[0]=self.fiftyk_stage_temp_list
        elif command=='Floating Diode Temperature':
            self.active_lists[0]=self.floating_diode_temp_list
        # Resets the active list to the commanded list.
        
        
        if self.active_lists[0]!=old_active_list:
            # If the active list has changed, shorten previous lists to 1000 entries.
            del old_active_list[:-1000]
            
        
        self.plot.plot_toggle(command,0)
        # Give the plot new instructions.
        
    def plot_toggle2(self, command):
        old_active_list=self.active_lists[1]
    
        if command=="Bridge Temperature":
            self.active_lists[1]=self.temp_list
        elif command=="Magnet Current":
            self.active_lists[1]=self.magnet_current_list
        elif command=="Magnet Voltage":
            self.active_lists[1]=self.magnet_voltage_list
        elif command=="PID Setpoint":
            self.active_lists[1]=self.pid_setpoint_list
        elif command=="PID Setpoint Input Monitor":
            self.active_lists[1]=self.pid_setpoint_input_monitor_list
        elif command=='Magnet Diode Temperature':
            self.active_lists[1]=self.magnet_diode_temp_list
        elif command=='50K Stage Temperature':
            self.active_lists[1]=self.fiftyk_stage_temp_list
        elif command=='Floating Diode Temperature':
            self.active_lists[1]=self.floating_diode_temp_list
        # Resets the active list to the commanded list.
        
        if self.active_lists[1]!=old_active_list:
            # If the active list has changed, shorten previous lists to 1000 entries.
            del old_active_list[:-1000]
    
        self.plot.plot_toggle(command,1)
        
        
### Methods that deal with connecting and disconnecting the controller. ###

    def toggle_controller(self):
        if self.controller.command_thread:
            if self.controller.command_thread.is_alive():
                print 'Regenerate thread is running in controller. Terminate it before disconnecting the controller.'
                return
        if self.controller.regulate_thread:
            if self.controller.regulate_thread.is_alive():
                print 'Regulate thread is running in controller. Terminate it before disconnecting the controller.'
                return
        if self.controller.loop_thread.is_alive():
            self.disconnect_controller()
            return
        if not self.controller.loop_thread.is_alive():
            self.connect_controller()
            return
            
    def disconnect_controller(self):
        self.controller.exit=True
        start=time.time()
        while self.controller.loop_thread.is_alive():
            tic=time.time()
            if tic-start>5.0:
                print 'Disconnect controller timed out.'
                return
            time.sleep(0.5)
        self.regenerate_button.setEnabled(False)
        self.regulate_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.controller_value.setText('Controller disconnected.')
        self.timer2.stop()
        self.timer3.stop()
    
    def connect_controller(self):
        self.controller.exit=False
        self.controller.start_loop_thread()
        self.regenerate_button.setEnabled(True)
        self.regulate_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.controller_value.setText('Controller connected.')
        self.timer2.start(2000)
        self.timer3.start(300)
        
        
### Methods that request actions from the controller. Connected to buttons. ###
        
    def request_regenerate(self):
    
        if self.controller.state!='standby':
            msg='To regenerate, the controller must be in standby mode.'
            self.raise_error_box(msg)
            return
        if self.controller.manual_output_now!=0.0:
            msg='To regenerate, manual output must be zero.'
            self.raise_error_box(msg)
            return
    
        setpoint=self.setpoint_value.value()
        current=self.peak_current_value.value()
        rru=self.ramp_rate_up_value.value()
        rrd=self.ramp_rate_down_value.value()
        dwell=self.dwell_time_value.value()
    
        msg='Prepared to regenerate.\nSettings are:\n\nSetpoint: %f\nPeak Current: %f\nRamp Rate Up: %f\nRamp Rate Down: %f\nDwell Time: %f\n\nPress OK to continue.'%(setpoint,current,rru,rrd,dwell)
    
        self.raise_verification_box(msg, self.send_regenerate_request)
        
    def send_regenerate_request(self):
        setpoint=self.setpoint_value.value()
        current=self.peak_current_value.value()
        rru=self.ramp_rate_up_value.value()
        rrd=self.ramp_rate_down_value.value()
        dwell=self.dwell_time_value.value()
        self.controller.request_regenerate(pid_setpoint_goal=setpoint,peak_current=current, ramp_rate_up=rru, ramp_rate_down=rrd, dwell_time=dwell)\
        
    def request_regulate(self):
    
        if self.controller.state!='standby':
            msg='To regulate, the controller must be in standby mode.'
            self.raise_error_box(msg)
            return
        if self.controller.manual_output_now!=0.0:
            msg='To regulate, manual output must be zero.'
            self.raise_error_box(msg)
            return
           
        setpoint=self.setpoint_value.value() 
        step=self.pid_step_value.value()
            
        if setpoint<self.controller.data['bridge_temp_value']:
            msg='Regulate temperature is below current temperature. Must regulate at a temperature higher than temperature now.'
            self.raise_error_box(msg)
            return
        
        msg='Prepared to regulate.\nSettings are:\n\nSetpoint: %f\nPID Ramp Rate: %f\n\nPress OK to continue.'%(setpoint,step)
    
        self.raise_verification_box(msg, self.send_regulate_request)
        
    def send_regulate_request(self):
        setpoint=self.setpoint_value.value()
        step=self.pid_step_value.value()
        self.controller.request_regulate(pid_setpoint_goal=setpoint,pid_ramp_rate=step)
        
    def request_standby(self):
        rrd=self.ramp_rate_down_value.value()
        self.controller.request_standby(ramp_down=rrd)
        
    def request_update_setpoint(self):
    
        if self.controller.data['pid_ramp_status']!=0:
            msg='PID ramp status is not IDLE. Wait for current ramp to finish before updating setpoint.'
            self.raise_error_box(msg)
            return
    
        setpoint=self.setpoint_value.value()
        msg='Prepared to update setpoint.\nSetpoint: %f\n\nPress OK to continue.'%(setpoint)
    
        self.raise_verification_box(msg, self.send_update_setpoint_request)
    
    def send_update_setpoint_request(self):
        setpoint=self.setpoint_value.value()
        self.controller.update_setpoint(setpoint)
        
    def raise_verification_box(self,msg,requested_method):
        msg_box=QMessageBox()
        msg_box.setText(msg)
        msg_box.setModal(False)
        
        action_button=QPushButton('OK')
        action_button.clicked.connect(requested_method)
        action_button.setFocusPolicy(Qt.NoFocus)
        msg_box.addButton(action_button, QMessageBox.ActionRole)
        
        reject_button=QPushButton('Cancel')
        reject_button.clicked.connect(self.reject)
        reject_button.setFocusPolicy(Qt.NoFocus)
        msg_box.addButton(reject_button, QMessageBox.ActionRole)
        
        msg_box.exec_()
        
    def raise_error_box(self,msg):
        msg_box=QMessageBox()
        msg_box.setText(msg)
        msg_box.setModal(False)
        
        action_button=QPushButton('OK')
        action_button.clicked.connect(self.reject)
        action_button.setFocusPolicy(Qt.NoFocus)
        msg_box.addButton(action_button, QMessageBox.ActionRole)
        
        msg_box.exec_()
        
    def reject(self):
        return
        
### Methods that deal with the controller requesting user input. ###
        
    def raise_message_box(self,msg):
        msg_box=QMessageBox()
        msg_box.setText(msg)
        msg_box.setModal(False)
        
        action_button=QPushButton('OK')
        action_button.clicked.connect(lambda: self.respond_to_controller(msg))
        action_button.setFocusPolicy(Qt.NoFocus)
        msg_box.addButton(action_button, QMessageBox.ActionRole)
        
        msg_box.exec_()
        
    def respond_to_controller(self,message):
        if message==self.controller.message_for_gui:
        # Makes sure the user is responding to the correct message.
            self.controller.gui_response=True
        
    def check_for_message(self):
        if self.controller.message_for_gui!=None:
            self.raise_message_box(self.controller.message_for_gui)
                
    def setupTimer2(self):
        self.timer2 = QTimer()
        self.timer2.timeout.connect(self.check_for_message)
        self.timer2.start(2000)
        
### Methods that deal with displaying messages from GUI (and logging them). ###
        
    def push_message(self,message):
        # Pushes messages to the message_queue
        self.message_queue.append(message)
        
    def display_message(self):
        # Grabs the first value in the message_queue and displays it on message_value
        if len(self.message_queue)>0:
            msg=self.message_queue.pop(0)
            self.message_value.append(msg)
        
    def setupTimer3(self):
        # Causes the display message method to trigger every 300 ms
        self.timer3=QTimer()
        self.timer3.timeout.connect(self.display_message)
        self.timer3.start(300)
        
    def pass_to_logger(self, message):
        self.message_logger.log(message)
        
    
        
def main():
    app = QApplication(sys.argv)
    app.quitOnLastWindowClosed = True
    form = PlotDialog(app)
    form.show()
    IPython.embed()
    app.exit()
    
if __name__ == "__main__":
    main()
