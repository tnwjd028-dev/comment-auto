"""환경변수 로딩 및 설정값 모음."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# 프로젝트 루트 (이 파일의 부모의 부모)
ROOT = Path(__file__).resolve().parent.parent

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8")

CLOVA_SPEECH_INVOKE_URL = os.getenv("CLOVA_SPEECH_INVOKE_URL", "")
CLOVA_SPEECH_SECRET = os.getenv("CLOVA_SPEECH_SECRET", "")

INPUT_DIR = (ROOT / os.getenv("INPUT_DIR", "input")).resolve()
OUTPUT_DIR = (ROOT / os.getenv("OUTPUT_DIR", "output")).resolve()

# 처리 대상 오디오 확장자
AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".flac", ".aac", ".ogg", ".mp4"}


def require(name: str, value: str) -> str:
    """필수 환경변수가 비어 있으면 친절한 에러를 낸다."""
    if not value:
        raise RuntimeError(
            f"환경변수 {name} 이(가) 설정되지 않았습니다. "
            f".env 파일을 만들고 값을 채워주세요 (.env.example 참고)."
        )
    return value
