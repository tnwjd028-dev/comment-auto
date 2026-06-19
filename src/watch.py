"""input/ 폴더를 감시하다가 새 음성 파일이 들어오면 자동 처리한다.

실행:  python -m src.watch
종료:  Ctrl + C
"""
from __future__ import annotations

import time
import traceback
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from . import config
from .pipeline import process_file


def _is_stable(path: Path, checks: int = 3, interval: float = 1.0) -> bool:
    """파일 크기가 더 이상 변하지 않을 때까지 기다린다(업로드/복사 완료 확인)."""
    last = -1
    stable = 0
    for _ in range(60):  # 최대 60초 대기
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            return False
        if size == last and size > 0:
            stable += 1
            if stable >= checks:
                return True
        else:
            stable = 0
            last = size
        time.sleep(interval)
    return False


class AudioHandler(FileSystemEventHandler):
    def __init__(self) -> None:
        self._seen: set[str] = set()

    def on_created(self, event):
        self._maybe_process(event)

    def on_moved(self, event):
        # 일부 OS는 임시 파일로 받았다가 이름을 바꾼다
        self._maybe_process(event, attr="dest_path")

    def _maybe_process(self, event, attr: str = "src_path") -> None:
        if event.is_directory:
            return
        path = Path(getattr(event, attr))
        if path.suffix.lower() not in config.AUDIO_EXTS:
            return
        key = str(path)
        if key in self._seen:
            return
        self._seen.add(key)

        print(f"\n새 파일 감지: {path.name}")
        if not _is_stable(path):
            print("  파일이 안정화되지 않아 건너뜁니다.")
            self._seen.discard(key)
            return
        try:
            process_file(path)
        except Exception:  # 한 건 실패해도 감시는 계속
            print("  처리 중 오류 발생:")
            traceback.print_exc()


def main() -> None:
    config.INPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"감시 시작: {config.INPUT_DIR}")
    print(f"결과 저장: {config.OUTPUT_DIR}")
    print("음성 파일을 input/ 폴더에 넣으면 자동으로 처리합니다. (종료: Ctrl+C)\n")

    handler = AudioHandler()
    observer = Observer()
    observer.schedule(handler, str(config.INPUT_DIR), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n감시를 종료합니다.")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
