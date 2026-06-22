@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   후보자 코멘트 자동 정리
echo   input 폴더의 음성 파일을 처리합니다.
echo ============================================
echo.

set "count=0"
for %%F in (input\*.m4a input\*.mp3 input\*.wav input\*.aac input\*.flac input\*.ogg input\*.mp4) do (
    echo --- 처리 중: %%~nxF ---
    python -m src.run_once "%%F"
    set /a count+=1
    echo.
)

if "%count%"=="0" (
    echo [안내] input 폴더에 음성 파일이 없습니다.
    echo        음성과 이력서를 input 폴더에 넣고 다시 실행하세요.
    echo.
)

echo ============================================
echo   완료! 결과는 output 폴더를 확인하세요.
echo ============================================
pause
