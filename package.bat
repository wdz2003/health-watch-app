@echo off
REM 健康监测手表APP - 打包脚本
REM 请先修改下面的环境变量路径

echo ====================================
echo   健康监测手表APP打包脚本
echo ====================================
echo.

REM 设置环境变量（请根据实际情况修改）
REM ============================================
REM 请修改以下路径为您的实际路径
REM ============================================

REM 设置 Android SDK 路径
set ANDROID_HOME=C:\Users\35911\AppData\Local\Android\Sdk

REM 设置 Android NDK 路径
set ANDROID_NDK_HOME=C:\Users\35911\AppData\Local\Android\Sdk\ndk\25.1.8937393

REM 设置 JDK 路径
set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.18.8-hotspot

REM 设置 PATH
set PATH=%ANDROID_HOME%\platform-tools;%ANDROID_HOME%\tools;%ANDROID_HOME%\build-tools\34.0.0;%JAVA_HOME%\bin;%PATH%

echo [1/5] 环境变量配置：
echo   Android SDK: %ANDROID_HOME%
echo   Android NDK: %ANDROID_NDK_HOME%
echo   Java Home:   %JAVA_HOME%
echo.

REM 检查Python环境
echo [2/5] 检查Python环境...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)
echo.

REM 检查buildozer
echo [3/5] 检查buildozer...
buildozer --version
if %ERRORLEVEL% NEQ 0 (
    echo [提示] 未找到buildozer，正在安装...
    pip install buildozer
    if %ERRORLEVEL% NEQ 0 (
        echo [错误] buildozer安装失败
        pause
        exit /b 1
    )
)
echo.

REM 进入apk_package目录
cd /d "%~dp0apk_package"

echo [4/5] 开始打包...
echo   这可能需要30-60分钟，请耐心等待...
echo.

REM 开始打包
buildozer android debug

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ====================================
    echo [5/5] 打包完成！
    echo ====================================
    echo.
    echo APK文件位置:
    dir /b bin\*.apk 2>nul
    echo.
    echo 请将APK文件传输到手机安装
    echo.
) else (
    echo.
    echo [错误] 打包失败，请检查错误信息
    echo.
)

pause
