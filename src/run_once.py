"""음성 파일 1건을 즉시 처리한다(폴더 감시 없이 테스트용).

실행:  python -m src.run_once "input/면접녹음.m4a"
"""
from __future__ import annotations

import sys
from pathlib import Path

from .pipeline import process_file


def main() -> None:
    if len(sys.argv) < 2:
        print('사용법: python -m src.run_once "경로/파일.m4a"')
        raise SystemExit(1)
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"파일을 찾을 수 없습니다: {path}")
        raise SystemExit(1)
    process_file(path)


if __name__ == "__main__":
    main()
