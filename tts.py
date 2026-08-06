# -*- coding: utf-8 -*-
"""
스크랩 md → 카드별 음성(mp3) 생성 (edge-tts, 무료·키 불필요).
- mobile.html의 카드 순서와 동일하게 슬라이드를 나눠 audio/<date>/<n>.mp3 로 저장.
- 이미 있는 파일은 다시 만들지 않는다(재실행해도 빠름).
- 실행: python tts.py [YYYY-MM-DD]  (생략 시 최신 날짜)
"""
import asyncio
import re
import sys
from pathlib import Path

import edge_tts

BASE = Path(__file__).resolve().parent
SCRAP_DIR = BASE / "scraps"
AUDIO_DIR = BASE / "audio"
FNAME_RE = re.compile(r"뉴스스크랩_(\d{4})-(\d{2})-(\d{2})\.md$")
VOICE = "ko-KR-SunHiNeural"
RATE = "+8%"


def latest_date():
    dates = []
    for p in SCRAP_DIR.glob("뉴스스크랩_*.md"):
        m = FNAME_RE.search(p.name)
        if m:
            dates.append("{}-{}-{}".format(*m.groups()))
    if not dates:
        return None
    return sorted(dates)[-1]


def parse_slides(md):
    """generate.py의 JS parseSlides()와 동일한 규칙으로 md를 슬라이드로 쪼갠다."""
    slides = []
    cur = None

    def push():
        nonlocal cur
        if cur:
            slides.append(cur)
            cur = None

    for raw in md.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            continue
        if re.match(r"^-{3,}$", line):
            continue
        if line.startswith("## "):
            continue
        m = re.match(r"^###\s+(.*)$", line)
        if m:
            push()
            title = re.sub(r"^\d+\.\s*", "", m.group(1)).replace("*", "").strip()
            cur = {"title": title, "blocks": []}
            continue
        if line.startswith("🔗"):
            continue
        m = re.match(r"^[-*]\s+(.*)$", line)
        if m:
            if cur:
                cur["blocks"].append(m.group(1))
            continue
        if cur:
            cur["blocks"].append(line)
    push()
    return slides


def slide_text(s):
    parts = [s["title"]] + s["blocks"]
    return ". ".join(p.strip() for p in parts if p.strip())


async def synth(text, out_path):
    communicate = edge_tts.Communicate(text, voice=VOICE, rate=RATE)
    await communicate.save(str(out_path))


async def build_async(date):
    md_path = SCRAP_DIR / f"뉴스스크랩_{date}.md"
    if not md_path.exists():
        print(f"⚠️  {md_path.name} 을 찾지 못했어요.")
        return 1
    slides = parse_slides(md_path.read_text(encoding="utf-8"))
    if not slides:
        print("⚠️  카드로 나눌 내용이 없어요.")
        return 1

    out_dir = AUDIO_DIR / date
    out_dir.mkdir(parents=True, exist_ok=True)

    made = 0
    for i, s in enumerate(slides, start=1):
        out_path = out_dir / f"{i}.mp3"
        if out_path.exists():
            continue
        try:
            await synth(slide_text(s), out_path)
            made += 1
        except Exception as e:
            print(f"⚠️  {i}번 카드 음성 생성 실패: {e}")

    print(f"✅ 음성 생성 완료 — {date} 카드 {len(slides)}개 중 {made}개 새로 만듦 (audio/{date}/)")
    return 0


def build(date=None):
    date = date or latest_date()
    if not date:
        print("⚠️  뉴스스크랩_*.md 파일을 찾지 못했어요.")
        return 1
    return asyncio.run(build_async(date))


if __name__ == "__main__":
    sys.exit(build(sys.argv[1] if len(sys.argv) > 1 else None))
