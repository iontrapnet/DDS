import sys, time
from ctypes import *

def chunks(seq, n):
    return (seq[i:i+n] for i in xrange(0, len(seq), n))

def bits2byte(bits):
    out = 0
    for bit in bits:
        out = (out << 1) | bit
    return out

def byte2bits(byte):
    return [int(x) for x in list('{0:08b}'.format(byte))]

def int2arr(val,length):
    arr = []
    for i in range(length):
        mask=0xFF<<(8*i)
        arr.append(int((val&mask)>>(8*i)))
    return arr

def arr2int(arr):
    val = 0
    for i in range(len(arr)):
        val |= arr[i] << (8*i)
    return val
    
class ad9910():
    _dll=windll.adiclockeval
    _portValue = [0x02, 0x00, 0x03, 0x00, 0x80]
    _portConfig = [0xFF, 0x00, 0xFF, 0x00, 0xFF]
    _regSize = [32, 32, 32, 32, 32, 48, 48, 32, 16, 32, 32, 64, 64, 32, 64, 64, 64, 64, 64, 64, 64, 64, 32, 0, 0, 0, 0, 0, 0, 0, 0, 40]
    _vid = 0x0456
    _pid = 0xEE25
    _handle = []
    _fs = 1000000000

    def __init__(self,reset=None):
        self.FindHardware()
        self.GetHandle()
        self.IsReady()
        self.ConfigPorts()
        if reset:
            for dut in range(self._NUMduts):
                self.reset(dut)
        #self.read(0x3)

    def reset(self,dut=1):
        self.SetPortValue('a',0x7,dut)
        time.sleep(0.01)
        self.SetPortValue('a',0x3,dut)
        time.sleep(0.3)
    
    def FindHardware(self):
        vidArry=c_int*1
        pidArry=c_int*1
        vid=vidArry(self._vid)
        pid=pidArry(self._pid)
        length=c_int(1)
        hard_instances = self._dll.FindHardware(byref(vid),byref(pid),length)
        if hard_instances == 0:
            raise RuntimeError("AD9910 instance not found!")
        else:
            self._NUMduts=hard_instances
            #print(self._dll.GetHardwareCount())
    
    def GetHandle(self):
        handleArry=c_int*self._NUMduts
        handle=handleArry(0)
        self._dll.GetHardwareHandles(byref(handle))
        for dut in range(self._NUMduts):
            #print(map(lambda x: '%04X' % x,  (self._dll.GetVendorID(handle[dut]),self._dll.GetProductID(handle[dut]))))
            infoLen = c_int(22)
            infoArry=c_ubyte*22
            info=infoArry(0)
            self._dll.GetEvbdInfo(handle[dut], byref(info), byref(infoLen))
            boardID = ''.join(['%02X' % x for x in info[10:2:-1]])
            if '0000000000AD9910' == boardID:
                self._handle.append(c_int(handle[dut]))
                major = c_int(0)
                minor = c_int(0)
                self._dll.GetFirmwareVersion(handle[dut], byref(major), byref(minor))
                #print(major, minor)
                self._dll.SetCtlValue(handle[dut], 3)
    
    def IsReady(self):
        for dut in range(self._NUMduts):
            ready=self._dll.IsConnected(self._handle[dut])
            if ready != 1:
                raise RuntimeError("AD9910 USB not ready")
            else:
                self._dll.DownloadFirmware(self._handle[dut], 'AD9910FWNR.hex')
    
    def ConfigPorts(self):
        for dut in range(self._NUMduts):
            for index in range(5):
                port=c_int(index)
                value = c_ubyte(self._portValue[index])
                self._dll.SetPortValue(self._handle[dut],port,value)
                config = c_ubyte(self._portConfig[index])
                self._dll.SetPortConfig(self._handle[dut],port,config)
            self._dll.SetHostID(self._handle[dut], id(self))
            
            #self._dll.SetLedBlink(self._handle[dut],1)
            #print(self._dll.GetLedBlink(self._handle[dut]))
            
            #self._dll.SetPortValue(self._handle[dut],0,0x02)
            #self._dll.SetPortValue(self._handle[dut],4,0x80)
            #self._dll.SetPortValue(self._handle[dut],0,0x0A)
            #self._dll.SetPortValue(self._handle[dut],4,0x80)
            #self._dll.SetPortValue(self._handle[dut],0,0x02)
            
            #self._dll.SetPortValue(self._handle[dut],0,0x02)
            #self._dll.SetPortValue(self._handle[dut],2,0x03)
            #self._dll.SetPortValue(self._handle[dut],2,0x23)
            #self._dll.SetPortValue(self._handle[dut],2,0x00)
            #self._dll.SetPortValue(self._handle[dut],2,0x10)
            #self._dll.SetPortValue(self._handle[dut],2,0x00)
            #self._dll.SetPortValue(self._handle[dut],2,0x03)

    @staticmethod
    def instruction(rw,reg):
        instr = [rw, 0, 0] + [int(x) for x in list('{0:05b}'.format(reg))]     
        return instr
    
    def write(self,reg,data,dut=0):
        self._dll.SetAutoCSB(self._handle[dut],0)
        self._dll.SetCtlValue(self._handle[dut],2)
        self._dll.SetPortValue(self._handle[dut],0,0x00)
        instr = self.instruction(0,reg)
        for i in data:
            instr += byte2bits(i)
        #print ' '.join(['%02X' % bits2byte(x) for x in chunks(instr,8)])
        writeDataArry = c_ushort*len(instr)
        writeData = writeDataArry(0)
        for i in range(len(instr)):
            writeData[i] = instr[i]
        writeLen=c_int(2*len(instr))
        self._dll.WriteParallelData(self._handle[dut],byref(writeData),writeLen)
        self._dll.SetAutoCSB(self._handle[dut],1)
        self._dll.SetPortValue(self._handle[dut],0,0x02)
        if reg > 0xD:
            self.update(dut)
    
    def update(self,dut=0):
        self._dll.SetPortValue(self._handle[dut],4,0x90)
        self._dll.SetPortValue(self._handle[dut],4,0x80)
    
    def read(self,reg,dut=0):
        self._dll.SetAutoCSB(self._handle[dut],0)
        self._dll.SetCtlValue(self._handle[dut],2)
        self._dll.SetPortValue(self._handle[dut],0,0x00)
        returnData=[]
        instr = self.instruction(1,reg)
        writeDataArry = c_ushort*8
        writeData = writeDataArry(0)
        for i in range(8):
            writeData[i] = instr[i]
        writeLen=c_int(16)
        readDataArry=c_ubyte*(2*self._regSize[reg])
        readData=readDataArry(0)
        readLen=c_int(2*self._regSize[reg])
        self._dll.WriteParallelData(self._handle[dut],byref(writeData),writeLen)
        self._dll.ReadParallelData(self._handle[dut],byref(readData),readLen)
        returnData = [bits2byte(x) for x in chunks(readData[0:-1:2], 8)]
        print '[%02X]' % reg, ' '.join(['%02X' % x for x in returnData])
        self._dll.SetAutoCSB(self._handle[dut],1)
        self._dll.SetPortValue(self._handle[dut],0,0x02)
        return returnData

    def frequency(self, freq=None, dut=0):
        reg = 0xE
        base = 4294967296.
        if freq == None:
            FTW = self.read(reg,dut)
            FTW = arr2int(FTW[-1:3:-1])
            return (FTW / base) * self._fs
        else:
            FTW = int(base * (freq / float(self._fs)))
            FTW = int2arr(FTW,4)[::-1]
            self.write(reg,[0x08, 0xB5, 0x00, 0x00] + FTW,dut)

if __name__ == '__main__':
    dds=ad9910()
    print(dds.frequency())
    dds.frequency(1e6)
    print(dds.frequency())