@echo off

rem set CSC="C:\Program Files (x86)\MSBuild\14.0\Bin\csc.exe"
rem %CSC% /target:library AD5372.cs /reference:CyUSB.dll

rem gacutil.exe /i CyUSB.dll

cl /nologo /MD /O2 /c AD5372.cpp
link /dll /NOENTRY /machine:x64 AD5372.obj kernel32.lib user32.lib setupapi.lib /out:AD5372.dll