@echo off set PYTHON=C:\python27\python.exe
@echo off set IMPL=%1

%PYTHON% autotest.py %IMPL%
%PYTHON% buffertest.py %IMPL%
%PYTHON% commtest.py %IMPL%
%PYTHON% guardtest.py %IMPL%
%PYTHON% iotest.py %IMPL%
%PYTHON% poisontest.py %IMPL%
%PYTHON% selecttest.py %IMPL%
cd windows
%PYTHON% remotetest.py %IMPL%
