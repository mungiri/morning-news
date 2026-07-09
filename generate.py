# -*- coding: utf-8 -*-
"""
뉴스 스크랩 웹 리더 빌더
- 이 폴더의 `뉴스스크랩_YYYY-MM-DD.md` 파일들을 모아
  하나의 자체 완결형 `index.html`(오프라인 동작, 더블클릭 OK)을 생성한다.
- 매일 새 md가 생기면 다시 실행:  python generate.py
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Windows 콘솔(cp949)에서 이모지 출력이 깨지지 않도록 UTF-8로 고정
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = Path(__file__).resolve().parent
SCRAP_DIR = BASE / "scraps"            # md는 이 하위 폴더에만 보관
FNAME_RE = re.compile(r"뉴스스크랩_(\d{4})-(\d{2})-(\d{2})\.md$")
WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]


def extract(md):
    """본문에서 헤드라인(홈 미리보기용)과 검색 키워드(제목들)를 뽑는다."""
    headlines, keywords = [], []
    for ln in md.splitlines():
        s = ln.strip()
        m = re.match(r"^###\s+(.*)$", s)
        if m and "오늘의 스크랩 포인트" not in m.group(1):
            t = re.sub(r"^\d+\.\s*", "", m.group(1)).replace("*", "").strip()
            if len(headlines) < 5:
                headlines.append(t)
            keywords.append(t)
            continue
        b = re.match(r"^\*\*(.+)\*\*$", s)  # 전력 섹션의 굵은 소제목
        if b:
            keywords.append(b.group(1).replace("*", "").strip())
    return headlines, keywords


def relocate_md():
    """루트에 저장된 md를 scraps/ 하위 폴더로 쓸어담는다(저장 위치 무관하게 정리)."""
    SCRAP_DIR.mkdir(exist_ok=True)
    for p in BASE.glob("뉴스스크랩_*.md"):
        p.replace(SCRAP_DIR / p.name)  # 같은 이름이 있으면 덮어씀


def collect_reports():
    """본문(markdown)은 내장하지 않고, 가벼운 메타데이터(manifest)만 만든다."""
    reports = []
    for p in SCRAP_DIR.glob("뉴스스크랩_*.md"):
        m = FNAME_RE.search(p.name)
        if not m:
            continue
        y, mo, d = (int(x) for x in m.groups())
        date_str = f"{y:04d}-{mo:02d}-{d:02d}"
        try:
            weekday = WEEKDAY_KR[datetime(y, mo, d).weekday()]
        except ValueError:
            weekday = ""
        md = p.read_text(encoding="utf-8")
        title = next(
            (ln[2:].strip() for ln in md.splitlines() if ln.startswith("# ")),
            f"아침 뉴스 스크랩 — {date_str}",
        )
        headlines, keywords = extract(md)
        reports.append({
            "date": date_str,
            "weekday": weekday,
            "title": title,
            "headlines": headlines,        # 홈 카드 미리보기
            "keywords": " ".join(keywords),  # 날짜 간 검색용 (본문 대신)
        })
    # 최신 날짜가 위로
    reports.sort(key=lambda r: r["date"], reverse=True)
    return reports


def build():
    relocate_md()
    reports = collect_reports()
    if not reports:
        print("⚠️  뉴스스크랩_*.md 파일을 찾지 못했어요. 폴더를 확인해 주세요.")
        return 1
    manifest_json = json.dumps(reports, ensure_ascii=False)
    built_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = (
        TEMPLATE
        .replace("__MANIFEST__", manifest_json)
        .replace("__BUILT_AT__", built_at)
    )
    out = BASE / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"✅ index.html 생성 완료 — 리포트 {len(reports)}건 (최근: {reports[0]['date']})")
    print(f"   파일 위치: {out}")

    mobile_html = (
        MOBILE_TEMPLATE
        .replace("__MANIFEST__", manifest_json)
        .replace("__BUILT_AT__", built_at)
    )
    mobile_out = BASE / "mobile.html"
    mobile_out.write_text(mobile_html, encoding="utf-8")
    print(f"✅ mobile.html 생성 완료 (카드뉴스 스와이프)")
    return 0


TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>📰 아침 뉴스 스크랩</title>
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="stylesheet" as="style" crossorigin
  href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css">
<style>
  :root{
    --bg:#f4f5f7; --panel:#ffffff; --ink:#1d2330; --muted:#6b7280;
    --line:#e6e8ec; --brand:#2563eb; --brand-soft:#eaf1ff;
    --accent:#f59e0b; --accent-soft:#fff7e6; --chip:#f1f3f6; --chip-ink:#374151;
    --shadow:0 1px 3px rgba(20,30,60,.06),0 8px 24px rgba(20,30,60,.06);
  }
  @media (prefers-color-scheme: dark){
    :root{
      --bg:#0f1115; --panel:#171a21; --ink:#e7eaf0; --muted:#9aa3b2;
      --line:#262b35; --brand:#6ea8fe; --brand-soft:#16223a;
      --accent:#f5b13d; --accent-soft:#2a2316; --chip:#222732; --chip-ink:#c6cdda;
      --shadow:0 1px 3px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
    }
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0}
  body{
    background:var(--bg); color:var(--ink);
    font-family:'Pretendard Variable','Pretendard','Apple SD Gothic Neo',
      system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI','Malgun Gothic',sans-serif;
    line-height:1.72; -webkit-font-smoothing:antialiased; letter-spacing:-.01em;
  }
  a{color:var(--brand);text-decoration:none}
  a:hover{text-decoration:underline}

  .layout{display:flex;min-height:100vh;max-width:1240px;margin:0 auto}

  /* ── Sidebar ── */
  .side{
    width:288px;flex:0 0 288px;border-right:1px solid var(--line);
    padding:22px 16px;position:sticky;top:0;height:100vh;overflow:auto;
    background:var(--panel);
  }
  .sidehead{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:2px 2px 0}
  .brand{display:flex;align-items:center;gap:9px;font-weight:800;font-size:18px;
    letter-spacing:-.3px;margin:0;background:none;border:none;padding:0;cursor:pointer;
    color:inherit;font-family:inherit}
  .brand:hover{color:var(--brand)}
  .brand-sub{font-size:11.5px;color:var(--muted);margin:4px 4px 14px}
  .search{width:100%;padding:9px 12px;border:1px solid var(--line);border-radius:10px;
    background:var(--bg);color:var(--ink);font-size:13px;margin-bottom:12px;outline:none}
  .search:focus{border-color:var(--brand)}
  .datelist{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:4px}
  .datelist li{padding:0}
  .datebtn{display:flex;justify-content:space-between;align-items:center;gap:8px;
    width:100%;text-align:left;border:1px solid transparent;background:transparent;
    color:var(--ink);padding:10px 12px;border-radius:10px;cursor:pointer;font-size:14px;
    font-family:inherit}
  .datebtn:hover{background:var(--bg)}
  .datebtn.active{background:var(--brand-soft);border-color:var(--brand);font-weight:700}
  .datebtn .wd{font-size:12px;color:var(--muted);font-weight:600}
  .sidefoot{margin-top:18px;padding:0 6px;font-size:11px;color:var(--muted)}

  /* ── Main ── */
  .main{flex:1;min-width:0;padding:34px clamp(18px,5vw,56px) 80px}
  .collapse,.reopen{display:inline-flex;align-items:center;justify-content:center;
    border:1px solid var(--line);background:var(--panel);color:var(--muted);
    border-radius:9px;cursor:pointer;font-family:inherit;line-height:1}
  .collapse{width:30px;height:30px;font-size:18px;flex:0 0 auto}
  .collapse:hover,.reopen:hover{border-color:var(--brand);color:var(--brand)}
  .reopen{position:fixed;left:14px;top:14px;z-index:40;width:38px;height:38px;
    font-size:17px;box-shadow:var(--shadow);display:none}
  body.collapsed .reopen{display:inline-flex}
  @media (min-width:761px){ body.collapsed .side{display:none} }
  mark{background:#ffe58a;color:#1d2330;border-radius:3px;padding:0 1px}
  .scount{font-size:11.5px;color:var(--muted);margin:8px 4px 2px}
  .flag{height:.95em;width:auto;vertical-align:-2px;border-radius:2px;
    box-shadow:0 0 0 1px var(--line)}
  .content{max-width:820px;margin:0 auto}
  .content h1{font-size:clamp(24px,3.6vw,33px);font-weight:850;letter-spacing:-.6px;
    line-height:1.25;margin:.2em 0 .1em}
  .content hr{border:none;border-top:1px solid var(--line);margin:22px 0}
  .content h2{font-size:20px;font-weight:800;letter-spacing:-.3px;margin:34px 0 6px;
    padding:10px 14px;background:var(--brand-soft);border-radius:12px;
    display:flex;align-items:center;gap:8px}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:16px;
    padding:18px 20px;margin:14px 0;box-shadow:var(--shadow)}
  .card h3{font-size:17.5px;font-weight:800;line-height:1.4;margin:0 0 8px;letter-spacing:-.3px}
  .card h3.sub{font-size:16px}
  .card p{margin:8px 0;color:var(--ink);font-size:15.3px}
  .card.points{background:var(--accent-soft);border-color:var(--accent)}
  .card.points h3{color:var(--accent)}
  .card ul{margin:6px 0 2px;padding-left:20px}
  .card li{margin:7px 0;font-size:15px}
  .chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px}
  .chip{display:inline-flex;align-items:center;gap:5px;background:var(--chip);
    color:var(--chip-ink);font-size:12.5px;padding:5px 11px;border-radius:999px;
    border:1px solid var(--line);max-width:100%;}
  .chip:hover{text-decoration:none;border-color:var(--brand);color:var(--brand)}
  .chip span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .empty{color:var(--muted);text-align:center;margin-top:80px}

  /* ── Home (landing) ── */
  [hidden]{display:none!important}
  .home{max-width:1000px;margin:0 auto}
  .hero{position:relative;padding:26px 24px 22px;border-radius:20px;overflow:hidden;
    background:linear-gradient(135deg,var(--brand-soft),var(--accent-soft));
    border:1px solid var(--line);box-shadow:var(--shadow);margin-bottom:6px}
  .hero::after{content:"";position:absolute;right:-40px;top:-44px;width:170px;height:170px;
    background:radial-gradient(circle,var(--brand) 0%,transparent 70%);opacity:.12;pointer-events:none}
  .hero-greet{font-size:13.5px;font-weight:700;color:var(--brand);margin:0 0 6px;letter-spacing:-.2px}
  .hero h1{font-size:clamp(26px,4vw,38px);font-weight:850;letter-spacing:-.6px;margin:0 0 6px}
  .hero p{color:var(--muted);margin:0;font-size:15px}
  .stats{display:flex;gap:10px;margin-top:18px;flex-wrap:wrap}
  .stat{background:var(--panel);border:1px solid var(--line);border-radius:13px;
    padding:10px 16px;min-width:86px;display:flex;flex-direction:column;gap:1px}
  .stat b{font-size:20px;font-weight:850;letter-spacing:-.4px;line-height:1.15}
  .stat span{font-size:11.5px;color:var(--muted);font-weight:600}

  /* 읽음/안읽음 · 즐겨찾기 */
  .hcard.read{opacity:.6}
  .hcard.read:hover{opacity:1}
  .hcard-dot{width:8px;height:8px;border-radius:50%;background:var(--brand);flex:0 0 auto;
    box-shadow:0 0 0 3px var(--brand-soft)}
  .hcard-star{margin-left:auto;font-size:18px;line-height:1;cursor:pointer;color:var(--muted);
    padding:0 2px;user-select:none}
  .hcard-star:hover{color:var(--accent)}
  .hcard-star.on{color:var(--accent)}

  /* 맨 위로 */
  .fab{position:fixed;right:20px;bottom:20px;z-index:40;width:44px;height:44px;border-radius:50%;
    border:1px solid var(--line);background:var(--panel);color:var(--brand);font-size:20px;
    cursor:pointer;box-shadow:var(--shadow);display:none;align-items:center;justify-content:center;
    font-family:inherit;line-height:1}
  .fab.show{display:inline-flex}
  .fab:hover{border-color:var(--brand)}
  .hsection-label{font-size:12.5px;font-weight:800;color:var(--muted);letter-spacing:.04em;
    margin:30px 4px 12px}
  .hgrid{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(248px,1fr))}
  .feat-grid{grid-template-columns:1fr}
  .hcard{text-align:left;background:var(--panel);border:1px solid var(--line);border-radius:16px;
    padding:18px 20px;cursor:pointer;font-family:inherit;color:var(--ink);box-shadow:var(--shadow);
    display:flex;flex-direction:column;gap:10px;min-width:0;
    transition:transform .12s ease,border-color .12s ease}
  .hcard:hover{transform:translateY(-2px);border-color:var(--brand)}
  .hcard.feat{background:var(--brand-soft);border-color:var(--brand)}
  .hcard-top{display:flex;align-items:center;gap:8px}
  .hcard-date{font-size:18px;font-weight:800;letter-spacing:-.3px}
  .hcard.feat .hcard-date{font-size:22px}
  .hcard-wd{font-size:13px;color:var(--muted);font-weight:600}
  .hcard-badge{margin-left:8px;background:var(--brand);color:#fff;font-size:11px;font-weight:800;
    padding:3px 10px;border-radius:999px}
  .hcard-peek{margin:0;padding-left:18px;display:flex;flex-direction:column;gap:5px}
  .hcard-peek li{font-size:14px;line-height:1.5;color:var(--ink);
    overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .hcard-go{color:var(--brand);font-size:13.5px;font-weight:700;margin-top:2px}

  @media (max-width:760px){
    .side{position:fixed;left:0;top:0;z-index:30;transform:translateX(-100%);
      transition:transform .22s ease;box-shadow:var(--shadow)}
    .side.open{transform:translateX(0)}
    .reopen{display:inline-flex}                 /* 모바일에선 펼치기 버튼 항상 표시 */
    .backdrop{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:20}
    .backdrop.show{display:block}
    .main{padding-top:20px}
  }
</style>
</head>
<body>
<div class="backdrop" id="backdrop"></div>
<button class="reopen" id="reopen" title="날짜 목록 열기" aria-label="날짜 목록 열기">☰</button>
<button class="fab" id="fab" title="맨 위로" aria-label="맨 위로">↑</button>
<div class="layout">
  <aside class="side" id="side">
    <div class="sidehead">
      <button class="brand" id="home-btn" title="홈으로">📰 뉴스 스크랩</button>
      <button class="collapse" id="collapse" title="목록 접기" aria-label="목록 접기">«</button>
    </div>
    <div class="brand-sub">전력·전기직 취업 준비용 데일리 브리핑</div>
    <input class="search" id="search" type="search" placeholder="🔎 날짜·내용 검색 (예: 한전, 06-29)">
    <div class="scount" id="scount"></div>
    <ul class="datelist" id="datelist"></ul>
    <div class="sidefoot">빌드: __BUILT_AT__</div>
  </aside>

  <main class="main">
    <section class="home" id="home"></section>
    <article class="content" id="content" hidden></article>
  </main>
</div>

<script>
// 모바일 접속 시 카드뉴스 전용 페이지(mobile.html)로 자동 이동.
// ?desktop=1 로 들어오거나 한 번 데스크톱을 선택하면 다시 안 옮김(localStorage 기억).
(function(){
  const params = new URLSearchParams(location.search);
  if(params.get('desktop') === '1'){
    try{ localStorage.setItem('prefer-desktop', '1'); }catch(e){}
    return;
  }
  // localStorage가 막힌 브라우저(인스타 인앱 브라우저 등)에서도
  // '데스크톱 기억' 기능만 못 쓸 뿐, 모바일 리다이렉트 자체는 항상 되게 분리.
  let preferDesktop = false;
  try{ preferDesktop = localStorage.getItem('prefer-desktop') === '1'; }catch(e){}
  if(preferDesktop) return;
  const isMobile = window.matchMedia('(max-width:760px)').matches
    || /Android|iPhone|iPad|iPod|Instagram/i.test(navigator.userAgent);
  if(isMobile){ location.replace('mobile.html'); }
})();

// 가벼운 목록만 내장(본문 X). 본문은 날짜를 열 때 해당 md 파일을 fetch.
const MANIFEST = __MANIFEST__;
const cache = {};   // 한 번 불러온 본문은 캐시
function mdUrl(date){ return './scraps/' + encodeURIComponent('뉴스스크랩_' + date + '.md'); }
async function fetchReport(i){
  const d = MANIFEST[i].date;
  if(cache[d] != null) return cache[d];
  const res = await fetch(mdUrl(d));
  if(!res.ok) throw new Error('HTTP ' + res.status);
  cache[d] = await res.text();
  return cache[d];
}

/* ---------- 태극기 인라인 SVG (Windows가 🇰🇷 국기 이모지를 못 그려서 직접 그림) ---------- */
const TRI = { geon:[1,1,1], gam:[0,1,0], ri:[1,0,1], gon:[0,0,0] };
function trigram(cx, cy, pat){
  let o = '';
  pat.forEach((solid, k) => {
    const y = cy - 2.3 + k * 2.3 - 0.5;
    if(solid){ o += `<rect x="${cx-4}" y="${y}" width="8" height="1" fill="#111"/>`; }
    else{ o += `<rect x="${cx-4}" y="${y}" width="3.2" height="1" fill="#111"/>`
             + `<rect x="${cx+0.8}" y="${y}" width="3.2" height="1" fill="#111"/>`; }
  });
  return o;
}
const FLAG =
  '<svg class="flag" viewBox="0 0 36 24" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="태극기">'
  + '<rect width="36" height="24" rx="2" fill="#fff"/>'
  + '<g transform="rotate(-56.31 18 12)">'
  + '<path d="M18,6 A6,6 0 0 1 18,18 A3,3 0 0 1 18,12 A3,3 0 0 0 18,6 Z" fill="#cd2e3a"/>'
  + '<path d="M18,6 A6,6 0 0 0 18,18 A3,3 0 0 0 18,12 A3,3 0 0 1 18,6 Z" fill="#0047a0"/>'
  + '</g>'
  + trigram(8,5,TRI.geon)  + trigram(28,5,TRI.gam)
  + trigram(8,19,TRI.ri)   + trigram(28,19,TRI.gon)
  + '</svg>';

/* ---------- 마크다운 → HTML (이 스크랩 형식에 맞춘 경량 렌더러) ---------- */
function escapeHtml(s){
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}
function inline(s){
  s = escapeHtml(s);
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g,
        '<a href="$2" target="_blank" rel="noopener">$1</a>');
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  s = s.replace(/🇰🇷/g, () => FLAG);
  return s;
}
function chip(url){
  let host = url;
  try{ host = new URL(url).hostname.replace(/^www\./,''); }catch(e){}
  return '<a class="chip" href="'+escapeHtml(url)+'" target="_blank" rel="noopener">'
       + '🔗 <span>'+escapeHtml(host)+'</span></a>';
}
function renderMarkdown(md){
  const lines = md.split(/\r?\n/);
  let html = '', inList = false, cardOpen = false, chips = '';
  const closeList = () => { if(inList){ html+='</ul>'; inList=false; } };
  const flushChips = () => { if(chips){ html+='<div class="chips">'+chips+'</div>'; chips=''; } };
  const closeCard = () => { if(cardOpen){ closeList(); flushChips(); html+='</div>'; cardOpen=false; } };
  let m;
  for(const raw of lines){
    const line = raw.trim();
    if(line === ''){ closeList(); flushChips(); continue; }
    if(/^---+$/.test(line)){ closeCard(); html+='<hr>'; continue; }
    if((m = line.match(/^#\s+(.*)$/))){ closeCard(); html+='<h1>'+inline(m[1])+'</h1>'; continue; }
    if((m = line.match(/^##\s+(.*)$/))){ closeCard(); html+='<h2>'+inline(m[1])+'</h2>'; continue; }
    if((m = line.match(/^###\s+(.*)$/))){
      closeCard();
      const isPoints = /오늘의 스크랩 포인트/.test(m[1]);
      html += '<div class="card'+(isPoints?' points':'')+'">';
      cardOpen = true;
      html += '<h3>'+inline(m[1])+'</h3>';
      continue;
    }
    if(line.startsWith('🔗')){ chips += chip(line.replace('🔗','').trim()); continue; }
    if((m = line.match(/^[-*]\s+(.*)$/))){
      flushChips();
      if(!inList){ html+='<ul>'; inList=true; }
      html += '<li>'+inline(m[1])+'</li>';
      continue;
    }
    if((m = line.match(/^\*\*(.+)\*\*$/))){            // 전력 섹션의 굵은 소제목 → 카드
      closeCard();
      html += '<div class="card"><h3 class="sub">'+inline(m[1])+'</h3>';
      cardOpen = true;
      continue;
    }
    if((m = line.match(/^>\s?(.*)$/))){ flushChips(); html+='<blockquote>'+inline(m[1])+'</blockquote>'; continue; }
    closeList(); flushChips();
    html += '<p>'+inline(line)+'</p>';
  }
  closeCard(); closeList(); flushChips();
  return html;
}

/* ---------- UI ---------- */
const $ = (id) => document.getElementById(id);
const MOBILE = () => window.matchMedia('(max-width:760px)').matches;
let current = -1;   // -1 = 홈 화면

/* ---------- 읽음 표시 · 즐겨찾기 (localStorage) ---------- */
const LS = {
  get(k){ try{ return JSON.parse(localStorage.getItem(k)) || []; }catch(e){ return []; } },
  set(k,v){ try{ localStorage.setItem(k, JSON.stringify(v)); }catch(e){} }
};
const readSet = new Set(LS.get('read-dates'));
const markSet = new Set(LS.get('bookmarks'));
const isRead = (d) => readSet.has(d);
const isMark = (d) => markSet.has(d);
function markRead(d){ if(!readSet.has(d)){ readSet.add(d); LS.set('read-dates', [...readSet]); } }
function toggleMark(d){
  if(markSet.has(d)) markSet.delete(d); else markSet.add(d);
  LS.set('bookmarks', [...markSet]);
}

/* ---------- 시간대별 인사말 · 연속 기록(streak) ---------- */
function greeting(){
  const h = new Date().getHours();
  if(h < 6)  return '🌙 새벽까지 고생이 많네요';
  if(h < 11) return '🌅 좋은 아침이에요';
  if(h < 14) return '☀️ 좋은 점심이에요';
  if(h < 18) return '🌤️ 좋은 오후예요';
  if(h < 22) return '🌆 좋은 저녁이에요';
  return '🌙 늦은 시간이네요';
}
// 최신 날짜부터 하루씩 거슬러 끊기지 않고 이어진 브리핑 일수
// (UTC 변환 시 KST에서 하루 밀리므로 날짜 키는 로컬 기준으로 만든다)
function streak(){
  if(!MANIFEST.length) return 0;
  const have = new Set(MANIFEST.map(r => r.date));
  const pad = (n) => String(n).padStart(2, '0');
  const key = (d) => d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  const [y, m, dd] = MANIFEST[0].date.split('-').map(Number);
  let n = 0, d = new Date(y, m - 1, dd);
  while(have.has(key(d))){ n++; d.setDate(d.getDate() - 1); }
  return n;
}

// 날짜·요일·제목·헤드라인(키워드)으로 날짜 간 검색
function matches(r, q){
  if(!q) return true;
  q = q.toLowerCase();
  return r.date.includes(q) || (r.weekday||'').includes(q)
      || r.title.toLowerCase().includes(q)
      || (r.keywords||'').toLowerCase().includes(q);
}
function renderList(q){
  const ul = $('datelist'); ul.innerHTML = '';
  let shown = 0;
  MANIFEST.forEach((r, i) => {
    if(!matches(r, q)) return;
    shown++;
    const li = document.createElement('li');
    const b = document.createElement('button');
    b.className = 'datebtn' + (i===current ? ' active' : '');
    b.innerHTML = '<span>'+r.date+'</span><span class="wd">('+(r.weekday||'')+')</span>';
    b.onclick = () => { select(i); if(MOBILE()) closeSide(); };
    li.appendChild(b); ul.appendChild(li);
  });
  $('scount').textContent = q ? ('검색 결과 ' + shown + '건') : '';
  return shown;
}
// 본문에서 검색어를 <mark>로 강조
function highlight(q){
  if(!q) return;
  const esc = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const test = new RegExp(esc, 'i');
  const rep  = new RegExp('(' + esc + ')', 'ig');
  const walker = document.createTreeWalker($('content'), NodeFilter.SHOW_TEXT);
  const hits = []; let n;
  while((n = walker.nextNode())){ if(test.test(n.nodeValue)) hits.push(n); }
  hits.forEach(node => {
    const span = document.createElement('span');
    span.innerHTML = node.nodeValue
      .replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))
      .replace(rep, '<mark>$1</mark>');
    node.replaceWith(span);
  });
}
function homeCard(i, featured){
  const r = MANIFEST[i];
  const read = isRead(r.date), mark = isMark(r.date);
  const peek = (r.headlines || []).slice(0, featured ? 5 : 3)
    .map(h => '<li>' + escapeHtml(h) + '</li>').join('');
  return '<button class="hcard' + (featured ? ' feat' : '') + (read ? ' read' : '') + '" data-i="' + i + '">'
    + '<div class="hcard-top">'
    + (read ? '' : '<span class="hcard-dot" title="안 읽음"></span>')
    + '<span class="hcard-date">' + r.date + '</span>'
    + '<span class="hcard-wd">(' + (r.weekday||'') + ')</span>'
    + '<span class="hcard-star' + (mark ? ' on' : '') + '" data-star="' + i + '" '
    +   'role="button" title="즐겨찾기" aria-label="즐겨찾기">' + (mark ? '★' : '☆') + '</span>'
    + (featured ? '<span class="hcard-badge">최신</span>' : '')
    + '</div><ul class="hcard-peek">' + peek + '</ul>'
    + '<div class="hcard-go">브리핑 열기 →</div></button>';
}
function buildHome(){
  const total = MANIFEST.length;
  const latest = total ? MANIFEST[0].date.slice(5).replace('-', '/') : '—';
  let h = '<div class="hero">'
        + '<div class="hero-greet">' + greeting() + '</div>'
        + '<h1>📰 아침 뉴스 스크랩</h1>'
        + '<p>전력·전기직 취업 준비용 데일리 브리핑</p>';
  if(total){
    h += '<div class="stats">'
       + '<div class="stat"><b>' + total + '</b><span>총 브리핑</span></div>'
       + '<div class="stat"><b>' + latest + '</b><span>최신</span></div>'
       + '<div class="stat"><b>' + streak() + '일</b><span>연속 기록</span></div>'
       + '</div>';
  }
  h += '</div>';

  if(total){
    // ⭐ 즐겨찾기 (있을 때만, 최신순 유지)
    const marks = MANIFEST.map((r, i) => i).filter(i => isMark(MANIFEST[i].date));
    if(marks.length){
      h += '<div class="hsection-label">⭐ 즐겨찾기</div><div class="hgrid">';
      marks.forEach(i => h += homeCard(i, false));
      h += '</div>';
    }
    h += '<div class="hsection-label">오늘의 브리핑</div>'
       + '<div class="hgrid feat-grid">' + homeCard(0, true) + '</div>';
    if(total > 1){
      h += '<div class="hsection-label">지난 브리핑</div><div class="hgrid">';
      for(let i = 1; i < total; i++) h += homeCard(i, false);
      h += '</div>';
    }
  } else {
    h += '<p class="empty">아직 스크랩이 없어요.</p>';
  }
  const home = $('home');
  home.innerHTML = h;
  // 별(즐겨찾기) 토글 — 카드 열기보다 먼저 가로채기
  home.querySelectorAll('.hcard-star').forEach(s => {
    s.onclick = (e) => {
      e.stopPropagation();
      toggleMark(MANIFEST[parseInt(s.dataset.star, 10)].date);
      buildHome();
    };
  });
  home.querySelectorAll('.hcard').forEach(b => {
    b.onclick = () => select(parseInt(b.dataset.i, 10));
  });
}
function showHome(){
  current = -1;
  $('content').hidden = true;
  $('home').hidden = false;
  buildHome();
  renderList($('search').value.trim());
  location.hash = '';
  window.scrollTo({top:0});
}
// 이미 불러온(캐시된) 본문을 다시 그리고 강조만 갱신
function rerender(){
  if(current < 0) return;
  const md = cache[MANIFEST[current].date];
  if(md == null) return;
  $('content').innerHTML = renderMarkdown(md);
  highlight($('search').value.trim());
}
async function select(i){
  current = i;
  markRead(MANIFEST[i].date);   // 연 브리핑은 읽음 처리
  $('home').hidden = true;
  $('content').hidden = false;
  location.hash = MANIFEST[i].date;
  renderList($('search').value.trim());
  window.scrollTo({top:0, behavior:'smooth'});
  if(cache[MANIFEST[i].date] == null){
    $('content').innerHTML = '<p class="empty">불러오는 중…</p>';
  }
  try{
    const md = await fetchReport(i);
    if(current !== i) return;   // 그새 다른 날짜를 눌렀으면 무시
    $('content').innerHTML = renderMarkdown(md);
    highlight($('search').value.trim());
  }catch(e){
    if(current !== i) return;
    $('content').innerHTML = '<p class="empty">브리핑을 불러오지 못했어요.<br>'
      + '온라인 상태에서 다시 시도해 주세요. (로컬에서 열었다면 서버가 필요해요)</p>';
  }
}
function onSearch(){
  const q = $('search').value.trim();
  renderList(q);
  // 홈 화면에서 검색하면 첫 매칭 글로 이동
  if(current < 0){
    if(q){ const first = MANIFEST.findIndex(r => matches(r, q)); if(first >= 0) select(first); }
    return;
  }
  // 보던 글이 검색과 안 맞으면 첫 매칭 글로, 맞으면 강조만 갱신
  if(q && !matches(MANIFEST[current], q)){
    const first = MANIFEST.findIndex(r => matches(r, q));
    if(first >= 0){ select(first); return; }
  }
  rerender();
}
function openSide(){ $('side').classList.add('open'); $('backdrop').classList.add('show'); }
function closeSide(){ $('side').classList.remove('open'); $('backdrop').classList.remove('show'); }
// 사이드바 안의 « 버튼 → 접기 (모바일은 드로어 닫기)
function collapse(){
  if(MOBILE()){ closeSide(); return; }
  document.body.classList.add('collapsed');
  try{ localStorage.setItem('side-collapsed', '1'); }catch(e){}
}
// 좌상단 ☰ 버튼 → 펼치기 (모바일은 드로어 열기)
function expand(){
  if(MOBILE()){ openSide(); return; }
  document.body.classList.remove('collapsed');
  try{ localStorage.setItem('side-collapsed', '0'); }catch(e){}
}

$('search').addEventListener('input', onSearch);
$('collapse').addEventListener('click', collapse);
$('reopen').addEventListener('click', expand);
$('backdrop').addEventListener('click', closeSide);
$('home-btn').addEventListener('click', () => { showHome(); if(MOBILE()) closeSide(); });

// 맨 위로 버튼 — 스크롤 내리면 표시
const fab = $('fab');
window.addEventListener('scroll', () => { fab.classList.toggle('show', window.scrollY > 400); }, {passive:true});
fab.addEventListener('click', () => window.scrollTo({top:0, behavior:'smooth'}));

// 데스크톱 접힘 상태 복원
try{
  if(localStorage.getItem('side-collapsed') === '1' && !MOBILE())
    document.body.classList.add('collapsed');
}catch(e){}

// 해시(#날짜) ↔ 화면 동기화 — 브라우저 뒤로/앞으로 가기 지원
function applyHash(){
  const h = location.hash.slice(1);
  const idx = MANIFEST.findIndex(r => r.date === h);
  if(idx >= 0){ if(idx !== current) select(idx); }
  else if(current !== -1){ showHome(); }
}
window.addEventListener('hashchange', applyHash);
// 첫 진입: 해시(#날짜) 있으면 그 리포트로, 없으면 홈
if(location.hash.slice(1)) applyHash(); else showHome();
</script>
</body>
</html>
"""


MOBILE_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">
<title>📰 아침 뉴스 카드</title>
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="stylesheet" as="style" crossorigin
  href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css">
<style>
  :root{
    --bg:#f4f5f7; --panel:#ffffff; --ink:#1d2330; --muted:#6b7280;
    --line:#e6e8ec; --brand:#2563eb; --brand-soft:#eaf1ff;
    --accent:#f59e0b; --accent-soft:#fff7e6;
    --shadow:0 1px 3px rgba(20,30,60,.06),0 8px 24px rgba(20,30,60,.06);
  }
  @media (prefers-color-scheme: dark){
    :root{
      --bg:#0f1115; --panel:#171a21; --ink:#e7eaf0; --muted:#9aa3b2;
      --line:#262b35; --brand:#6ea8fe; --brand-soft:#16223a;
      --accent:#f5b13d; --accent-soft:#2a2316;
      --shadow:0 1px 3px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
    }
  }
  *{box-sizing:border-box; -webkit-tap-highlight-color:transparent}
  html,body{margin:0;padding:0;overscroll-behavior:none;overflow:hidden}
  body{
    background:var(--bg); color:var(--ink);
    font-family:'Pretendard Variable','Pretendard','Apple SD Gothic Neo',
      system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI','Malgun Gothic',sans-serif;
    -webkit-font-smoothing:antialiased; letter-spacing:-.01em;
  }
  a{color:inherit}

  .topbar{position:fixed;top:0;left:0;right:0;z-index:20;display:flex;align-items:center;
    gap:8px;padding:12px 14px;padding-top:calc(12px + env(safe-area-inset-top));
    pointer-events:none}
  .topbar > *{pointer-events:auto}
  .navbtn{background:var(--panel);border:1px solid var(--line);border-radius:999px;
    width:34px;height:34px;flex:0 0 auto;display:flex;align-items:center;justify-content:center;
    color:var(--ink);font-size:15px;box-shadow:var(--shadow);cursor:pointer}
  .navbtn:disabled{opacity:.35}
  .navbtn.home{width:auto;padding:0 12px;font-size:12.5px;font-weight:700;color:var(--muted)}
  .datepill{flex:1;text-align:center;font-size:13px;font-weight:800;background:var(--panel);
    border:1px solid var(--line);border-radius:999px;padding:8px 10px;box-shadow:var(--shadow);
    overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .datepill .wd{color:var(--muted);font-weight:600;margin-left:4px}

  .deck{position:fixed;inset:0;display:flex;overflow-x:auto;overflow-y:hidden;
    scroll-snap-type:x mandatory;-webkit-overflow-scrolling:touch}
  .slide{flex:0 0 100vw;height:100vh;height:100dvh;scroll-snap-align:start;
    scroll-snap-stop:always;display:flex;flex-direction:column;box-sizing:border-box;
    padding:76px 22px 96px;overflow-y:auto}
  .slide.cover{align-items:center;justify-content:center;text-align:center;
    background:linear-gradient(135deg,var(--brand-soft),var(--accent-soft))}
  .slide.cover h1{font-size:clamp(24px,7vw,32px);font-weight:850;letter-spacing:-.5px;margin:0 0 10px}
  .slide.cover p{color:var(--muted);font-size:14px;margin:0 0 26px}
  .swipe-hint{font-size:13px;color:var(--brand);font-weight:700;
    animation:nudge 1.4s ease-in-out infinite}
  @keyframes nudge{0%,100%{transform:translateX(0)}50%{transform:translateX(6px)}}

  .cat-chip{display:inline-flex;align-self:flex-start;background:var(--brand-soft);color:var(--brand);
    font-size:12px;font-weight:800;padding:5px 12px;border-radius:999px;margin-bottom:16px}
  .slide.points .cat-chip{background:var(--accent-soft);color:var(--accent)}
  .slide h2{font-size:clamp(21px,6vw,27px);font-weight:850;line-height:1.38;letter-spacing:-.4px;
    margin:0 0 18px}
  .slide-text p{font-size:16px;line-height:1.85;margin:0 0 14px;color:var(--ink)}
  .slide-text ul{margin:0;padding-left:20px;display:flex;flex-direction:column;gap:14px}
  .slide-text li{font-size:15.5px;line-height:1.8}
  .links{margin-top:auto;padding-top:18px;display:flex;flex-wrap:wrap;gap:8px}
  .linkbtn{display:inline-flex;align-items:center;gap:6px;background:var(--panel);color:var(--brand);
    font-size:13px;font-weight:700;padding:9px 14px;border-radius:999px;border:1px solid var(--line);
    text-decoration:none;box-shadow:var(--shadow)}

  .progress-wrap{position:fixed;left:0;right:0;bottom:0;z-index:20;
    padding:10px 20px calc(14px + env(safe-area-inset-bottom));pointer-events:none}
  .progress-track{height:3px;border-radius:2px;background:var(--line);overflow:hidden}
  .progress-fill{height:100%;background:var(--brand);width:0%;transition:width .15s ease}
  .progress-label{text-align:center;font-size:11.5px;color:var(--muted);margin-top:7px;font-weight:600}

  .empty{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;
    color:var(--muted);text-align:center;padding:0 30px}
</style>
</head>
<body>
<div id="app"></div>
<script>
const MANIFEST = __MANIFEST__;
const $ = (tag) => document.createElement(tag);
function escapeHtml(s){
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}
function mdUrl(date){ return './scraps/' + encodeURIComponent('뉴스스크랩_' + date + '.md'); }

/* ---------- md → 슬라이드 배열 ---------- */
function parseSlides(md){
  const lines = md.split(/\r?\n/);
  let category = '';
  let slides = [];
  let cur = null;
  const push = () => { if(cur){ slides.push(cur); cur = null; } };
  for(const raw of lines){
    const line = raw.trim();
    if(line === '') continue;
    let m;
    if(/^#\s+/.test(line)) continue;
    if(/^---+$/.test(line)) continue;
    if((m = line.match(/^##\s+(.*)$/))){ category = m[1].trim(); continue; }
    if((m = line.match(/^###\s+(.*)$/))){
      push();
      const isPoints = /오늘의 스크랩 포인트/.test(m[1]);
      const title = m[1].replace(/^\d+\.\s*/, '').replace(/\*/g, '').trim();
      cur = { category: isPoints ? '💡 오늘의 스크랩 포인트' : category, title, points: isPoints, blocks: [], links: [] };
      continue;
    }
    if(line.startsWith('🔗')){ if(cur) cur.links.push(line.replace('🔗', '').trim()); continue; }
    if((m = line.match(/^[-*]\s+(.*)$/))){ if(cur) cur.blocks.push({ li: m[1] }); continue; }
    if(cur) cur.blocks.push({ p: line });
  }
  push();
  return slides;
}
function renderBlocks(blocks){
  let html = '', inList = false;
  const close = () => { if(inList){ html += '</ul>'; inList = false; } };
  blocks.forEach(b => {
    if(b.li != null){
      if(!inList){ html += '<ul>'; inList = true; }
      html += '<li>' + escapeHtml(b.li) + '</li>';
    } else {
      close();
      html += '<p>' + escapeHtml(b.p) + '</p>';
    }
  });
  close();
  return html;
}
function chipHost(url){
  let host = url;
  try{ host = new URL(url).hostname.replace(/^www\./, ''); }catch(e){}
  return host;
}

/* ---------- 상태 ---------- */
const app = document.getElementById('app');
let dateIdx = 0;

function buildShell(){
  app.innerHTML = '';
  const top = $('div'); top.className = 'topbar';
  const prev = $('button'); prev.className = 'navbtn'; prev.textContent = '‹';
  prev.title = '이전 브리핑'; prev.disabled = dateIdx >= MANIFEST.length - 1;
  prev.onclick = () => loadDate(dateIdx + 1);
  const pill = $('div'); pill.className = 'datepill'; pill.id = 'datepill';
  const home = $('a'); home.className = 'navbtn home'; home.textContent = '전체목록';
  home.href = 'index.html?desktop=1';
  const next = $('button'); next.className = 'navbtn'; next.textContent = '›';
  next.title = '다음 브리핑'; next.disabled = dateIdx <= 0;
  next.onclick = () => loadDate(dateIdx - 1);
  top.append(prev, pill, next, home);

  const deck = $('div'); deck.className = 'deck'; deck.id = 'deck';

  const progWrap = $('div'); progWrap.className = 'progress-wrap';
  const track = $('div'); track.className = 'progress-track';
  const fill = $('div'); fill.className = 'progress-fill'; fill.id = 'progress-fill';
  track.appendChild(fill);
  const label = $('div'); label.className = 'progress-label'; label.id = 'progress-label';
  progWrap.append(track, label);

  app.append(top, deck, progWrap);
}

function renderEmpty(){
  app.innerHTML = '<div class="empty"><p>아직 스크랩이 없어요.<br>PC에서 먼저 브리핑을 생성해 주세요.</p></div>';
}

function showMessage(msg){
  const deck = document.getElementById('deck');
  deck.innerHTML = '<div class="slide" style="align-items:center;justify-content:center;text-align:center;color:var(--muted)">' + msg + '</div>';
}

function buildDeck(md, report){
  const deck = document.getElementById('deck');
  deck.innerHTML = '';
  const slides = parseSlides(md);

  const cover = $('section'); cover.className = 'slide cover';
  cover.innerHTML = '<h1>📰 ' + escapeHtml(report.date) + ' (' + escapeHtml(report.weekday || '') + ')</h1>'
    + '<p>오늘의 브리핑 · 총 ' + slides.length + '개 뉴스</p>'
    + '<div class="swipe-hint">옆으로 넘겨서 보기 →</div>';
  deck.appendChild(cover);

  slides.forEach((s, i) => {
    const sec = $('section'); sec.className = 'slide' + (s.points ? ' points' : '');
    let html = '<span class="cat-chip">' + escapeHtml(s.category || '') + '</span>';
    html += '<h2>' + escapeHtml(s.title) + '</h2>';
    html += '<div class="slide-text">' + renderBlocks(s.blocks) + '</div>';
    if(s.links.length){
      html += '<div class="links">' + s.links.map(u =>
        '<a class="linkbtn" href="' + escapeHtml(u) + '" target="_blank" rel="noopener">🔗 ' + escapeHtml(chipHost(u)) + '</a>'
      ).join('') + '</div>';
    }
    sec.innerHTML = html;
    deck.appendChild(sec);
  });

  const total = slides.length + 1;
  const fill = document.getElementById('progress-fill');
  const label = document.getElementById('progress-label');
  function updateProgress(){
    const i = Math.round(deck.scrollLeft / window.innerWidth);
    fill.style.width = ((i + 1) / total * 100) + '%';
    label.textContent = i === 0 ? '표지' : (i + ' / ' + slides.length);
  }
  deck.addEventListener('scroll', updateProgress, { passive: true });
  deck.scrollLeft = 0;
  updateProgress();

  document.onkeydown = (e) => {
    if(e.key === 'ArrowRight') deck.scrollBy({ left: window.innerWidth, behavior: 'smooth' });
    if(e.key === 'ArrowLeft') deck.scrollBy({ left: -window.innerWidth, behavior: 'smooth' });
  };
}

function loadDate(idx){
  if(idx < 0 || idx >= MANIFEST.length) return;
  dateIdx = idx;
  const report = MANIFEST[idx];
  buildShell();
  document.getElementById('datepill').innerHTML =
    escapeHtml(report.date) + '<span class="wd">(' + escapeHtml(report.weekday || '') + ')</span>';
  showMessage('불러오는 중…');
  fetch(mdUrl(report.date))
    .then(res => { if(!res.ok) throw new Error('HTTP ' + res.status); return res.text(); })
    .then(md => buildDeck(md, report))
    .catch(() => showMessage('브리핑을 불러오지 못했어요.<br>온라인 상태에서 다시 시도해 주세요.'));
}

if(!MANIFEST.length){
  renderEmpty();
} else {
  loadDate(0);
}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    sys.exit(build())
