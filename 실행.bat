@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   후보자 코멘트 자동 정리
echo   input 폴더의 음성 파일을 처리합니다.
echo ============================================
echo.

if not exist "input\done" mkdir "input\done"

set "count=0"
set "fail=0"
for %%F in (input\*.m4a input\*.mp3 input\*.wav input\*.aac input\*.flac input\*.ogg input\*.mp4) do (
    echo --- 처리 중: %%~nxF ---
    python -m src.run_once "%%F"
    if errorlevel 1 (
        echo    [실패] 이 파일은 input 에 그대로 둡니다. 잠시 후 다시 실행해 주세요.
        set /a fail+=1
    ) else (
        rem 처리 성공: 음성과 같은 이름(첫 단어) 파일들을 done 폴더로 이동
        for /f "tokens=1 delims= " %%T in ("%%~nF") do move /Y "input\%%T*" "input\done\" >nul 2>&1
    )
    set /a count+=1
    echo.
)

if "%count%"=="0" (
    echo [안내] input 폴더에 처리할 음성 파일이 없습니다.
    echo        음성과 이력서를 input 폴더에 넣고 다시 실행하세요.
    echo.
)

echo ============================================
echo   완료! 결과는 output 폴더에서 확인하세요.
echo   처리한 파일은 input\done 폴더로 옮겨졌습니다.
echo ============================================
pause
