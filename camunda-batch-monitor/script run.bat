@echo off
setlocal enabledelayedexpansion

:scheduler
for /F "tokens=1,2 delims=:" %%a in ("%time%") do (
    set /A "current_time=%%a*60+%%b"
)

set /A start_process_time=820
set /A end_time=1120

set DAYS_TO_RUN=2,3,4,5,6

set SHOULD_RUN=0

set PYTHON_PATH="C:/Users/ZX/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe"
set SCRIPT_PATH="C:/Users/ZX/Desktop/Batch Monitoring.py"

set START_TIME=14:00

set INTERVAL=10

set END_STRING=Batch Completed!

:: echo %current_time%, %start_process_time%, %end_time%

if %current_time% GEQ %start_process_time% (
	if %current_time% LEQ %end_time% (
	for /f "tokens=1-3 delims=: " %%a in ("%time%") do (
		set HOUR=%%a
		set MINUTE=%%b
	)
	
	for /f "tokens=1 delims= " %%a in ('date /t') do set DayName=%%a
		
	if /i "!DayName!"=="Mon" set DAY=1
	if /i "!DayName!"=="Tue" set DAY=2
	if /i "!DayName!"=="Wed" set DAY=3
	if /i "!DayName!"=="Thu" set DAY=4
	if /i "!DayName!"=="Fri" set DAY=5
	if /i "!DayName!"=="Sat" set DAY=6
	if /i "!DayName!"=="Sun" set DAY=7

	echo Today is !DayName!, the numeric value is !DAY!.

	for %%a in (!DAYS_TO_RUN!) do (
		if "!DAY!"=="%%a" (
			set SHOULD_RUN=1
			goto :RunScript
		)
	)

	if "!SHOULD_RUN!"=="0" (
		echo Today is not a scheduled day to run the script. Exiting...
		exit /b
	)

	:RunScript
	call :RunPythonScript

	:: Loop to run the script periodically
	:Loop
	:: Calculate 30 minutes in seconds
	set /a WAIT_TIME=%INTERVAL%*60
	:: Wait for the specified interval
	echo Checking if it is time to run the script again...
	timeout /t %WAIT_TIME%
	
	:RunPythonScript
	:: Run the Python script and capture its output
	for /f "delims=" %%i in ('"%PYTHON_PATH% %SCRIPT_PATH%"') do set OUTPUT=%%i

	echo Script output: %OUTPUT%

	:: Check if the output matches the termination string
	if "!OUTPUT!"=="%END_STRING%" (
		echo Termination condition met. Exiting...
		goto :END
	) else (
		goto :Loop
	)
	exit /b

	:END
	echo Task finished.
	exit
	)
) else (
    rem If outside the time window, wait for 30 minutes (1800 seconds)
    echo Outside the allowed time window, waiting for 30 minutes...
    timeout /t 1200
)
goto :scheduler