# -*- coding: utf-8 -*-
"""
스크랩 md → 인스타 카드뉴스 이미지(1080x1080 PNG) 생성.
- 표지 1장 + 헤드라인 카드 최대 8장 + (남는 뉴스 있으면) 더보기 카드 1장 = 최대 10장
  (인스타 캐러셀 한 게시물 최대 10장 제한에 맞춤)
- 실행: python cards.py [YYYY-MM-DD]  (생략 시 최신 날짜)
"""
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
SCRAP_DIR = BASE / "scraps"
CARDS_DIR = BASE / "cards"
FONT_DIR = BASE / "assets" / "fonts"
FNAME_RE = re.compile(r"뉴스스크랩_(\d{4})-(\d{2})-(\d{2})\.md$")
WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]

W = H = 1080
MAX_ITEM_CARDS = 8  # 표지(1) + 헤드라인(최대8) + 더보기(1) = 10장 이내

BG = (244, 245, 247)
INK = (29, 35, 48)
MUTED = (107, 114, 128)
BRAND = (37, 99, 235)
BRAND_SOFT = (234, 241, 255)
ACCENT = (245, 158, 11)
ACCENT_SOFT = (255, 247, 230)
WHITE = (255, 255, 255)


def font(weight, size):
    return ImageFont.truetype(str(FONT_DIR / f"Pretendard-{weight}.otf"), size)


def latest_date():
    dates = []
    for p in SCRAP_DIR.glob("뉴스스크랩_*.md"):
        m = FNAME_RE.search(p.name)
        if m:
            dates.append("-".join(m.groups()))
    if not dates:
        return None
    return sorted(dates)[-1]


def weekday_of(date_str):
    y, mo, d = (int(x) for x in date_str.split("-"))
    return WEEKDAY_KR[__import__("datetime").datetime(y, mo, d).weekday()]


def parse_slides(md):
    """md 본문을 카테고리별 뉴스 슬라이드 목록으로 분해한다."""
    category = ""
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
        if re.match(r"^---+$", line):
            continue
        m = re.match(r"^##\s+(.*)$", line)
        if m:
            category = m.group(1).strip()
            continue
        m = re.match(r"^###\s+(.*)$", line)
        if m:
            push()
            is_points = "오늘의 스크랩 포인트" in m.group(1)
            title = re.sub(r"^\d+\.\s*", "", m.group(1)).replace("*", "").strip()
            cur = {
                "category": "오늘의 스크랩 포인트" if is_points else category,
                "title": title,
                "body": [],
                "points": is_points,
            }
            continue
        if line.startswith("🔗"):
            continue
        m = re.match(r"^[-*]\s+(.*)$", line)
        if m:
            if cur:
                cur["body"].append(m.group(1))
            continue
        if cur:
            cur["body"].append(line)
    push()
    return slides


def wrap_text(draw, text, fnt, max_width):
    words = list(text)  # 한글은 어절 대신 글자 단위로 감쌈(줄바꿈 정확도 위해)
    # 어절(공백) 우선 시도, 넘치면 글자 단위로 쪼갬
    lines = []
    cur = ""
    for ch in text:
        trial = cur + ch
        if draw.textlength(trial, font=fnt) > max_width and cur:
            lines.append(cur)
            cur = ch
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def prepare_lines(draw, text, fnt, max_width, max_lines):
    lines = wrap_text(draw, text, fnt, max_width)
    truncated = len(lines) > max_lines
    lines = lines[:max_lines]
    if truncated and lines:
        last = lines[-1]
        while draw.textlength(last + "…", font=fnt) > max_width and len(last) > 1:
            last = last[:-1]
        lines[-1] = last + "…"
    return lines


def draw_wrapped(draw, xy, text, fnt, fill, max_width, max_lines, line_gap=1.42, align="left"):
    lines = prepare_lines(draw, text, fnt, max_width, max_lines)
    x, y = xy
    line_h = int(fnt.size * line_gap)
    for i, ln in enumerate(lines):
        lx = x
        if align == "center":
            lx = x + (max_width - draw.textlength(ln, font=fnt)) / 2
        draw.text((lx, y + i * line_h), ln, font=fnt, fill=fill)
    return y + len(lines) * line_h


def vertical_gradient(size, top_rgb, bottom_rgb):
    h = size[1]
    grad = np.linspace(0, 1, h).reshape(h, 1)
    top = np.array(top_rgb, dtype=np.float32)
    bottom = np.array(bottom_rgb, dtype=np.float32)
    row = (top[None, :] * (1 - grad) + bottom[None, :] * grad).astype(np.uint8)
    arr = np.repeat(row[:, None, :], size[0], axis=1)
    return Image.fromarray(arr, mode="RGB")


def rounded_pill(draw, xy, text, fnt, fg, bg, pad_x=20, pad_y=10):
    x, y = xy
    tw = draw.textlength(text, font=fnt)
    th = fnt.size
    box = (x, y, x + tw + pad_x * 2, y + th + pad_y * 2)
    draw.rounded_rectangle(box, radius=(th + pad_y * 2) // 2, fill=bg)
    draw.text((x + pad_x, y + pad_y - 2), text, font=fnt, fill=fg)
    return box[3] - box[1]  # 높이


def card_cover(date_str, weekday, total):
    img = vertical_gradient((W, H), BRAND_SOFT, ACCENT_SOFT)
    d = ImageDraw.Draw(img)
    pad = 90

    d.text((pad, 300), "📰", font=font("Regular", 90), fill=INK)
    d.text((pad, 410), "아침 뉴스 스크랩", font=font("ExtraBold", 64), fill=INK)
    d.text((pad, 495), f"{date_str} ({weekday})", font=font("SemiBold", 34), fill=MUTED)

    d.text((pad, 590), f"오늘의 브리핑 · 총 {total}개 뉴스", font=font("SemiBold", 30), fill=BRAND)
    d.text((pad, 660), "전력·전기직 취업 준비용 데일리 브리핑", font=font("Regular", 26), fill=MUTED)

    hint = "swipe → "
    d.text((pad, H - 140), "옆으로 넘겨서 보기 →", font=font("Bold", 30), fill=BRAND)
    return img


def card_news(category, title, body_paras, idx, total):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    pad = 80
    content_w = W - pad * 2

    # 카테고리 칩
    chip_fnt = font("Bold", 26)
    rounded_pill(d, (pad, 80), category or "뉴스", chip_fnt, BRAND, BRAND_SOFT)

    # 제목
    title_fnt = font("ExtraBold", 50)
    y = draw_wrapped(d, (pad, 170), title, title_fnt, INK, content_w, max_lines=4, line_gap=1.32)

    # 본문 — 제목 아래 ~ 하단 브랜드 영역 사이 빈 공간에 세로로 가운데 정렬
    body_fnt = font("Regular", 30)
    body_text = " ".join(body_paras)[:400]
    line_gap = 1.55
    line_h = int(body_fnt.size * line_gap)
    lines = prepare_lines(d, body_text, body_fnt, content_w, max_lines=7)
    block_h = len(lines) * line_h

    area_top = y + 20
    area_bottom = H - 90 - 40
    body_y = area_top + max(0, (area_bottom - area_top - block_h) // 2)
    for i, ln in enumerate(lines):
        d.text((pad, body_y + i * line_h), ln, font=body_fnt, fill=(60, 68, 82))

    # 하단 브랜드 + 페이지 표시
    foot_fnt = font("SemiBold", 26)
    d.text((pad, H - 90), "📰 아침 뉴스 스크랩", font=foot_fnt, fill=MUTED)
    counter = f"{idx} / {total}"
    cw = d.textlength(counter, font=foot_fnt)
    d.text((W - pad - cw, H - 90), counter, font=foot_fnt, fill=BRAND)
    return img


def card_cta(remaining, mobile_url):
    img = vertical_gradient((W, H), ACCENT_SOFT, BRAND_SOFT)
    d = ImageDraw.Draw(img)
    pad = 90

    d.text((pad, 340), "＋", font=font("ExtraBold", 90), fill=ACCENT)
    d.text((pad, 460), f"{remaining}개 뉴스 더보기", font=font("ExtraBold", 54), fill=INK)
    d.text((pad, 545), "전체 브리핑은 프로필 링크에서", font=font("SemiBold", 32), fill=(60, 68, 82))
    d.text((pad, 590), "모바일 카드뉴스로 이어서 볼 수 있어요", font=font("SemiBold", 32), fill=(60, 68, 82))

    d.text((pad, H - 140), "🔗 프로필 링크 확인 →", font=font("Bold", 32), fill=BRAND)
    return img


def build(date_str=None):
    date_str = date_str or latest_date()
    if not date_str:
        print("⚠️  스크랩 md가 없어요.")
        return None
    md_path = SCRAP_DIR / f"뉴스스크랩_{date_str}.md"
    if not md_path.exists():
        print(f"⚠️  {md_path.name} 파일이 없어요.")
        return None

    slides = [s for s in parse_slides(md_path.read_text(encoding="utf-8")) if not s["points"]]
    weekday = weekday_of(date_str)

    out_dir = CARDS_DIR / date_str
    out_dir.mkdir(parents=True, exist_ok=True)

    images = [card_cover(date_str, weekday, len(slides))]

    shown = slides[:MAX_ITEM_CARDS]
    remaining = len(slides) - len(shown)
    total_pages = 1 + len(shown) + (1 if remaining > 0 else 0)

    for i, s in enumerate(shown, start=1):
        images.append(card_news(s["category"], s["title"], s["body"], 1 + i, total_pages))

    if remaining > 0:
        images.append(card_cta(remaining, "https://morning-news-black.vercel.app/mobile.html"))

    paths = []
    for i, im in enumerate(images, start=1):
        p = out_dir / f"{i:02d}.png"
        im.save(p, "PNG")
        paths.append(p)

    print(f"✅ 카드 {len(paths)}장 생성 완료 → {out_dir}")
    return paths


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(0 if build(date_arg) else 1)
