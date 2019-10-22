@echo off

rem set CSC="C:\Program Files (x86)\MSBuild\14.0\Bin\csc.exe"
rem %CSC% /target:library AD5372.cs /reference:CyUSB.dll

gacutil.exe /i CyUSB.dll