import sys
from PyQt4 import QtCore, QtGui, QtNetwork
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from AD9910 import ad9910

# ID start from 2
config = (
        ('Pumping',270,0.2,0.5),
        ('Cooling',260,0.2,0.5),
        ('Detection',270,0.4,0.5),
        ('Raman1',200.027,0.2,0.5),
        ('Raman2',200,1,1)
        )
PORT = 9999
        
dds = ad9910()

class LVSpinBox(QDoubleSpinBox):
    stepChanged = QtCore.pyqtSignal()

    def stepBy(self, step):
        value = self.value()
        digit = str(self.text()).find('.') - self.lineEdit().cursorPosition()
        if digit < 0:
            digit += 1
        self.setValue(value + step*(10**digit))
        if self.value() != value:
            self.stepChanged.emit()

    def onValueChanged(self,func):
        self.editingFinished.connect(func)
        self.stepChanged.connect(func)

class LVNumCtrl:
    def __init__(self, parent = None):
        if isinstance(parent, QLayout):
            self.hbox = QHBoxLayout()
            parent.addLayout(self.hbox)
        else:
            self.hbox = QHBoxLayout(parent)
        self.label = QLabel()
        self.spin = LVSpinBox()
        
        self.label.setFont(QFont("Microsoft YaHei", 14))
        self.spin.setFont(QFont("Microsoft YaHei", 16))
        
        self.hbox.addWidget(self.label)
        self.hbox.addWidget(self.spin)

    def setLabel(self, text):
        self.label.setText(text)

    def value(self):
        return self.spin.value()

    def setValue(self, val):
        self.spin.setValue(val)

class DDSCtrl:
    def __init__(self, parent = None):
        self.group = QGroupBox(parent)
        self.group.setFont(QFont("Microsoft YaHei", 12))
        
        self.vbox = QVBoxLayout(self.group)
        self.freq = LVNumCtrl(self.vbox)
        self.hbox = QHBoxLayout()
        self.amp = LVNumCtrl(self.hbox)
        self.pll = QCheckBox('PLL',self.group)
        self.pll.setLayoutDirection(Qt.RightToLeft)
        self.pll.setFont(QFont("Microsoft YaHei", 12))
        self.hbox.addWidget(self.pll)
        self.vbox.addLayout(self.hbox)
        
        self.freq.setLabel('Freq')
        #self.freq.spin.setSuffix(' MHz')
        self.freq.spin.setDecimals(4)
        self.freq.spin.setRange(0,1000)
        self.freq.spin.onValueChanged(self.setFreq)

        self.amp.setLabel('Amp')
        self.amp.spin.setRange(0,1)
        self.amp.spin.onValueChanged(self.setAmp)
        
        self.dut = None
        self.timer = None
    
    def setLabel(self, text):
        self.group.setTitle(text)
    
    def setEnabled(self, state):
        self.group.setEnabled(state)
        if state:
            self.timer = QTimer()
            self.timer.timeout.connect(self.getStatus)
            self.timer.start(1000)
        elif self.timer != None:
            self.timer.stop()
    
    def setMaxAmp(self, amp):
        self.amp.spin.setRange(0,amp)
        
    def setID(self, dut):
        self.dut = dut
        
    def setFreq(self, freq = None):
        if freq == None:
            freq = self.freq.value()
        else:
            self.freq.setValue(freq)
        #print('board {0} set freq {1}'.format(self.dut, freq))
        dds.parameter(self.dut, 1e6*self.freq.value(), self.amp.value())

    def setAmp(self, amp = None):
        if amp == None:
            amp = self.amp.value()
        else:
            self.amp.setValue(amp)
        #print('board {0} set amp {1}'.format(self.dut, amp))
        dds.parameter(self.dut, 1e6*self.freq.value(), self.amp.value())
    
    def getStatus(self):
        state = dds.pll_lock(self.dut)
        #print('board {0} PLL status {1}'.format(self.dut,state))
        self.pll.setCheckState(state)
        if not state:
            dds.ConfigPort(self.dut)
            dds.parameter(self.dut, 1e6*self.freq.value(), self.amp.value())
            
class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle('DDS')
        
        self.box = QVBoxLayout()
        self.setLayout(self.box)
        
        self.ctrls = QHBoxLayout()
        self.box.addLayout(self.ctrls)
        
        self.btnReload = QPushButton('Reload')
        self.btnReload.setFont(QFont("Microsoft YaHei", 12))
        self.ctrls.addWidget(self.btnReload)
        
        self.dds = []
        for i in range(len(config)):
            self.dds.append(DDSCtrl(self))
            self.dds[i].setLabel(config[i][0])
            self.box.addWidget(self.dds[i].group)
            
        self.btnReload.clicked.connect(self.reload)
        self.server = QTcpServer()
        self.server.listen(QHostAddress("0.0.0.0"), PORT)
        self.server.newConnection.connect(self.accept)
        self.clients = []
    
    def reload(self):
        dds.reload()
        for i in range(len(config)):
            self.dds[i].setEnabled(False)
        for k in dds._handle:
            i = k - 2
            self.dds[i].setID(k)
            self.dds[i].setFreq(config[i][1])
            self.dds[i].setAmp(config[i][2])
            self.dds[i].setMaxAmp(config[i][3])
            self.dds[i].setEnabled(True)
    
    def accept(self):
        client = self.server.nextPendingConnection()
        self.clients.append(client)
        client.readyRead.connect(self.receive)
        client.disconnected.connect(self.close)
    
    def receive(self):
        for c in self.clients:
            if c.bytesAvailable() > 0:
                s = str(c.readAll()).split()
                cmd = s[0]
                dds = self.dds[int(s[1])]
                if cmd.endswith('?'):
                    val = 0
                    if cmd.startswith('FREQ'):
                        val = dds.freq.value()
                    elif cmd.startswith('AMP'):
                        val = dds.amp.value()
                    c.write('{0}\r\n'.format(val,'%lf'))
                elif cmd.startswith('FREQ'):
                    dds.setFreq(float(s[2]))
                elif cmd.startswith('AMP'):
                    dds.setAmp(float(s[2]))
    
    def close(self):
        for c in self.clients:
            if c.state() == 0:
                self.clients.remove(c)
                
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    window.reload()
    sys.exit(app.exec_())