# -*- coding: utf-8 -*-
"""
cards/<date>/*.png (Vercel에 이미 배포된 공개 URL)로 인스타 캐러셀 게시물을 만든다.
- 하루에 한 번만 게시되도록 cards/<date>/.posted 마커로 중복 방지.
- 실행: python instagram_post.py [YYYY-MM-DD]  (생략 시 최신 날짜)
"""
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent
CARDS_DIR = BASE / "cards"
ENV_PATH = BASE / ".env"
SITE_BASE = "https://morning-news-black.vercel.app"
GRAPH = "https://graph.instagram.com"
WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]


def load_env():
    env = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def latest_card_date():
    dates = sorted(p.name for p in CARDS_DIR.iterdir() if p.is_dir())
    return dates[-1] if dates else None


def weekday_of(date_str):
    y, mo, d = (int(x) for x in date_str.split("-"))
    return WEEKDAY_KR[datetime(y, mo, d).weekday()]


def wait_public(url, timeout=420, interval=5):
    """카드 이미지가 Vercel에 실제로 배포돼 접근 가능해질 때까지 기다림."""
    waited = 0
    while waited <= timeout:
        try:
            r = requests.head(url, timeout=10)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(interval)
        waited += interval
    return False


def create_child(image_url, ig_id, token):
    r = requests.post(f"{GRAPH}/{ig_id}/media", data={
        "image_url": image_url,
        "is_carousel_item": "true",
        "access_token": token,
    }, timeout=30)
    data = r.json()
    if "id" not in data:
        raise RuntimeError(f"child 컨테이너 생성 실패: {data}")
    return data["id"]


def create_carousel(children_ids, caption, ig_id, token):
    r = requests.post(f"{GRAPH}/{ig_id}/media", data={
        "media_type": "CAROUSEL",
        "children": ",".join(children_ids),
        "caption": caption,
        "access_token": token,
    }, timeout=30)
    data = r.json()
    if "id" not in data:
        raise RuntimeError(f"캐러셀 컨테이너 생성 실패: {data}")
    return data["id"]


def wait_container_ready(container_id, token, timeout=120, interval=5):
    waited = 0
    while waited <= timeout:
        r = requests.get(f"{GRAPH}/{container_id}", params={
            "fields": "status_code",
            "access_token": token,
        }, timeout=15)
        status = r.json().get("status_code")
        if status == "FINISHED":
            return True
        if status == "ERROR":
            raise RuntimeError(f"컨테이너 처리 실패: {r.json()}")
        time.sleep(interval)
        waited += interval
    return False


def publish(creation_id, ig_id, token):
    r = requests.post(f"{GRAPH}/{ig_id}/media_publish", data={
        "creation_id": creation_id,
        "access_token": token,
    }, timeout=30)
    data = r.json()
    if "id" not in data:
        raise RuntimeError(f"발행 실패: {data}")
    return data["id"]


def build_caption(date_str):
    weekday = weekday_of(date_str)
    return (
        f"📰 아침 뉴스 스크랩 · {date_str} ({weekday})\n"
        "전력·전기직 취업 준비용 오늘의 뉴스 브리핑, 스와이프해서 확인하세요!\n\n"
        "전체 브리핑은 프로필 링크에서 모바일 카드뉴스로 이어보실 수 있어요.\n\n"
        "#전력 #전기직 #전기기사 #전력산업 #취업준비 #뉴스브리핑 #아침뉴스"
    )


def run(date_str=None):
    date_str = date_str or latest_card_date()
    if not date_str:
        print("⚠️  생성된 카드가 없어요. 먼저 cards.py를 실행하세요.")
        return 1

    marker = CARDS_DIR / date_str / ".posted"
    if marker.exists():
        print(f"ℹ️  {date_str} 이미 게시됨 — 건너뜁니다.")
        return 0

    img_dir = CARDS_DIR / date_str
    pngs = sorted(img_dir.glob("*.png"))
    if not pngs:
        print(f"⚠️  {img_dir}에 카드 이미지가 없어요.")
        return 1

    # 캐시버스터: 같은 날짜라도 파일 내용이 바뀌면(재게시 등) CDN이 옛 이미지를
    # 그대로 서빙하지 않도록 파일 수정시각을 쿼리스트링으로 붙인다.
    urls = [f"{SITE_BASE}/cards/{date_str}/{p.name}?v={int(p.stat().st_mtime)}" for p in pngs]

    print(f"⏳ 배포 반영 대기 중… ({urls[0]})")
    if not wait_public(urls[0]):
        print("❌ 카드 이미지가 시간 내에 공개되지 않았어요. 배포(push) 됐는지 확인하세요.")
        return 1

    env = load_env()
    ig_id = env.get("IG_USER_ID", "")
    token = env.get("IG_ACCESS_TOKEN", "")
    if not ig_id or not token:
        print("❌ .env에 IG_USER_ID / IG_ACCESS_TOKEN이 없어요.")
        return 1

    print(f"⏳ 캐러셀 아이템 {len(urls)}개 업로드 중…")
    children = [create_child(u, ig_id, token) for u in urls]

    print("⏳ 캐러셀 컨테이너 생성 중…")
    container_id = create_carousel(children, build_caption(date_str), ig_id, token)

    print("⏳ 처리 대기 중…")
    wait_container_ready(container_id, token)

    print("🚀 게시 중…")
    post_id = publish(container_id, ig_id, token)

    marker.write_text(post_id, encoding="utf-8")
    print(f"✅ 인스타 게시 완료 — post id: {post_id}")
    return 0


def main_with_retry(date_str, attempts=3, backoff=30):
    """백그라운드로 던져진 프로세스라 시간 제약이 없으니, 실패해도 여유있게 재시도."""
    for attempt in range(1, attempts + 1):
        try:
            code = run(date_str)
        except Exception as e:
            code = 1
            print(f"⚠️  실패 [시도 {attempt}/{attempts}]: {e}")
        if code == 0:
            return 0
        if attempt < attempts:
            print(f"↻ {backoff}초 후 재시도합니다… [{attempt}/{attempts}]")
            time.sleep(backoff)
    print(f"❌ {attempts}회 모두 실패 — 수동으로 python instagram_post.py 실행 필요.")
    return 1


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(main_with_retry(date_arg or latest_card_date()))
