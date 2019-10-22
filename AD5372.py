from ctypes import *
from array import array

HEX_PATH="AD537xSPI.hex"
DLL_PATH="ADI_CYUSB_USB4.dll"

class ad5372:
    """ Class to control the AD537x EVAL board. """

    def __init__(self, vid=0x0456, pid=0xB20F):
        self.dll = windll.LoadLibrary(DLL_PATH)
        self.VID = vid
        self.PID = pid
        self.handle = c_uint(0)
        self.hexfile = array('B', HEX_PATH)
        self.hexfile.append(0)
        if not self.Connect_to_Board():
            print("Connected to board...")
            print("Writing offset values")
            self.Write_SPI_Word('022000') #Write offset values to get +- 10V span
            self.Pulse_LDAC()
            self.Write_SPI_Word('032000') #Write offset values to get +- 10V span
            self.Pulse_LDAC()
            for i in range(0,32):
                self.Write_Voltage(0,i) # Zero all channels
            self.Pulse_LDAC()
            print("done. Ready to use.")
        else:
            print("Could not connect to board, please check your settings.")



    def Connect_to_Board(self, num_boards=1):
        """ Finds the EVAL board, connects to it and uploads the SPI firmware."""

        part_path = create_string_buffer("", 8)
        c_vid = c_uint(self.VID)
        c_pid = c_uint(self.PID)
        num = c_uint(num_boards)

        ret_search = self.dll.Search_For_Boards(c_vid, c_pid, byref(num), byref(part_path))
        new_path = repr(part_path.value)[3:5] # get first value, since there is only one board
        print(new_path)
        path = c_byte(int(new_path))
        ret_conn = self.dll.Connect(c_vid, c_pid, path, byref(self.handle))
        print(ret_conn)
        arr = (c_int8*len(self.hexfile))(*self.hexfile)
        ret_firm = self.dll.Download_Firmware(self.handle, arr)
        ret_init = self.Initialize()
        if ret_search != 0 or ret_conn != 0 or ret_firm != 0 or ret_init != 1:
            return 1
        else:
            return 0

    def Write_Voltage(self, Vtarget, channel):
        """ Takes a target voltage and channel and converts it to the correct hex word
        to write to the SPI. """
        index = self.channel_to_hex(channel)
        value = self.voltage_to_hex(Vtarget)
        word = index+value
        return self.Write_SPI_Word(word)

    def Write_SPI_Word(self, word):
        """ Write SPI word by calling the Vendor_Request DLL call. Takes a hexadecimal word
        and splits to different value and index parameters.
        Function prototype: Int Vendor_Request(UInt  Handle, UChar Request, UShort Value, UShort Index,
                            UChar Direction, UShort DataLength, UChar *Buffer[]);
        """
        c_req = c_byte(0xDD)
        value = int(word[2:6], 16)
        index = int(word[0:2], 16)
        c_index = c_short(index)
        c_value = c_short(value)
        c_zero = c_short(0)
        c_direction = c_char('0')
        c_buffer = create_string_buffer("",0)
        ret = self.dll.Vendor_Request(self.handle, c_req, c_value, c_index, c_direction, c_zero, byref(c_buffer))
        return ret

    def Pulse_LDAC(self):
        """ Pulse LDAC. """
        c_req = c_byte(0xDE)
        c_zero = c_short(0)
        c_buffer = create_string_buffer("",0)
        c_direction = c_char('0')
        ret = self.dll.Vendor_Request(self.handle, c_req, c_zero, c_zero, c_direction, c_zero, byref(c_buffer))
        return ret

    def Initialize(self):
        """ Call Initialize function after the firmware has been downloaded.
        Thanks dpersechini for pointing this out. """
        c_req = c_byte(0xE0)
        c_zero = c_short(0)
        c_direction = c_char('0')
        c_buffer = create_string_buffer("",0)
        ret = self.dll.Vendor_Request(self.handle, c_req, c_zero, c_zero, c_direction, c_zero, byref(c_buffer))
        return ret


    def voltage_to_hex(self, Vtarget, Vmax=10, Vmin=-10):
        """ Takes target voltage and returns the hexadecimal value for the DAC.
        Default values span from Vmax = 10, Vmin = -10."""
        Vtarget = float(Vtarget)
        Voffset = (Vmax-Vmin)/2
        x = ((Vtarget+Voffset)/(Vmax-Vmin))*65535
        return format(int(round(x)), '04x')

    def num_to_binary(self, num, width=3):
        """ Returns binary string of fixed width from an integer. Default width is 3. """
        bin_code = int("{0:b}".format(num))
        return format(bin_code, '0%dd'%width)

    def channel_to_hex(self, channel):
        group, channel = divmod(channel, 8)
        group+=1
        group = self.num_to_binary(group)
        channel = self.num_to_binary(channel)
        register = '11' # Write to X register
        word = register+group+channel
        return format(int(word, 2), '02x')

    def kill(self):
        return self.dll.Disconnect(self.handle)

# Testing
if __name__ == '__main__':
    dac = ad5372()
    dac.Write_Voltage(5,3) # target voltage, channel
    print(dac.Write_Voltage(6,4))
    dac.Write_Voltage(7,5)
    dac.Write_Voltage(8,6)
    dac.Write_Voltage(9,7)
    dac.Pulse_LDAC()
    print(dac.Write_SPI_Word('C80000')) #Channel 0 = -10V
    print(dac.Pulse_LDAC())
    #print dac.Write_SPI_Word('C9FFFF')
    #print dac.Pulse_LDAC()
    dac.Write_Voltage(1,0)
    dac.Pulse_LDAC()
    dac.kill()
