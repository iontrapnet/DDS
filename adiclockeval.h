int FindHardware(int* vids, int* pids, int len);
int GetHardwareCount();
int GetHardwareHandles(int* handles)
int GetHardwareInstance(int handle, char* instance);
int GetVendorID(int handle);
int GetProductID(int handle);
int GetFirmwareVersion(int handle, int* major, int* minor);
int GetUsbSpeed(int handle);
int IsConnected(int handle);
int GetLedBlink(int handle);
int SetLedBlink(int handle, int value);
int Reset(int handle);
int SpiRead(int handle, int* wdata, int wlen, int* rdata, int rlen, int fourwire);
int SpiWrite(int handle, int* wdata, int wlen);                           
int GetSpiInstruction(int rw, int address, int datalen, char* instr, int instrlen);
int GetPortConfig(int handle, int port, char* config);
int SetPortConfig(int handle, int port, char config);
int GetPortValue(int handle, int port, char* value);
int SetPortValue(int handle, int port, char value);
int GetCtlValue(int handle, char* value);
int SetCtlValue(int handle, char value);
int GetHostID(int handle, int* value);
int SetHostID(int handle, int value);
int GetSPIConfig(int handle, char* value);
int SetSPIConfig(int handle, char value);
int GetEvbdInfo(int handle, char* boardinfo, int* length);
int GetClkConfig(int handle, char* value);
int SetClkConfig(int handle, char value);
int DownloadFirmware(int handle, const char* hexfilepath);
int SetAutoCSB(int handle, char value);
int SetCSBMask(int handle, char value);
int WriteParallelData(int handle, const char* data, int len);
int ReadParallelData(int handle, char* data, int len);
int WriteReadParallelData(int handle, const char* wdata, int wlen, char* rdata, int rlen);