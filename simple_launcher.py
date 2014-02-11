import sys
from data_logging import *
from control_gui import *

import IPython
# Can I not use IPython?

class launcher_main():
    def __init__(self):
        self.app = QtGui.QApplication(sys.argv)
        self.dl = data_logging()
        self.control_gui=fridge_gui(self.dl)
        
        self.setup_logging()

    def setup_logging(self):
        #This sets up a simple logging system
        self.dl.addRegisters("control_gui",self.control_gui.registers)
        
    def launch_gui(self):
        self.dl.open_file()
        self.dl.start_logging()
        #self.gui.show()
        self.control_gui.show()
        
if __name__ == "__main__":
    main_l = launcher_main()
    main_l.launch_gui()
    use_ipython = True
    print "Access main class as main_l"
    if use_ipython:
        try:
            IPython.embed()
        except AttributeError:
            IPython.Shell.IPShellEmbed()()
    sys.exit()# main_b.app.exec_())
