# -*- coding: utf-8 -*-
"""
원클릭 배포 스크립트 (체이닝용)
- index.html 재빌드 → git add/commit/push
- 아침 뉴스 작업 맨 끝에 `python deploy.py` 한 줄만 추가하면,
  새 md 생성 직후 사이트가 자동으로 갱신·배포된다(Vercel이 push를 감지).
- 변경이 없으면 커밋/푸시를 건너뛴다.
"""
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from generate import build  # generate.py 의 빌드 함수 재사용
import cards

BASE = Path(__file__).resolve().parent
KST = timezone(timedelta(hours=9))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=BASE, check=check,
                          capture_output=True, text=True, encoding="utf-8")


def clear_stale_locks():
    """이전 실행이 중간에 끊기면 .git 안에 *.lock 파일이 남아 다음 git 작업을 막는다.
    이 폴더 마운트는 파일 삭제(unlink)가 막혀 있으므로, 삭제 대신 rename(os.replace)으로
    잠금 파일을 .stale 로 치워 자동 복구한다. (스케줄 작업은 단독 실행이라 안전)"""
    git_dir = BASE / ".git"
    if not git_dir.is_dir():
        return
    for lock in git_dir.rglob("*.lock"):
        try:
            os.replace(lock, lock.with_suffix(lock.suffix + ".stale"))
            print(f"🔓 남은 잠금 파일 정리: {lock.relative_to(BASE)}")
        except OSError as e:
            print(f"⚠️  잠금 파일 정리 실패({lock.name}): {e}")


def main():
    # 0) 이전 실행 잔여 잠금 파일 자동 정리
    clear_stale_locks()

    # 1) index.html / mobile.html 재빌드
    if build() != 0:
        print("⚠️  빌드 실패 — 배포 중단")
        return 1

    # 1-1) 인스타 카드뉴스 이미지 생성
    today = datetime.now(KST).date().isoformat()
    cards.build(today)

    # 2) 변경사항 스테이징
    git("add", "-A")

    # 3) 변경 없으면 종료 (카드/사이트 둘 다 이미 최신)
    no_changes = git("diff", "--cached", "--quiet", check=False).returncode == 0
    if no_changes:
        print("ℹ️  변경된 내용이 없어 배포를 건너뜁니다.")
    else:
        # 4) 커밋 & 푸시 (날짜는 항상 한국시간 기준)
        git("commit", "-m", f"뉴스 {today}")
        push = git("push", check=False)
        if push.returncode != 0:
            print("⚠️  push 실패:\n" + (push.stderr or push.stdout))
            return 1
        print(f"🚀 배포 완료 — {today} 스크랩을 푸시했습니다. Vercel이 곧 반영합니다.")

    # 5) 인스타 게시 — Vercel 반영 대기(수 분 소요) 때문에 deploy.py 안에서 기다리지 않고
    #    완전히 분리된 백그라운드 프로세스로 던져둔다. 호출한 쪽(스케줄 작업 등)이
    #    빨리 끝나야 해서 타임아웃에 걸리더라도, 이 프로세스는 알아서 끝까지 진행된다.
    log_path = BASE / "cards" / today / "instagram_post.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as logf:
        subprocess.Popen(
            [sys.executable, str(BASE / "instagram_post.py"), today],
            cwd=BASE, stdout=logf, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, start_new_session=True,
        )
    print(f"🕊️  인스타 게시는 백그라운드로 넘겼습니다 (로그: {log_path.relative_to(BASE)})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
