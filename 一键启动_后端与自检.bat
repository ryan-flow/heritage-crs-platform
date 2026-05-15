@echo off

chcp 65001 >nul

setlocal EnableExtensions EnableDelayedExpansion



set "ROOT=D:\桌面\毕业设计"

set "BACKEND_DIR=%ROOT%\backend"

set "APP_JS=%ROOT%\frontend\miniprogram\app.js"

set "API_PORT=8000"

set "API_PREFIX=/api/v1"

set "PYTHON_EXE=C:\Users\老王\AppData\Local\Programs\Python\Python311\python.exe"



echo ==========================================

echo 非遗平台一键启动（后端 + 自检 + 管理端）

echo ==========================================

echo.



if not exist "%BACKEND_DIR%" (

  echo [错误] 后端目录不存在: %BACKEND_DIR%

  pause

  exit /b 1

)



if not exist "%APP_JS%" (

  echo [错误] 小程序 app.js 不存在: %APP_JS%

  pause

  exit /b 1

)



if not exist "%PYTHON_EXE%" (

  echo [错误] Python 路径不存在: %PYTHON_EXE%

  echo 请修改本脚本中的 PYTHON_EXE 为你本机 python.exe 的实际路径。

  pause

  exit /b 1

)



set "LOCAL_IP=127.0.0.1"

for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$ips=Get-NetIPAddress -AddressFamily IPv4; foreach($x in $ips){$ip=$x.IPAddress; if($ip -like '192.168.*' -or $ip -like '10.*' -or $ip -match '^172\.(1[6-9]|2[0-9]|3[0-1])\.'){Write-Output $ip; break}}"`) do set "LOCAL_IP=%%I"

if "%LOCAL_IP%"=="" set "LOCAL_IP=127.0.0.1"



set "API_BASE=http://%LOCAL_IP%:%API_PORT%%API_PREFIX%"



echo [1/6] 当前局域网IP: %LOCAL_IP%

echo [1/6] 目标 API Base: %API_BASE%

echo.



echo [2/6] 当前脚本不改写小程序 app.js，避免入口文件被覆盖。

echo [2/6] 真机调试请确保 app.js 中 API 地址与当前局域网 IP 一致。

echo.



echo [3/6] 检查 Python 依赖...

"%PYTHON_EXE%" -c "import fastapi, uvicorn, sqlalchemy, pydantic_settings" 1>nul 2>nul

if errorlevel 1 (

  echo 检测到依赖缺失，正在安装 backend\requirements.txt...

  "%PYTHON_EXE%" -m pip install -r "%BACKEND_DIR%\requirements.txt"

  if errorlevel 1 (

    echo [错误] 依赖安装失败。

    pause

    exit /b 1

  )

)



echo [4/6] 检查后端是否已经运行...

powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:%API_PORT%/' -TimeoutSec 2; if($r.StatusCode -eq 200){ exit 0 } else { exit 1 } } catch { exit 1 }" 1>nul 2>nul

if errorlevel 1 (

  echo 后端未运行，正在启动新窗口...

  start "Heritage Backend API" /D "%BACKEND_DIR%" "%ComSpec%" /k ""%PYTHON_EXE%" -m uvicorn app.main:app --host 0.0.0.0 --port %API_PORT% --reload"

) else (

  echo 后端已在运行，跳过重复启动。

)



echo.

echo [5/6] 等待服务启动并执行自检...

set "HEALTH_OK="

for /l %%N in (1,1,30) do (

  powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:%API_PORT%/' -TimeoutSec 2; if($r.StatusCode -eq 200){ exit 0 } else { exit 1 } } catch { exit 1 }" 1>nul 2>nul

  if not errorlevel 1 (

    set "HEALTH_OK=1"

    goto :health_done

  )

  timeout /t 1 >nul

)



:health_done

if "%HEALTH_OK%"=="" (

  echo [错误] 后端启动超时。

  echo 请查看新打开的 "Heritage Backend API" 窗口日志。

  echo 常见原因：8000 端口被占用、依赖未安装、数据库文件被占用。

  pause

  exit /b 1

)



echo 根路径检查: PASS



powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:%API_PORT%/admin-web' -TimeoutSec 4; if($r.StatusCode -eq 200){ '管理Web检查: PASS' } else { '管理Web检查: FAIL' } } catch { '管理Web检查: FAIL' }"



echo.

echo [6/6] 打开后台管理 Web...

start "" "http://127.0.0.1:%API_PORT%/admin-web"



echo.

echo ==========================================

echo 启动完成！

echo 后端地址: http://127.0.0.1:%API_PORT%

echo 局域网地址: http://%LOCAL_IP%:%API_PORT%

echo 小程序 API: %API_BASE%

echo 后端窗口: Heritage Backend API

echo ==========================================

echo.

pause

exit /b 0

