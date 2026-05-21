@echo off
echo ========================================
echo   青商企业诊断 H5 - 启动服务
echo ========================================
echo.
echo 安装依赖...
pip install -r requirements.txt
echo.
echo 启动服务 http://localhost:5000
echo.
python server.py
pause
