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
후보자의 '이력서'(있을 경우)와 '전화 면접 녹음 전사문'을 함께 읽고,
'후보자 코멘트' 양식 항목을 정확히 작성합니다.

자료 활용 원칙:
- 이력서가 함께 제공되면: 객관적 사실(성명, 기술스택, 회사명, 재직기간, 총 경력,
  연봉, 직무 등)은 이력서를 우선 근거로 삼으세요.
- 전화 전사문: 후보자의 이직 사유, 구직 상황, 입사 가능 시기, 희망 직무·연봉 등
  '의향과 상황'을 보완하는 데 사용하세요.
- 두 자료가 충돌하면 객관적 사실은 이력서를 따르되, 통화에서 갱신·확정된 정보
  (예: 변경된 희망 연봉, 면접 가능일)는 통화를 우선합니다.

성명(name) 작성 시 특히 주의:
- 음성 받아쓰기는 한국어 사람 이름을 자주 틀리게 인식합니다 (예: '정주원'을 '정주호'로).
- 따라서 성명은 ① 이력서 → ② 제공된 파일명 힌트 순으로 우선하고,
  전화 전사문의 이름은 가장 신뢰도가 낮은 근거로 취급하세요.
- 이력서나 파일명 힌트의 이름과 전사문의 이름이 다르면, 이력서/파일명을 따르세요.
- 파일명 힌트가 사람 이름이 아니면(예: '면접녹음1') 무시하세요.

작성 규칙:
- 두 자료에 실제로 있는 내용만 사용하세요. 추측하거나 지어내지 마세요.
- 정보가 없는 항목은 빈 문자열("") 또는 빈 목록([])으로 두세요.
- 연봉/숫자는 자연스러운 한국어 단위로 정리하세요 (예: "사천오백" → "4,500만원").
- 기간(period)은 깔끔한 형태로 정리하세요 (예: "4년 좀 안 됨" → "약 4년",
  "1년2개월" → "1년 2개월").
- career(총 경력)는 이력서/통화에 명시가 있으면 그대로, 없으면 회사별 재직기간을
  합산해 "약 N년 M개월" 형태로 채우세요.

⭐ 분량은 '간결하게' — 채용 담당자가 빠르게 훑는 짧은 코멘트입니다:
- skills(기술스택)는 전부 나열하지 말고, 대표 핵심 기술 8~12개 이내로만 추리세요.
- summary는 2~3문장 이내로 핵심만.
- job_seeking_status는 1~2문장 이내로.
- 각 회사의 work(수행업무)는 한 문장으로 요약하고, reason(이직사유)도 한 문장으로
  간결하게 쓰세요. 업무를 길게 나열하지 마세요."""


def extract(
    transcript: str,
    resume: dict | None = None,
    name_hint: str | None = None,
) -> CandidateComment:
    """전사문(+선택적 이력서, 파일명 힌트) → 구조화된 코멘트 항목.

    resume:    resume.load_resume() 가 돌려준 dict 또는 None.
    name_hint: 음성 파일명(성명 추정 보조용) 또는 None.
    """
    from google import genai  # 지연 임포트
    from google.genai import errors as genai_errors
    from google.genai import types

    config.require("GEMINI_API_KEY", config.GEMINI_API_KEY)
    client = genai.Client(api_key=config.GEMINI_API_KEY)

    # Gemini 입력(contents) 조립: 안내 → (이력서) → 전사문
    contents: list = [
        "후보자의 자료를 바탕으로 '후보자 코멘트' 양식 항목을 작성해 주세요."
    ]

    if name_hint:
        contents.append(
            f"참고용 파일명: '{name_hint}'. "
            f"이것이 사람 이름이면 성명(name) 근거로 우선 사용하세요."
        )

    if resume and resume.get("kind") == "text" and resume.get("text", "").strip():
        contents.append(
            "=== 이력서(텍스트) 시작 ===\n" + resume["text"] + "\n=== 이력서 끝 ==="
        )
    elif resume and resume.get("kind") == "file":
        contents.append("아래 첨부된 이력서 파일을 먼저 참고하세요.")
        contents.append(
            types.Part.from_bytes(data=resume["data"], mime_type=resume["mime"])
        )

    contents.append(
        "=== 전화 면접 전사문 시작 ===\n" + transcript + "\n=== 전사문 끝 ==="
    )

    # 서버 혼잡(503)·요청 과다(429) 등 일시적 오류는 잠시 대기 후 재시도한다.
    import time

    response = None
    last_err: Exception | None = None
    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=contents,
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "response_mime_type": "application/json",
                    "response_schema": CandidateComment,
                },
            )
            break
        except genai_errors.APIError as e:
            code = getattr(e, "code", None)
            if code in (429, 500, 502, 503, 504) and attempt < 4:
                wait = 5 * (attempt + 1)  # 5, 10, 15, 20초
                print(f"  서버 혼잡(코드 {code}) — {wait}초 후 재시도 ({attempt + 1}/5)...")
                time.sleep(wait)
                last_err = e
                continue
            raise
    if response is None:
        raise RuntimeError(
            "Gemini 서버가 계속 혼잡합니다. 잠시 후(몇 분 뒤) 다시 실행해 주세요."
        ) from last_err

    # google-genai는 response_schema가 pydantic이면 .parsed에 인스턴스를 채워준다.
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, CandidateComment):
        return parsed

    # 안전장치: 텍스트(JSON)를 직접 검증
    if response.text:
        return CandidateComment.model_validate(json.loads(response.text))

    raise RuntimeError("Gemini가 구조화된 결과를 반환하지 못했습니다.")
