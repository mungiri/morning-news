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
FNAME_RE = re.compile(r"뉴스스크랩_(\d{4})-(\d{2})-(\d{2})\.md$")
WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]


def collect_reports():
    reports = []
    for p in BASE.glob("뉴스스크랩_*.md"):
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
        # 첫 번째 # 제목 라인 추출 (없으면 날짜로 대체)
        title = next(
            (ln[2:].strip() for ln in md.splitlines() if ln.startswith("# ")),
            f"아침 뉴스 스크랩 — {date_str}",
        )
        reports.append(
            {"date": date_str, "weekday": weekday, "title": title, "markdown": md}
        )
    # 최신 날짜가 위로
    reports.sort(key=lambda r: r["date"], reverse=True)
    return reports


def build():
    reports = collect_reports()
    if not reports:
        print("⚠️  뉴스스크랩_*.md 파일을 찾지 못했어요. 폴더를 확인해 주세요.")
        return 1
    data_json = json.dumps(reports, ensure_ascii=False)
    built_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = (
        TEMPLATE
        .replace("__NEWS_DATA__", data_json)
        .replace("__BUILT_AT__", built_at)
    )
    out = BASE / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"✅ index.html 생성 완료 — 리포트 {len(reports)}건 (최근: {reports[0]['date']})")
    print(f"   파일 위치: {out}")
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
  .hero{padding:14px 4px 4px}
  .hero h1{font-size:clamp(26px,4vw,38px);font-weight:850;letter-spacing:-.6px;margin:0 0 6px}
  .hero p{color:var(--muted);margin:0;font-size:15px}
  .hsection-label{font-size:12.5px;font-weight:800;color:var(--muted);letter-spacing:.04em;
    margin:30px 4px 12px}
  .hgrid{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(248px,1fr))}
  .feat-grid{grid-template-columns:1fr}
  .hcard{text-align:left;background:var(--panel);border:1px solid var(--line);border-radius:16px;
    padding:18px 20px;cursor:pointer;font-family:inherit;color:var(--ink);box-shadow:var(--shadow);
    display:flex;flex-direction:column;gap:10px;
    transition:transform .12s ease,border-color .12s ease}
  .hcard:hover{transform:translateY(-2px);border-color:var(--brand)}
  .hcard.feat{background:var(--brand-soft);border-color:var(--brand)}
  .hcard-top{display:flex;align-items:center;gap:8px}
  .hcard-date{font-size:18px;font-weight:800;letter-spacing:-.3px}
  .hcard.feat .hcard-date{font-size:22px}
  .hcard-wd{font-size:13px;color:var(--muted);font-weight:600}
  .hcard-badge{margin-left:auto;background:var(--brand);color:#fff;font-size:11px;font-weight:800;
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
const REPORTS = __NEWS_DATA__;

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

// 날짜·요일·제목·본문 전체에서 검색
function matches(r, q){
  if(!q) return true;
  q = q.toLowerCase();
  return r.date.includes(q) || (r.weekday||'').includes(q)
      || r.title.toLowerCase().includes(q)
      || r.markdown.toLowerCase().includes(q);
}
function renderList(q){
  const ul = $('datelist'); ul.innerHTML = '';
  let shown = 0;
  REPORTS.forEach((r, i) => {
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
// 각 리포트에서 헤드라인(### N. 제목)을 n개 추출 — 홈 카드 미리보기용
function headlines(md, n){
  const out = [];
  for(const ln of md.split(/\r?\n/)){
    const m = ln.match(/^###\s+(.*)$/);
    if(m && !/오늘의 스크랩 포인트/.test(m[1])){
      out.push(m[1].replace(/^\d+\.\s*/, '').replace(/[*]/g, '').trim());
      if(out.length >= n) break;
    }
  }
  return out;
}
function homeCard(i, featured){
  const r = REPORTS[i];
  const peek = headlines(r.markdown, featured ? 5 : 3)
    .map(h => '<li>' + escapeHtml(h) + '</li>').join('');
  return '<button class="hcard' + (featured ? ' feat' : '') + '" data-i="' + i + '">'
    + '<div class="hcard-top"><span class="hcard-date">' + r.date + '</span>'
    + '<span class="hcard-wd">(' + (r.weekday||'') + ')</span>'
    + (featured ? '<span class="hcard-badge">최신</span>' : '')
    + '</div><ul class="hcard-peek">' + peek + '</ul>'
    + '<div class="hcard-go">브리핑 열기 →</div></button>';
}
function buildHome(){
  let h = '<div class="hero"><h1>📰 아침 뉴스 스크랩</h1>'
        + '<p>전력·전기직 취업 준비용 데일리 브리핑</p></div>';
  if(REPORTS.length){
    h += '<div class="hsection-label">오늘의 브리핑</div>'
       + '<div class="hgrid feat-grid">' + homeCard(0, true) + '</div>';
    if(REPORTS.length > 1){
      h += '<div class="hsection-label">지난 브리핑</div><div class="hgrid">';
      for(let i = 1; i < REPORTS.length; i++) h += homeCard(i, false);
      h += '</div>';
    }
  } else {
    h += '<p class="empty">아직 스크랩이 없어요.</p>';
  }
  const home = $('home');
  home.innerHTML = h;
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
function render(){
  $('content').innerHTML = renderMarkdown(REPORTS[current].markdown);
  highlight($('search').value.trim());
}
function select(i){
  current = i;
  $('home').hidden = true;
  $('content').hidden = false;
  render();
  renderList($('search').value.trim());
  window.scrollTo({top:0, behavior:'smooth'});
  location.hash = REPORTS[i].date;
}
function onSearch(){
  const q = $('search').value.trim();
  renderList(q);
  // 홈 화면에서 검색하면 첫 매칭 글로 이동
  if(current < 0){
    if(q){ const first = REPORTS.findIndex(r => matches(r, q)); if(first >= 0) select(first); }
    return;
  }
  // 보던 글이 검색과 안 맞으면 첫 매칭 글로, 맞으면 강조만 갱신
  if(q && !matches(REPORTS[current], q)){
    const first = REPORTS.findIndex(r => matches(r, q));
    if(first >= 0){ select(first); return; }
  }
  render();
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

// 데스크톱 접힘 상태 복원
try{
  if(localStorage.getItem('side-collapsed') === '1' && !MOBILE())
    document.body.classList.add('collapsed');
}catch(e){}

// 해시(#날짜)가 있으면 그 리포트로, 없으면 홈 화면으로 진입
const fromHash = REPORTS.findIndex(r => r.date === location.hash.slice(1));
if(fromHash >= 0) select(fromHash); else showHome();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    sys.exit(build())
