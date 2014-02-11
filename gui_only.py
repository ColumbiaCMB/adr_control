# Just the GUI from fridge_gui in hdp_devel. To be used as basis for automated control of adr.

import sys
from PyQt4 import QtGui, QtCore, Qt

from plot_template import plot_template
# I just copied the plot_template.py from the previous project. It doesn't seem to have anything other than GUI template in it.

class fridge_gui(QtGui.QDialog):

    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUI()
        
    def setupUI(self):
        #Create Window and its Geometry
        self.setWindowTitle("Fridge Controls")
        self.resize(1200,550)
        self.centerUI()
        self.organizeUI()

    def centerUI(self):
        #Centers the GUI on the screen
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def organizeUI(self):
        #Create Widgets
        self.top_widget = QtGui.QTabWidget()
        self.readings_widget = QtGui.QWidget()
        self.commands_widget = QtGui.QWidget()
        self.bottom_widget = QtGui.QWidget()

        #Create Groups
        self.measurements_group = QtGui.QGroupBox("Measurements")
        self.pid_readout_group = QtGui.QGroupBox("PID Readout")
        self.procedures_group = QtGui.QGroupBox("Procedures")
        self.pid_commands_group = QtGui.QGroupBox("PID Commands")
        self.plot_group = QtGui.QGroupBox("Temperature v. Time")

        #Create Layouts
        self.measurements_layout = QtGui.QGridLayout()
        self.pid_readout_layout = QtGui.QGridLayout()
        self.procedures_layout = QtGui.QVBoxLayout()
        self.pid_commands_layout = QtGui.QGridLayout()
        self.plot_layout = QtGui.QGridLayout()

        #Create Labels
        self.bridge_setpoint_label = QtGui.QLabel("Bridge Setpoint")
        self.bridge_setpoint_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.temp_bridge_label = QtGui.QLabel("Bridge Temperature")
        self.temp_bridge_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.temp_3K_label = QtGui.QLabel("3K Temperature")
        self.temp_3K_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.temp_50K_label = QtGui.QLabel("50K Temperature")
        self.temp_50K_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.current_label = QtGui.QLabel("Magnet Current")
        self.current_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)

        self.setpoint_readout_label = QtGui.QLabel("Setpoint")
        self.setpoint_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.measure_readout_label = QtGui.QLabel("Measure")
        self.measure_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.error_readout_label = QtGui.QLabel("Error")
        self.error_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.output_readout_label = QtGui.QLabel("Output")
        self.output_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.p_status_readout_label = QtGui.QLabel("P-Status")
        self.p_status_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.i_status_readout_label = QtGui.QLabel("I-Status")
        self.i_status_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.d_status_readout_label = QtGui.QLabel("D-Status")
        self.d_status_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.o_status_readout_label = QtGui.QLabel("Offset Status")
        self.o_status_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.p_gain_readout_label = QtGui.QLabel("P-Gain")
        self.p_gain_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.i_gain_readout_label = QtGui.QLabel("I-Gain")
        self.i_gain_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.d_gain_readout_label = QtGui.QLabel("D-Gain")
        self.d_gain_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.o_readout_label = QtGui.QLabel("Offset")
        self.o_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.ramp_readout_label = QtGui.QLabel("Ramping")
        self.ramp_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.ramp_rate_readout_label = QtGui.QLabel("Ramp Rate")
        self.ramp_rate_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.ramp_status_readout_label = QtGui.QLabel("Ramp Status")
        self.ramp_status_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.pid_status_readout_label = QtGui.QLabel("PID Control")
        self.pid_status_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.manual_output_readout_label = QtGui.QLabel("Manual Output")
        self.manual_output_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)

        self.bridge_setpoint_command_label = QtGui.QLabel("Bridge Setpoint (Direct)")
        self.bridge_setpoint_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.pid_setpoint_command_label = QtGui.QLabel("PID Setpoint")
        self.pid_setpoint_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.pid_status_command_label = QtGui.QLabel("PID Status")
        self.pid_status_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.manual_output_command_label = QtGui.QLabel("Manual Output")
        self.manual_output_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.ramp_command_label = QtGui.QLabel("Ramping")
        self.ramp_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.ramp_rate_command_label = QtGui.QLabel("Ramp Rate")
        self.ramp_rate_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.p_status_command_label = QtGui.QLabel("Proportional Status")
        self.p_status_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.i_status_command_label = QtGui.QLabel("Integral Status")
        self.i_status_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.d_status_command_label = QtGui.QLabel("Derivative Status")
        self.d_status_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.o_status_command_label = QtGui.QLabel("Offset Status")
        self.o_status_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.p_gain_command_label = QtGui.QLabel("Proportional Gain")
        self.p_gain_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.i_gain_command_label = QtGui.QLabel("Integral Gain")
        self.i_gain_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.d_gain_command_label = QtGui.QLabel("Derivative Gain")
        self.d_gain_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.o_command_label = QtGui.QLabel("Offset")
        self.o_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)

        self.status_label = QtGui.QLabel("Status:")
        self.status_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.status_bridge_setpoint_command_label = QtGui.QLabel("Bridge Setpoint Control:")
        self.status_bridge_setpoint_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)

        #Create Value Boxes
        self.bridge_setpoint_value = QtGui.QLineEdit()
        self.bridge_setpoint_value.setReadOnly(True)
        self.temp_bridge_value = QtGui.QLineEdit()
        self.temp_bridge_value.setReadOnly(True)
        self.temp_3K_value = QtGui.QLineEdit()
        self.temp_3K_value.setReadOnly(True)
        self.temp_50K_value = QtGui.QLineEdit()
        self.temp_50K_value.setReadOnly(True)
        self.current_value = QtGui.QLineEdit()
        self.current_value.setReadOnly(True)

        self.setpoint_readout_value = QtGui.QLineEdit()
        self.setpoint_readout_value.setReadOnly(True)
        self.measure_readout_value = QtGui.QLineEdit()
        self.measure_readout_value.setReadOnly(True)
        self.error_readout_value = QtGui.QLineEdit()
        self.error_readout_value.setReadOnly(True)
        self.output_readout_value = QtGui.QLineEdit()
        self.output_readout_value.setReadOnly(True)
        self.p_status_readout_value = QtGui.QLineEdit()
        self.p_status_readout_value.setReadOnly(True)
        self.i_status_readout_value = QtGui.QLineEdit()
        self.i_status_readout_value.setReadOnly(True)
        self.d_status_readout_value = QtGui.QLineEdit()
        self.d_status_readout_value.setReadOnly(True)
        self.o_status_readout_value = QtGui.QLineEdit()
        self.o_status_readout_value.setReadOnly(True)
        self.p_gain_readout_value = QtGui.QLineEdit()
        self.p_gain_readout_value.setReadOnly(True)
        self.i_gain_readout_value = QtGui.QLineEdit()
        self.i_gain_readout_value.setReadOnly(True)
        self.d_gain_readout_value = QtGui.QLineEdit()
        self.d_gain_readout_value.setReadOnly(True)
        self.o_readout_value = QtGui.QLineEdit()
        self.o_readout_value.setReadOnly(True)
        self.ramp_readout_value = QtGui.QLineEdit()
        self.ramp_readout_value.setReadOnly(True)
        self.ramp_rate_readout_value = QtGui.QLineEdit()
        self.ramp_rate_readout_value.setReadOnly(True)
        self.ramp_status_readout_value = QtGui.QLineEdit()
        self.ramp_status_readout_value.setReadOnly(True)
        self.pid_status_readout_value = QtGui.QLineEdit()
        self.pid_status_readout_value.setReadOnly(True)
        self.manual_output_readout_value = QtGui.QLineEdit()
        self.manual_output_readout_value.setReadOnly(True)

        self.enabled_command_check = QtGui.QCheckBox("Enabled")
        self.enabled_command_check.setChecked(False)
        self.bridge_setpoint_command_value = QtGui.QDoubleSpinBox()
        self.bridge_setpoint_command_value.setEnabled(False)
        self.bridge_setpoint_command_value.setRange(0.0,0.5)
        self.bridge_setpoint_command_value.setSingleStep(0.1)
        self.bridge_setpoint_command_value.setDecimals(6)
        self.pid_setpoint_command_value = QtGui.QDoubleSpinBox()
        self.pid_setpoint_command_value.setEnabled(False)
        self.pid_setpoint_command_value.setRange(0.0,9.4)
        self.pid_setpoint_command_value.setSingleStep(0.1)
        self.pid_setpoint_command_value.setDecimals(3)
        self.pid_status_command_value = QtGui.QComboBox()
        self.pid_status_command_value.setEnabled(False)
        self.pid_status_command_value.addItem(" ")
        self.pid_status_command_value.addItem("ON")
        self.pid_status_command_value.addItem("OFF")
        self.manual_output_command_value = QtGui.QDoubleSpinBox()
        self.manual_output_command_value.setEnabled(False)
        self.manual_output_command_value.setRange(-10.0,0.02)
        self.manual_output_command_value.setSingleStep(0.1)
        self.manual_output_command_value.setDecimals(3)
        self.ramp_command_value = QtGui.QComboBox()
        self.ramp_command_value.setEnabled(False)
        self.ramp_command_value.addItem(" ")
        self.ramp_command_value.addItem("ON")
        self.ramp_command_value.addItem("OFF")
        self.ramp_rate_command_value = QtGui.QDoubleSpinBox()
        self.ramp_rate_command_value.setEnabled(False)
        self.ramp_rate_command_value.setRange(0.0,0.01)
        self.ramp_rate_command_value.setSingleStep(0.001)
        self.ramp_rate_command_value.setDecimals(3)
        self.p_status_command_value = QtGui.QComboBox()
        self.p_status_command_value.setEnabled(False)
        self.p_status_command_value.addItem(" ")
        self.p_status_command_value.addItem("ON")
        self.p_status_command_value.addItem("OFF")
        self.i_status_command_value = QtGui.QComboBox()
        self.i_status_command_value.setEnabled(False)
        self.i_status_command_value.addItem(" ")
        self.i_status_command_value.addItem("ON")
        self.i_status_command_value.addItem("OFF")
        self.d_status_command_value = QtGui.QComboBox()
        self.d_status_command_value.setEnabled(False)
        self.d_status_command_value.addItem(" ")
        self.d_status_command_value.addItem("ON")
        self.d_status_command_value.addItem("OFF")
        self.o_status_command_value = QtGui.QComboBox()
        self.o_status_command_value.setEnabled(False)
        self.o_status_command_value.addItem(" ")
        self.o_status_command_value.addItem("ON")
        self.o_status_command_value.addItem("OFF")
        self.p_gain_command_value = QtGui.QDoubleSpinBox()
        self.p_gain_command_value.setEnabled(False)
        self.p_gain_command_value.setRange(-15.0,15.0)
        self.p_gain_command_value.setSingleStep(0.1)
        self.i_gain_command_value = QtGui.QDoubleSpinBox()
        self.i_gain_command_value.setEnabled(False)
        self.i_gain_command_value.setRange(-15.0,15.0)
        self.i_gain_command_value.setSingleStep(0.1)
        self.d_gain_command_value = QtGui.QDoubleSpinBox()
        self.d_gain_command_value.setEnabled(False)
        self.d_gain_command_value.setRange(-15.0,15.0)
        self.d_gain_command_value.setSingleStep(0.1)
        self.o_command_value = QtGui.QDoubleSpinBox()
        self.o_command_value.setEnabled(False)
        self.o_command_value.setRange(-15.0,15.0)
        self.o_command_value.setSingleStep(0.1)

        self.status_value = QtGui.QLineEdit()
        self.status_value.setReadOnly(True)
        self.status_value.setText("Ready")
        self.status_bridge_setpoint_command_value = QtGui.QDoubleSpinBox()
        self.status_bridge_setpoint_command_value.setEnabled(True)
        self.status_bridge_setpoint_command_value.setRange(0.0,0.5)
        self.status_bridge_setpoint_command_value.setSingleStep(0.1)
        self.status_bridge_setpoint_command_value.setDecimals(6)

        #Create PushButtons
        self.setup_button = QtGui.QPushButton("Set Up")
        self.warmup_button = QtGui.QPushButton("Warm Up")
        self.dumpheat_button = QtGui.QPushButton("Dump Heat")
        self.cooldown_button = QtGui.QPushButton("Cool Down")
        self.regulate_button = QtGui.QPushButton("Regulate")

        #Create Plot Background
        self.temp_plot = plot_template()

        #Add Objects to Layouts
        self.measurements_layout.addWidget(self.bridge_setpoint_label,0,0,1,1)
        self.measurements_layout.addWidget(self.bridge_setpoint_value,0,1,1,1)
        self.measurements_layout.addWidget(self.temp_bridge_label,1,0,1,1)
        self.measurements_layout.addWidget(self.temp_bridge_value,1,1,1,1)
        self.measurements_layout.addWidget(self.temp_3K_label,2,0,1,1)
        self.measurements_layout.addWidget(self.temp_3K_value,2,1,1,1)
        self.measurements_layout.addWidget(self.temp_50K_label,3,0,1,1)
        self.measurements_layout.addWidget(self.temp_50K_value,3,1,1,1)
        self.measurements_layout.addWidget(self.current_label,4,0,1,1)
        self.measurements_layout.addWidget(self.current_value,4,1,1,1)

        self.pid_readout_layout.addWidget(self.setpoint_readout_label,0,0,1,1)
        self.pid_readout_layout.addWidget(self.setpoint_readout_value,0,1,1,1)
        self.pid_readout_layout.addWidget(self.measure_readout_label,0,2,1,1)
        self.pid_readout_layout.addWidget(self.measure_readout_value,0,3,1,1)
        self.pid_readout_layout.addWidget(self.error_readout_label,0,4,1,1)
        self.pid_readout_layout.addWidget(self.error_readout_value,0,5,1,1)
        self.pid_readout_layout.addWidget(self.output_readout_label,0,6,1,1)
        self.pid_readout_layout.addWidget(self.output_readout_value,0,7,1,1)
        self.pid_readout_layout.addWidget(self.p_status_readout_label,1,0,1,1)
        self.pid_readout_layout.addWidget(self.p_status_readout_value,1,1,1,1)
        self.pid_readout_layout.addWidget(self.i_status_readout_label,1,2,1,1)
        self.pid_readout_layout.addWidget(self.i_status_readout_value,1,3,1,1)
        self.pid_readout_layout.addWidget(self.d_status_readout_label,1,4,1,1)
        self.pid_readout_layout.addWidget(self.d_status_readout_value,1,5,1,1)
        self.pid_readout_layout.addWidget(self.o_status_readout_label,1,6,1,1)
        self.pid_readout_layout.addWidget(self.o_status_readout_value,1,7,1,1)
        self.pid_readout_layout.addWidget(self.p_gain_readout_label,2,0,1,1)
        self.pid_readout_layout.addWidget(self.p_gain_readout_value,2,1,1,1)
        self.pid_readout_layout.addWidget(self.i_gain_readout_label,2,2,1,1)
        self.pid_readout_layout.addWidget(self.i_gain_readout_value,2,3,1,1)
        self.pid_readout_layout.addWidget(self.d_gain_readout_label,2,4,1,1)
        self.pid_readout_layout.addWidget(self.d_gain_readout_value,2,5,1,1)
        self.pid_readout_layout.addWidget(self.o_readout_label,2,6,1,1)
        self.pid_readout_layout.addWidget(self.o_readout_value,2,7,1,1)
        self.pid_readout_layout.addWidget(self.ramp_readout_label,3,2,1,1)
        self.pid_readout_layout.addWidget(self.ramp_readout_value,3,3,1,1)
        self.pid_readout_layout.addWidget(self.ramp_rate_readout_label,3,4,1,1)
        self.pid_readout_layout.addWidget(self.ramp_rate_readout_value,3,5,1,1)
        self.pid_readout_layout.addWidget(self.ramp_status_readout_label,3,6,1,1)
        self.pid_readout_layout.addWidget(self.ramp_status_readout_value,3,7,1,1)
        self.pid_readout_layout.addWidget(self.pid_status_readout_label,4,4,1,1)
        self.pid_readout_layout.addWidget(self.pid_status_readout_value,4,5,1,1)
        self.pid_readout_layout.addWidget(self.manual_output_readout_label,4,6,1,1)
        self.pid_readout_layout.addWidget(self.manual_output_readout_value,4,7,1,1)

        self.procedures_layout.addWidget(self.setup_button)
        self.procedures_layout.addWidget(self.warmup_button)
        self.procedures_layout.addWidget(self.dumpheat_button)
        self.procedures_layout.addWidget(self.cooldown_button)
        self.procedures_layout.addWidget(self.regulate_button)

        self.pid_commands_layout.addWidget(self.enabled_command_check,0,0,1,1)
        self.pid_commands_layout.addWidget(self.bridge_setpoint_command_label,0,2,1,1)
        self.pid_commands_layout.addWidget(self.bridge_setpoint_command_value,0,3,1,2)
        self.pid_commands_layout.addWidget(self.pid_setpoint_command_label,0,5,1,1)
        self.pid_commands_layout.addWidget(self.pid_setpoint_command_value,0,6,1,2)
        self.pid_commands_layout.addWidget(self.pid_status_command_label,1,2,1,1)
        self.pid_commands_layout.addWidget(self.pid_status_command_value,1,3,1,2)
        self.pid_commands_layout.addWidget(self.manual_output_command_label,1,5,1,1)
        self.pid_commands_layout.addWidget(self.manual_output_command_value,1,6,1,2)
        self.pid_commands_layout.addWidget(self.ramp_command_label,2,2,1,1)
        self.pid_commands_layout.addWidget(self.ramp_command_value,2,3,1,2)
        self.pid_commands_layout.addWidget(self.ramp_rate_command_label,2,5,1,1)
        self.pid_commands_layout.addWidget(self.ramp_rate_command_value,2,6,1,2)
        self.pid_commands_layout.addWidget(self.p_status_command_label,3,0,1,1)
        self.pid_commands_layout.addWidget(self.p_status_command_value,3,1,1,1)
        self.pid_commands_layout.addWidget(self.i_status_command_label,3,2,1,1)
        self.pid_commands_layout.addWidget(self.i_status_command_value,3,3,1,1)
        self.pid_commands_layout.addWidget(self.d_status_command_label,3,4,1,1)
        self.pid_commands_layout.addWidget(self.d_status_command_value,3,5,1,1)
        self.pid_commands_layout.addWidget(self.o_status_command_label,3,6,1,1)
        self.pid_commands_layout.addWidget(self.o_status_command_value,3,7,1,1)
        self.pid_commands_layout.addWidget(self.p_gain_command_label,4,0,1,1)
        self.pid_commands_layout.addWidget(self.p_gain_command_value,4,1,1,1)
        self.pid_commands_layout.addWidget(self.i_gain_command_label,4,2,1,1)
        self.pid_commands_layout.addWidget(self.i_gain_command_value,4,3,1,1)
        self.pid_commands_layout.addWidget(self.d_gain_command_label,4,4,1,1)
        self.pid_commands_layout.addWidget(self.d_gain_command_value,4,5,1,1)
        self.pid_commands_layout.addWidget(self.o_command_label,4,6,1,1)
        self.pid_commands_layout.addWidget(self.o_command_value,4,7,1,1)

        self.plot_layout.addWidget(self.temp_plot,0,0,1,4)
        self.plot_layout.addWidget(self.status_label,1,0,1,1)
        self.plot_layout.addWidget(self.status_value,1,1,1,1)
        self.plot_layout.addWidget(self.status_bridge_setpoint_command_label,1,2,1,1)
        self.plot_layout.addWidget(self.status_bridge_setpoint_command_value,1,3,1,1)

        #Add Layouts to Groups
        self.measurements_group.setLayout(self.measurements_layout)
        self.pid_readout_group.setLayout(self.pid_readout_layout)
        self.procedures_group.setLayout(self.procedures_layout)
        self.pid_commands_group.setLayout(self.pid_commands_layout)
        self.plot_group.setLayout(self.plot_layout)

        #Add Groups to Widgets
        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.measurements_group)
        hbox1.addWidget(self.pid_readout_group)
        self.readings_widget.setLayout(hbox1)

        hbox2 = QtGui.QHBoxLayout()
        hbox2.addWidget(self.procedures_group)
        hbox2.addWidget(self.pid_commands_group)
        self.commands_widget.setLayout(hbox2)

        vbox1 = QtGui.QVBoxLayout()
        vbox1.addWidget(self.plot_group)
        self.bottom_widget.setLayout(vbox1)

        #Add Widgets to TabWidget
        self.top_widget.addTab(self.readings_widget, "Readings")
        self.top_widget.addTab(self.commands_widget, "Commands")

        #Add TabWidget and PlotWidget to Window
        vbox2 = QtGui.QVBoxLayout()
        vbox2.addWidget(self.top_widget)
        vbox2.addWidget(self.bottom_widget)
        self.setLayout(vbox2)
        
def main():
    app = QtGui.QApplication(sys.argv)
    fg = fridge_gui()
    fg.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
