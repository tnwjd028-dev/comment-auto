"""음성 파일 1건을 처리하는 전체 파이프라인."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from . import config
from .extract import extract
from .render import render
from .stt import transcribe


def process_file(audio_path: Path) -> Path:
    """음성 파일 → 전사 → 추출 → .docx 생성. 결과 파일 경로를 반환한다."""
    print(f"[1/3] 음성 변환 중: {audio_path.name}")
    transcript = transcribe(audio_path)
    if not transcript.strip():
        raise RuntimeError("전사 결과가 비어 있습니다. 음성 파일을 확인해주세요.")

    # 전사문도 참고용으로 같이 저장
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = audio_path.stem
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    (config.OUTPUT_DIR / f"{stem}_{ts}_전사문.txt").write_text(
        transcript, encoding="utf-8"
    )

    print("[2/3] 항목 추출 중 (Claude)...")
    comment = extract(transcript)

    print("[3/3] 문서 생성 중...")
    name = comment.name or stem
    out_path = config.OUTPUT_DIR / f"{name}_후보자코멘트_{ts}.docx"
    render(comment, out_path)

    print(f"완료 → {out_path}")
    return out_path
