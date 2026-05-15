@echo off
chcp 65001 >nul
set KEY=C:\Users\老王\.ssh\id_ed25519
set HOST=ubuntu@119.91.156.46

echo [0/6] 预检免密连接...
ssh -i "%KEY%" %HOST% "echo connected"
if errorlevel 1 goto fail

echo [1/6] 上传到临时目录...
scp -i "%KEY%" "D:\桌面\毕业设计\backend\app\services\doubao_client.py" %HOST%:/home/ubuntu/doubao_client.py
if errorlevel 1 goto fail
scp -i "%KEY%" "D:\桌面\毕业设计\backend\app\services\ai_service.py" %HOST%:/home/ubuntu/ai_service.py
if errorlevel 1 goto fail

echo [2/6] 覆盖到项目目录并修权限...
ssh -i "%KEY%" %HOST% "sudo cp /home/ubuntu/doubao_client.py /home/ubuntu/backend/app/services/doubao_client.py && sudo cp /home/ubuntu/ai_service.py /home/ubuntu/backend/app/services/ai_service.py && sudo chown ubuntu:ubuntu /home/ubuntu/backend/app/services/doubao_client.py /home/ubuntu/backend/app/services/ai_service.py"
if errorlevel 1 goto fail

echo [3/6] 重启服务...
ssh -i "%KEY%" %HOST% "sudo systemctl restart heritage-api"
if errorlevel 1 goto fail

echo [4/6] 查看服务状态...
ssh -i "%KEY%" %HOST% "sudo systemctl status heritage-api --no-pager"
if errorlevel 1 goto fail

echo [5/6] 接口自检...
ssh -i "%KEY%" %HOST% "curl -s -X POST http://127.0.0.1:8010/api/v1/ai/chat -H 'Content-Type: application/json' -d '{\"question\":\"中国非遗保护经历了哪些重要阶段？\",\"user_id\":9}'"

echo.
echo ===== 部署完成 =====
pause
exit /b 0

:fail
echo.
echo !!!!! 部署失败，请看上方报错 !!!!!
pause
exit /b 1