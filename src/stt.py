"""로컬 Whisper(faster-whisper)로 음성 파일을 한국어 텍스트로 변환한다.

- 완전 무료, API 키 불필요. 모든 처리가 이 PC에서 일어난다(오프라인).
- 모델 가중치는 '처음 한 번만' 자동 다운로드된다(이후엔 인터넷 불필요).
- 화자분리(누가 말했는지 구분)는 기본 Whisper에 없다. 필요하면 pyannote 등을
  추가로 붙여야 하지만, 추출 단계에서는 전체 전사문만으로도 충분히 동작한다.
"""
from __future__ import annotations

from pathlib import Path

from . import config

# 모델은 무거우므로 한 번만 로드해서 재사용한다.
_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel  # 지연 임포트(설치 전 import 오류 방지)

        print(
            f"  Whisper 모델 로딩 중 (model={config.WHISPER_MODEL}, "
            f"device={config.WHISPER_DEVICE})... 최초 실행 시 다운로드로 시간이 걸립니다."
        )
        _model = WhisperModel(
            config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE_TYPE,
        )
    return _model


def transcribe(audio_path: Path) -> str:
    """음성 파일을 받아 전사 텍스트를 반환한다."""
    model = _get_model()
    segments, _info = model.transcribe(
        str(audio_path),
        language="ko",
        beam_size=5,
        vad_filter=True,  # 무음 구간 제거로 정확도/속도 향상
    )
    # segments 는 제너레이터 — 순회하면서 텍스트를 모은다.
    parts = [seg.text.strip() for seg in segments if seg.text and seg.text.strip()]
    return " ".join(parts).strip()
