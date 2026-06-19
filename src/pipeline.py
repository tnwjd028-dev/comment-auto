"""음성 파일 1건을 처리하는 전체 파이프라인."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from . import config
from .extract import extract
from .render import render
from .resume import find_resume, first_token, load_resume
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

    # 같은 이름의 이력서가 있으면 함께 사용
    resume = None
    resume_path = find_resume(audio_path)
    if resume_path:
        loaded = load_resume(resume_path)
        if loaded.get("kind") == "unsupported":
            print(
                f"  이력서 {resume_path.name} 형식({loaded['ext']})은 지원하지 않아 "
                f"전화 내용만 사용합니다. (PDF로 변환 권장)"
            )
        else:
            resume = loaded
            print(f"  이력서 함께 사용: {resume_path.name}")
    else:
        print("  (짝이 되는 이력서 없음 — 전화 내용만 사용)")

    print("[2/3] 항목 추출 중 (Gemini)...")
    # 파일명의 첫 단어(보통 이름)를 성명 힌트로 전달
    hint = first_token(audio_path.stem)
    comment = extract(transcript, resume=resume, name_hint=hint)

    # 파일명 첫 단어가 한글 이름 형태면, 성명을 그 값으로 확정한다.
    # (음성 받아쓰기가 이름을 자주 틀리므로, 사용자가 지정한 파일명을 최우선으로 신뢰)
    if re.fullmatch(r"[가-힣]{2,5}", hint) and comment.name != hint:
        print(f"  성명 보정(파일명 기준): {comment.name or '(빈값)'} → {hint}")
        comment.name = hint

    print("[3/3] 문서 생성 중...")
    name = comment.name or stem
    out_path = config.OUTPUT_DIR / f"{name}_후보자코멘트_{ts}.docx"
    render(comment, out_path)

    print(f"완료 → {out_path}")
    return out_path
