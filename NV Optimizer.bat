@echo off
title NV Optimizer 2.0
color 0B

:: Verificar administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ============================================
    echo   AVISO: Execute como Administrador
    echo   Algumas otimizacoes podem nao funcionar
    echo   sem privilegios elevados.
    echo.
    echo   Solicitando privilegios de administrador...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Verifica Python
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo  Python nao encontrado no PATH.
    echo  Instale Python 3.8+ e tente novamente.
    pause
    exit /b 1
)

:: Inicia a interface grafica (NV Optimizer 2.0)
cd /d "%~dp0"
start "" python main.py

exit /b