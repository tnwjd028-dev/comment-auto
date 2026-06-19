"""Naver CLOVA Speech 로 음성 파일을 한국어 텍스트로 변환한다.

CLOVA Speech(롱 센텐스) 업로드 API를 사용한다.
- 미디어 파일을 multipart 로 업로드하고 동기(sync)로 결과를 받는다.
- 화자분리(diarization)를 켜서, 가능하면 "화자별" 대화 형태의 전사문을 만든다.
  (전화 면접처럼 면접관/후보자가 나뉘면 추출 정확도가 올라간다.)

참고: 매우 긴 음성(수십 분 이상)은 sync 응답이 타임아웃될 수 있다.
그 경우 completion=async + callback 방식으로 바꿔야 한다(README 참고).
"""
from __future__ import annotations

import json
from pathlib import Path

import requests

from . import config


def transcribe(audio_path: Path, timeout: int = 600) -> str:
    """음성 파일을 받아 전사 텍스트(화자분리되면 화자 라벨 포함)를 반환한다."""
    invoke_url = config.require("CLOVA_SPEECH_INVOKE_URL", config.CLOVA_SPEECH_INVOKE_URL)
    secret = config.require("CLOVA_SPEECH_SECRET", config.CLOVA_SPEECH_SECRET)

    url = invoke_url.rstrip("/") + "/recognizer/upload"
    params = {
        "language": "ko-KR",
        "completion": "sync",
        "wordAlignment": True,
        "fullText": True,
        "diarization": {"enable": True},  # 화자분리
    }
    headers = {"X-CLOVASPEECH-API-KEY": secret}

    with audio_path.open("rb") as f:
        files = {
            "media": (audio_path.name, f, "application/octet-stream"),
            "params": (None, json.dumps(params), "application/json"),
        }
        resp = requests.post(url, headers=headers, files=files, timeout=timeout)

    if resp.status_code != 200:
        raise RuntimeError(
            f"CLOVA Speech 오류 ({resp.status_code}): {resp.text[:500]}"
        )

    data = resp.json()
    return _build_transcript(data)


def _build_transcript(data: dict) -> str:
    """API 응답에서 화자 라벨이 붙은 전사문을 만든다. 없으면 fullText 사용."""
    segments = data.get("segments") or []
    lines: list[str] = []
    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        speaker = (seg.get("speaker") or {}).get("label")
        if speaker:
            lines.append(f"화자{speaker}: {text}")
        else:
            lines.append(text)

    if lines:
        return "\n".join(lines)

    # 화자 세그먼트가 없으면 전체 텍스트 반환
    return (data.get("text") or "").strip()
