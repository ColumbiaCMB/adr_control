from widget import Ui_Widget

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib
import numpy as np
import IPython
import time
import Pyro4

import sys


class PlotDialog(QDialog,Ui_Widget):
    def __init__(self, qApp, parent=None):
        super(PlotDialog, self).__init__(parent)
        
        self.server=Pyro4.Proxy("PYRONAME:simple_server")
        
        self.__app = qApp
        self.setupUi(self)
        self.setupTimer()
        
        self.dpi = 72
        self.fig = Figure((9.1, 5.2), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.verticalLayout.insertWidget(0,self.canvas)
        self.canvas.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.axes = self.fig.add_subplot(111)
        
    def update(self):
        list=self.server.fetch_data()
        self.axes.cla()
        if len(list)<51:
            self.axes.plot(list)
        else:
            self.axes.plot(list[-50:])
        self.canvas.draw()
        #print list
        #for debugging
        
    def setupTimer(self):
        #Create a QT Timer that will timeout every half-a-second
        #The timeout is connected to the update function
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(500)



def main():
    app = QApplication(sys.argv)
    app.quitOnLastWindowClosed = True
    form = PlotDialog(app)
    form.show()
    IPython.embed()
    app.exit()
    
if __name__ == "__main__":
    main()
