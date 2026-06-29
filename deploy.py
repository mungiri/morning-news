# -*- coding: utf-8 -*-
"""
원클릭 배포 스크립트 (체이닝용)
- index.html 재빌드 → git add/commit/push
- 아침 뉴스 작업 맨 끝에 `python deploy.py` 한 줄만 추가하면,
  새 md 생성 직후 사이트가 자동으로 갱신·배포된다(Vercel이 push를 감지).
- 변경이 없으면 커밋/푸시를 건너뛴다.
"""
import subprocess
import sys
from datetime import date
from pathlib import Path

from generate import build  # generate.py 의 빌드 함수 재사용

BASE = Path(__file__).resolve().parent

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=BASE, check=check,
                          capture_output=True, text=True, encoding="utf-8")


def main():
    # 1) index.html 재빌드
    if build() != 0:
        print("⚠️  빌드 실패 — 배포 중단")
        return 1

    # 2) 변경사항 스테이징
    git("add", "-A")

    # 3) 변경 없으면 종료
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        print("ℹ️  변경된 내용이 없어 배포를 건너뜁니다.")
        return 0

    # 4) 커밋 & 푸시
    today = date.today().isoformat()
    git("commit", "-m", f"뉴스 {today}")
    push = git("push", check=False)
    if push.returncode != 0:
        print("⚠️  push 실패:\n" + (push.stderr or push.stdout))
        return 1

    print(f"🚀 배포 완료 — {today} 스크랩을 푸시했습니다. Vercel이 곧 반영합니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
