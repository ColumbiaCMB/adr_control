# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gui.ui'
#
# Created: Wed Feb 12 11:41:49 2014
#      by: PyQt4 UI code generator 4.8.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(942, 566)
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget = QtGui.QTabWidget(Form)
        self.tabWidget.setGeometry(QtCore.QRect(0, 0, 941, 161))
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tab = QtGui.QWidget()
        self.tab.setObjectName(_fromUtf8("tab"))
        self.tabWidget.addTab(self.tab, _fromUtf8(""))
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName(_fromUtf8("tab_2"))
        self.gridLayoutWidget = QtGui.QWidget(self.tab_2)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(10, 10, 631, 111))
        self.gridLayoutWidget.setObjectName(_fromUtf8("gridLayoutWidget"))
        self.gridLayout = QtGui.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setMargin(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.temp_bridge_value = QtGui.QLineEdit(self.gridLayoutWidget)
        self.temp_bridge_value.setReadOnly(True)
        self.temp_bridge_value.setObjectName(_fromUtf8("temp_bridge_value"))
        self.gridLayout.addWidget(self.temp_bridge_value, 1, 1, 1, 1)
        self.bridge_setpoint_value = QtGui.QLineEdit(self.gridLayoutWidget)
        self.bridge_setpoint_value.setReadOnly(True)
        self.bridge_setpoint_value.setObjectName(_fromUtf8("bridge_setpoint_value"))
        self.gridLayout.addWidget(self.bridge_setpoint_value, 0, 1, 1, 1)
        self.label_2 = QtGui.QLabel(self.gridLayoutWidget)
        self.label_2.setText(QtGui.QApplication.translate("Form", "Bridge Temperature", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.label = QtGui.QLabel(self.gridLayoutWidget)
        self.label.setText(QtGui.QApplication.translate("Form", "Bridge Setpoint", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_3 = QtGui.QLabel(self.gridLayoutWidget)
        self.label_3.setText(QtGui.QApplication.translate("Form", "3K Temp", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 0, 2, 1, 1)
        self.temp_3k_value = QtGui.QLineEdit(self.gridLayoutWidget)
        self.temp_3k_value.setReadOnly(True)
        self.temp_3k_value.setObjectName(_fromUtf8("temp_3k_value"))
        self.gridLayout.addWidget(self.temp_3k_value, 0, 3, 1, 1)
        self.label_4 = QtGui.QLabel(self.gridLayoutWidget)
        self.label_4.setText(QtGui.QApplication.translate("Form", "50K Temp", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout.addWidget(self.label_4, 1, 2, 1, 1)
        self.temp_50k_value = QtGui.QLineEdit(self.gridLayoutWidget)
        self.temp_50k_value.setReadOnly(True)
        self.temp_50k_value.setObjectName(_fromUtf8("temp_50k_value"))
        self.gridLayout.addWidget(self.temp_50k_value, 1, 3, 1, 1)
        self.label_5 = QtGui.QLabel(self.gridLayoutWidget)
        self.label_5.setText(QtGui.QApplication.translate("Form", "Magnet Voltage", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout.addWidget(self.label_5, 0, 4, 1, 1)
        self.label_6 = QtGui.QLabel(self.gridLayoutWidget)
        self.label_6.setText(QtGui.QApplication.translate("Form", "Magnet Current", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridLayout.addWidget(self.label_6, 1, 4, 1, 1)
        self.magnet_voltage_value = QtGui.QLineEdit(self.gridLayoutWidget)
        self.magnet_voltage_value.setReadOnly(True)
        self.magnet_voltage_value.setObjectName(_fromUtf8("magnet_voltage_value"))
        self.gridLayout.addWidget(self.magnet_voltage_value, 0, 5, 1, 1)
        self.magnet_current_value = QtGui.QLineEdit(self.gridLayoutWidget)
        self.magnet_current_value.setReadOnly(True)
        self.magnet_current_value.setObjectName(_fromUtf8("magnet_current_value"))
        self.gridLayout.addWidget(self.magnet_current_value, 1, 5, 1, 1)
        self.tabWidget.addTab(self.tab_2, _fromUtf8(""))
        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName(_fromUtf8("tab_3"))
        self.tabWidget.addTab(self.tab_3, _fromUtf8(""))
        self.verticalLayoutWidget = QtGui.QWidget(Form)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 170, 921, 391))
        self.verticalLayoutWidget.setObjectName(_fromUtf8("verticalLayoutWidget"))
        self.plotLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.plotLayout.setMargin(0)
        self.plotLayout.setObjectName(_fromUtf8("plotLayout"))

        self.retranslateUi(Form)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtGui.QApplication.translate("Form", "Number One", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtGui.QApplication.translate("Form", "Number Two", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QtGui.QApplication.translate("Form", "Number Three", None, QtGui.QApplication.UnicodeUTF8))

