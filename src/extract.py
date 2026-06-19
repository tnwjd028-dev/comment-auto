"""전사 텍스트를 Google Gemini로 분석해 후보자 코멘트 양식 항목을 추출한다.

Gemini 무료 티어 + 구조화 출력(response_schema)을 사용한다.
"""
from __future__ import annotations

import json
from typing import List

from pydantic import BaseModel, Field

from . import config


class JobHistory(BaseModel):
    """재직 기업별 경력 + 이직 사유."""
    company: str = Field(description="회사명")
    period: str = Field(description="재직 기간 (예: '1년 2개월'). 불명확하면 빈 문자열")
    work: str = Field(description="해당 기업에서 수행한 업무 요약")
    reason: str = Field(description="이직(퇴사) 사유")


class CandidateComment(BaseModel):
    """후보자 코멘트 양식의 전체 항목."""
    job_title: str = Field(description="지원/희망 직무명 (예: '백엔드 개발자'). 모르면 빈 문자열")
    name: str = Field(description="후보자 성명. 언급 없으면 빈 문자열")
    career: str = Field(description="총 경력 (예: '7년 10개월'). 모르면 빈 문자열")
    current_salary: str = Field(description="현재 연봉 (예: '4,500만원'). 모르면 빈 문자열")
    desired_salary: str = Field(description="희망 연봉 (예: '5,000만원'). 모르면 빈 문자열")
    skills: List[str] = Field(description="보유 기술 스택 목록")
    summary: str = Field(description="주요 수행 업무/경험 요약 ([내용] 영역). 2~4문장")
    desired_role: str = Field(description="희망하는 직무/포지션 또는 입사 후 하고 싶은 일")
    job_seeking_status: str = Field(
        description="현재 구직 상태와 입사 가능 시기 ([상황] 영역). 면접 가능일 등 포함"
    )
    histories: List[JobHistory] = Field(description="재직했던 기업별 경력과 이직 사유")


SYSTEM_PROMPT = """당신은 채용 담당자를 돕는 어시스턴트입니다.
후보자와의 전화 면접 녹음 전사문을 읽고, '후보자 코멘트' 양식 항목을 정확히 추출합니다.

규칙:
- 전사문에 실제로 언급된 내용만 사용하세요. 추측하거나 지어내지 마세요.
- 정보가 없는 항목은 빈 문자열("") 또는 빈 목록([])으로 두세요.
- 연봉/기간/숫자는 전사문에 나온 그대로 표기하되, 자연스러운 한국어 단위로 정리하세요
  (예: "사천오백" → "4,500만원").
- summary와 job_seeking_status는 채용 담당자가 바로 읽을 수 있는 간결한 문장으로 정리하세요."""


def extract(transcript: str) -> CandidateComment:
    """전사문 → 구조화된 코멘트 항목."""
    from google import genai  # 지연 임포트

    config.require("GEMINI_API_KEY", config.GEMINI_API_KEY)
    client = genai.Client(api_key=config.GEMINI_API_KEY)

    user_text = (
        "다음은 후보자 전화 면접 녹음의 전사문입니다. 양식 항목을 추출해 주세요.\n\n"
        "=== 전사문 시작 ===\n"
        f"{transcript}\n"
        "=== 전사문 끝 ==="
    )

    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=user_text,
        config={
            "system_instruction": SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "response_schema": CandidateComment,
        },
    )

    # google-genai는 response_schema가 pydantic이면 .parsed에 인스턴스를 채워준다.
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, CandidateComment):
        return parsed

    # 안전장치: 텍스트(JSON)를 직접 검증
    if response.text:
        return CandidateComment.model_validate(json.loads(response.text))

    raise RuntimeError("Gemini가 구조화된 결과를 반환하지 못했습니다.")
