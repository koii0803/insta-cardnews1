# 전체확인 서버 — 루트의 전체확인열기.bat 가 실행한다. 사용자가 직접 만질 일 없음.
# 하는 일: 제작/ 안의 모든 폴더(폐기 제외)를 한 화면에 띄우고,
# 건별 폐기/발행 버튼의 실제 동작을 처리한다.
#   폐기 = 그 폴더를 제작/폐기/ 로 이동
#   발행 = 그 폴더의 카드 전부 PNG 촬영(실패 시 2회 재시도) → JPEG 변환 → Make 웹훅 전송(인스타 자동 게시) + 발행대장.txt 한 줄

import base64
import calendar
import html
import http.server
import io
import json
import re
import shutil
import subprocess
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from datetime import date, datetime, timedelta
from pathlib import Path

from PIL import Image

PORT = 8765
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ROOT = Path(__file__).resolve().parent.parent
제작 = ROOT / "제작"
웹훅 = (ROOT / "작업파일" / "webhook.txt").read_text(encoding="utf-8").strip()


def 폴더들():
    return sorted(p for p in 제작.iterdir() if p.is_dir() and p.name != "폐기")


def 카테고리(폴더):
    try:
        스펙 = json.loads((폴더 / "카드셋.json").read_text(encoding="utf-8"))
        if 스펙.get("카테고리"):
            return 스펙["카테고리"]
    except Exception:
        pass
    try:
        first = (폴더 / "대본.txt").read_text(encoding="utf-8").splitlines()[0]
        m = re.search(r"\[(.+?)\]", first)
        if m:
            return m.group(1)
    except Exception:
        pass
    return "미상"


def 마감일(폴더):
    try:
        스펙 = json.loads((폴더 / "카드셋.json").read_text(encoding="utf-8"))
        return 스펙.get("마감일")
    except Exception:
        return None


def 촬영(폴더):
    실패 = []
    for h in sorted(폴더.glob("카드*.html")):
        png = h.with_suffix(".png")
        ok = False
        for _ in range(3):
            subprocess.run([
                CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                "--window-size=1080,1350", "--virtual-time-budget=8000",
                f"--screenshot={png}", h.as_uri(),
            ], capture_output=True, timeout=60)
            if png.exists() and png.stat().st_size > 10000:
                ok = True
                break
        if not ok:
            실패.append(h.name)
    return 실패


def 전송(폴더):
    # PNG → JPEG(인스타 API는 JPEG만 받음) → base64 → Make 웹훅으로 한 번에 보낸다.
    # 성공하면 None, 실패하면 이유 문자열
    if not (폴더 / "캡션.txt").exists():
        return "캡션.txt 없음 → 캡션작성 먼저"
    # [대체텍스트] 줄은 인스타 캡션에 들어가면 안 되므로 뺀다
    줄들 = (폴더 / "캡션.txt").read_text(encoding="utf-8").splitlines()
    캡션 = chr(10).join(l for l in 줄들 if not l.startswith("[대체텍스트]")).strip()
    images = []
    for png in sorted(폴더.glob("카드*.png")):
        buf = io.BytesIO()
        Image.open(png).convert("RGB").save(buf, "JPEG", quality=85)
        images.append({"name": png.stem + ".jpg",
                       "data": base64.b64encode(buf.getvalue()).decode()})
    if not images:
        return "보낼 JPEG가 없음 (PNG 촬영 결과 없음)"
    body = json.dumps({"caption": 캡션, "count": len(images), "images": images}).encode()
    if len(body) > 4_500_000:
        return f"전송 용량 초과 ({len(body)//1_000_000}MB). 카드 수를 줄여야 함"
    req = urllib.request.Request(웹훅, body, {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            if r.status != 200:
                return f"Make 응답 {r.status}"
    except Exception as e:
        return f"Make 전송 실패: {e}"
    return None


# ── 예약발행 ──────────────────────────────────────────────
# 예약발행.json 에 [{"folder": 폴더명, "time": "2026-09-06T18:00"}] 형태로 저장.
# 서버가 20초마다 보고, 시간이 되면 발행 버튼과 똑같은 절차(촬영→전송→발행대장)를 실행한다.
# 서버가 꺼져 있던 사이 지난 예약은 서버를 다시 켠 순간 바로 실행된다.
예약파일 = ROOT / "예약발행.json"
예약잠금 = threading.Lock()


def 예약목록():
    try:
        return json.loads(예약파일.read_text(encoding="utf-8"))
    except Exception:
        return []


def 예약저장(목록):
    예약파일.write_text(json.dumps(목록, ensure_ascii=False, indent=1), encoding="utf-8")


def 예약실행(항목):
    폴더 = 제작 / 항목["folder"]
    today = date.today().isoformat()
    if not 폴더.is_dir():
        기록 = f"{today} 예약발행 취소: {항목['folder']} 폴더 없음(폐기됨?)\n"
    else:
        실패 = 촬영(폴더)
        if 실패:
            기록 = f"{today} 예약발행 PNG 촬영 실패: {폴더.name} {', '.join(실패)}\n"
        else:
            이유 = 전송(폴더)
            if 이유:
                기록 = f"{today} 예약발행 전송 실패: {폴더.name} {이유}\n"
            else:
                제목 = 폴더.name.split("_", 1)[-1]
                with (ROOT / "발행대장.txt").open("a", encoding="utf-8") as f:
                    f.write(f"{today} [{카테고리(폴더)}] {제목}\n")
                기록 = None
    if 기록:
        (ROOT / "오류기록.txt").open("a", encoding="utf-8").write(기록)


숨김파일 = ROOT / "숨김목록.json"


def 숨김목록():
    # 화면에서만 숨긴 폴더 이름들. 파일·발행에는 영향 없음
    try:
        return json.loads(숨김파일.read_text(encoding="utf-8"))
    except Exception:
        return []


깃큐파일 = ROOT / "깃허브예약.json"


def 깃큐목록():
    try:
        return json.loads(깃큐파일.read_text(encoding="utf-8"))
    except Exception:
        return []


def 깃(*args):
    r = subprocess.run(["git", "-C", str(ROOT), *args],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    return r.returncode, (r.stdout + r.stderr).strip()


def 깃푸시():
    # 깃허브 쪽에 발행 결과 커밋이 쌓여 있으면 그냥 push가 거부되므로 먼저 받아온다
    깃("pull", "--rebase", "--autostash")
    return 깃("push")


def 원격장부():
    # 깃허브 쪽 장부(예약큐·발행대장·오류기록)를 받아온다. 연결 실패면 None
    code, _ = 깃("fetch", "--quiet", "origin", "main")
    if code != 0:
        return None

    def 원격(파일):
        c, out = 깃("show", f"origin/main:{파일}")
        return out if c == 0 else ""

    try:
        큐 = json.loads(원격("깃허브예약.json"))
    except Exception:
        큐 = []
    return {"큐": 큐, "발행": 원격("발행대장.txt").splitlines(),
            "오류": 원격("오류기록.txt").splitlines()}


def 깃헙현황(장부):
    # 현황판 줄들 (⏳ 대기중 / ✅ 발행됨 / ❌ 실패)
    if 장부 is None:
        return ["깃허브 연결 안 됨 — 깃헙예약 상태 확인 불가"]
    줄 = [f"⏳ 대기중 {x['time'].replace('T', ' ')} — {x['folder'].split('_', 1)[-1]}"
          for x in 장부["큐"]]
    줄 += ["✅ " + l for l in 장부["발행"] if "(깃허브예약)" in l][-3:]
    줄 += ["❌ " + l for l in 장부["오류"] if "깃허브 예약발행" in l][-3:]
    return 줄 or ["깃헙예약 기록 없음"]


def 달력html(행사):
    # 행사: {"YYYY-MM-DD": [(정렬키, css, 글), ...]} → 이번 달 + 예약 걸린 달의 달력 표
    오늘 = date.today().isoformat()
    달들 = {오늘[:7]}
    달들 |= {날[:7] for 날 in 행사 if 날 >= 오늘}
    표들 = []
    for 달 in sorted(달들):
        년, 월 = int(달[:4]), int(달[5:7])
        첫요일, 일수 = calendar.monthrange(년, 월)
        줄, 주 = [], ["<td></td>"] * 첫요일
        for 일 in range(1, 일수 + 1):
            날 = f"{달}-{일:02d}"
            내용 = "".join(f'<span class="ev {css}">{html.escape(글)}</span>'
                           for _, css, 글 in sorted(행사.get(날, [])))
            주.append(f'<td data-date="{날}" class="{"today" if 날 == 오늘 else ""}">'
                      f'<span class="day">{일}</span>{내용}</td>')
            if len(주) == 7:
                줄.append("<tr>" + "".join(주) + "</tr>")
                주 = []
        if 주:
            줄.append("<tr>" + "".join(주 + ["<td></td>"] * (7 - len(주))) + "</tr>")
        표들.append(f"<h3>{년}년 {월}월</h3><table><tr>"
                    + "".join(f"<th>{요일}</th>" for 요일 in "월화수목금토일")
                    + "</tr>" + "".join(줄) + "</table>")
    return "".join(표들)


def 깃허브예약등록(폴더, t):
    # PNG 촬영 + JPEG 변환 + 예약 기록 + 깃허브 푸시. 성공 None, 실패 이유 문자열
    실패 = 촬영(폴더)
    if 실패:
        return f"PNG 촬영 실패: {', '.join(실패)}"
    for png in sorted(폴더.glob("카드*.png")):
        Image.open(png).convert("RGB").save(png.with_suffix(".jpg"), "JPEG", quality=85)
    목록 = [x for x in 깃큐목록() if x["folder"] != 폴더.name]
    목록.append({"folder": 폴더.name, "time": t})
    깃큐파일.write_text(json.dumps(목록, ensure_ascii=False, indent=1), encoding="utf-8")
    깃("add", "깃허브예약.json", f"제작/{폴더.name}", ".github", "작업파일/깃허브발행.py")
    깃("commit", "-m", f"깃허브예약: {폴더.name} {t}")
    code, out = 깃푸시()
    if code != 0:
        return f"깃허브 푸시 실패 — 저장소 연결부터 필요: {out[:160]}"
    return None


def 예약감시():
    while True:
        with 예약잠금:
            목록 = 예약목록()
            now = datetime.now().strftime("%Y-%m-%dT%H:%M")
            실행할 = [x for x in 목록 if x["time"] <= now]
            if 실행할:
                예약저장([x for x in 목록 if x["time"] > now])
        for 항목 in 실행할:
            예약실행(항목)
        time.sleep(20)


def 대시보드():
    장부 = 원격장부()
    if 장부:
        발행줄 = 장부["발행"]
    else:
        try:
            발행줄 = (ROOT / "발행대장.txt").read_text(encoding="utf-8").splitlines()
        except Exception:
            발행줄 = []

    부분, 처리부분 = [], []
    숨김 = 숨김목록()
    예약중 = {x["folder"]: "PC예약: " + x["time"].replace("T", " ") for x in 예약목록()}
    for x in (장부["큐"] if 장부 else 깃큐목록()):
        예약중[x["folder"]] = "깃헙예약: " + x["time"].replace("T", " ")
    for 폴더 in 폴더들():
        이름 = 폴더.name
        if 이름 in 숨김:
            continue
        제목 = 이름.split("_", 1)[-1]
        카드 = sorted(폴더.glob("카드*.html"))
        try:
            캡션 = (폴더 / "캡션.txt").read_text(encoding="utf-8")
        except Exception:
            캡션 = "(캡션 없음)"
        try:
            실험 = (폴더 / "대본.txt").read_text(encoding="utf-8").splitlines()[1]
        except Exception:
            실험 = ""
        마감 = 마감일(폴더)
        마감표시 = f'<span class="deadline">마감 {마감}</span>' if 마감 else ""
        틀 = "".join(
            f'<div class="card"><iframe loading="lazy" src="{urllib.parse.quote(이름)}/{c.name}"></iframe></div>'
            for c in 카드)
        조각 = f"""
<section class="set" data-folder="{html.escape(이름)}" data-deadline="{html.escape(마감 or '')}">
  <h2>{html.escape(제목)} <small>({카테고리(폴더)}, {len(카드)}장)</small> {마감표시}</h2>
  <div class="tag">{html.escape(실험)}</div>
  <div class="cards">{틀}</div>
  <details><summary>캡션 보기</summary><div class="caption">{html.escape(캡션)}</div></details>
  <div class="rowbtns">
    <button class="discard">폐기</button>
    <button class="publish">발행</button>
    <input type="datetime-local" class="when">
    <button class="schedule">PC예약</button>
    <button class="ghschedule">깃헙예약</button>
    <span class="booked">{html.escape(예약중.get(이름, ""))}</span>
    <button class="cancel" {"" if 이름 in 예약중 else "hidden"}>예약취소</button>
    <button class="delete">삭제</button>
    <span class="result"></span>
  </div>
</section>"""
        처리 = 이름 in 예약중 or any(
            re.search(rf"\] {re.escape(제목)}( \(|$)", l) for l in 발행줄)
        (처리부분 if 처리 else 부분).append(조각)

    개수 = len(부분)
    본문 = "\n".join(부분) if 부분 else "<p>확인할 건이 없습니다.</p>"
    현황 = [f"⏳ 대기중 {x['time'].replace('T', ' ')} — {x['folder'].split('_', 1)[-1]} (PC예약)"
            for x in 예약목록()] + 깃헙현황(장부)
    현황판 = "<br>".join(html.escape(l) for l in 현황)

    행사 = {}
    for x in 예약목록() + (장부["큐"] if 장부 else 깃큐목록()):
        날, 시간 = x["time"].split("T")
        행사.setdefault(날, []).append((시간, "pend", f"⏳{시간} {x['folder'].split('_', 1)[-1]}"))
    for l in 발행줄:
        m = re.match(r"(\d{4}-\d{2}-\d{2}) (?:\[[^\]]*\] )?(.+)", l)
        if m:
            행사.setdefault(m.group(1), []).append(("", "done", "✅" + m.group(2)))
    달력 = 달력html(행사)
    행사수 = json.dumps({날: len(v) for 날, v in 행사.items()})

    # 최근 3일 예약발행 실패는 맨 위에 빨간 배너로 크게 보여준다
    오류줄 = 장부["오류"] if 장부 else []
    try:
        오류줄 = list(dict.fromkeys(
            오류줄 + (ROOT / "오류기록.txt").read_text(encoding="utf-8").splitlines()))
    except Exception:
        pass
    기준 = (date.today() - timedelta(days=3)).isoformat()
    최근실패 = [l for l in 오류줄 if "예약발행" in l and l[:10] >= 기준]
    배너 = ("" if not 최근실패 else
            '<div class="alert">⚠ 최근 3일 안에 예약발행 실패가 있다<br>'
            + "<br>".join(html.escape(l) for l in 최근실패) + "</div>")
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>전체확인 — 대기 {개수}건</title>
<style>
  body {{ margin:0; font-family:'Malgun Gothic',sans-serif; background:#0F1113; color:#1A1A1A; }}
  h1 {{ color:#F2F4F6; }}
  .wrap > p {{ color:#F2F4F6; }}
  .alert {{ background:#C0392B; color:#FFF; border-radius:10px; padding:14px 20px; margin-bottom:16px; font-size:15px; font-weight:700; line-height:1.8; }}
  .wrap {{ max-width:1200px; margin:0 auto; padding:32px 24px 80px; }}
  h1 {{ font-size:26px; }}
  .topbar {{ display:flex; justify-content:space-between; align-items:flex-start; gap:20px; flex-wrap:wrap; }}
  .board {{ background:#FFF; border:1px solid #CCC; border-radius:10px; padding:12px 18px; font-size:14px; line-height:1.9; min-width:300px; }}
  .board b {{ font-size:15px; }}
  .board .refresh {{ font-size:13px; font-weight:400; padding:3px 12px; background:#E9ECEF; margin-left:10px; }}
  .cal {{ background:#FFF; border:1px solid #CCC; border-radius:10px; padding:6px 20px 18px; margin-top:20px; }}
  .cal h3 {{ font-size:17px; margin:14px 0 8px; }}
  .cal table {{ border-collapse:collapse; width:100%; table-layout:fixed; }}
  .cal th {{ font-size:13px; color:#667; font-weight:400; padding:4px; }}
  .cal td {{ border:1px solid #E2E4E8; vertical-align:top; height:56px; padding:3px 6px; font-size:12px; }}
  .cal .day {{ display:block; font-weight:700; color:#99A; }}
  .cal td[data-date] {{ cursor:pointer; }}
  .cal td.picked {{ outline:2px solid #0E7C86; outline-offset:-2px; }}
  .cal .today {{ background:#EAF6F7; }}
  .cal .today .day {{ color:#0E7C86; }}
  .cal .ev {{ display:block; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .cal .pend {{ color:#B26A00; font-weight:700; }}
  .cal .done {{ color:#0E7C86; }}
  .donebox {{ background:#E8ECEF; border:1px solid #C5CCD3; border-radius:10px; padding:14px 20px; margin-top:20px; }}
  .donebox summary {{ cursor:pointer; font-size:16px; font-weight:700; }}
  #donearea .set {{ background:#F4F1E8; border-color:#D8D2BE; opacity:1; }}
  #donearea .set h2::after {{ content:" ✔ 처리됨"; color:#8A7B4F; font-size:14px; }}
  .set .delete {{ display:none; background:#C0392B; color:#FFF; }}
  #donearea .set .delete {{ display:inline-block; }}
  .hint {{ background:#FFF; border:1px solid #DDD; padding:14px 20px; font-size:16px; line-height:1.8; }}
  .set {{ background:#FFF; border:1px solid #CCC; border-radius:10px; padding:20px; margin:24px 0; }}
  .set.done {{ opacity:0.45; }}
  h2 {{ font-size:22px; margin:0 0 6px; }}
  h2 small {{ color:#667; font-weight:400; }}
  .deadline {{ background:#FFF3CD; border:1px solid #E6C860; padding:2px 10px; font-size:14px; font-weight:700; }}
  .tag {{ color:#667; font-size:14px; margin-bottom:12px; }}
  .cards {{ display:flex; flex-wrap:wrap; gap:14px; }}
  .card {{ width:346px; height:432px; overflow:hidden; border:1px solid #CCC; background:#FFF; }}
  .card iframe {{ width:1080px; height:1350px; transform:scale(0.32); transform-origin:0 0; border:0; pointer-events:none; }}
  details {{ margin-top:12px; font-size:15px; }}
  .caption {{ white-space:pre-wrap; background:#F7F8FA; border:1px solid #E2E4E8; padding:14px; line-height:1.7; }}
  .rowbtns {{ display:flex; gap:10px; align-items:center; margin-top:14px; }}
  button {{ font-size:18px; font-weight:700; padding:10px 28px; border:0; cursor:pointer; border-radius:8px; }}
  .discard {{ background:#E9ECEF; color:#333; }}
  .publish {{ background:#0E7C86; color:#FFF; }}
  .result {{ font-size:15px; font-weight:700; color:#0E7C86; white-space:pre-wrap; }}
</style>
</head>
<body>
<div class="wrap">
  {배너}
  <div class="topbar">
    <h1>전체확인 — 대기 {개수}건</h1>
    <div class="board"><b>예약 현황</b><button class="refresh">새로고침</button><br>{현황판}</div>
  </div>
  <div class="hint">위에서부터 보면서 건마다 폐기 또는 발행을 누르면 됩니다.<br>
  확인할 것: 오탈자 / 글자 잘림 / 사진 어울림 / 마감일. 폐기는 바로 안 지워지고 제작/폐기/ 로 이동합니다.</div>
  <div class="cal">{달력}</div>
  <details class="donebox">
    <summary id="donesum">처리된 항목 {len(처리부분)}건 — 발행·예약된 것 (누르면 펼침)</summary>
    <div id="donearea">{"".join(처리부분)}</div>
  </details>
  {본문}
</div>
<script>
const 행사수 = {행사수};
document.querySelector(".board .refresh").onclick = () => location.reload();
document.querySelectorAll(".cal td[data-date]").forEach(td => {{
  td.onclick = () => {{
    const 날 = td.dataset.date;
    document.querySelectorAll(".when").forEach(i => {{
      const 시간 = i.value.includes("T") ? i.value.split("T")[1] : "09:00";
      i.value = 날 + "T" + 시간;
    }});
    document.querySelectorAll(".cal td.picked").forEach(x => x.classList.remove("picked"));
    td.classList.add("picked");
  }};
}});
const donearea = document.getElementById("donearea");
const donesum = document.getElementById("donesum");
function 처리개수갱신() {{
  donesum.textContent = "처리된 항목 " + donearea.querySelectorAll(".set").length +
    "건 — 발행·예약된 것 (누르면 펼침)";
}}
document.querySelectorAll(".set").forEach(set => {{
  const folder = set.dataset.folder;
  const deadline = set.dataset.deadline;
  const result = set.querySelector(".result");
  function send(action, extra, keep, 성공후) {{
    result.textContent = "처리 중…";
    fetch("/", {{ method: "POST", body: JSON.stringify(Object.assign({{ folder, action }}, extra || {{}})) }})
      .then(r => r.json())
      .then(d => {{
        result.textContent = d.msg;
        if (!keep) set.classList.add("done");
        if (d.ok && 성공후) {{ 성공후(); 처리개수갱신(); }}
      }})
      .catch(() => alert("서버 연결이 끊겼습니다. 전체확인열기.bat 로 다시 여세요."));
  }}
  const 상자로 = () => donearea.appendChild(set);
  set.querySelector(".discard").onclick = () => {{
    if (confirm(folder + "\\n정말 폐기할까? (제작/폐기/ 로 이동)")) send("폐기");
  }};
  set.querySelector(".publish").onclick = () => {{
    if (deadline && new Date().toISOString().slice(0, 10) > deadline &&
        !confirm("경고: 마감일(" + deadline + ")이 지났다. 그래도 발행할까?")) return;
    const 오늘 = new Date().toISOString().slice(0, 10);
    if ((행사수[오늘] || 0) > 0 &&
        !confirm("오늘 이미 발행·예약이 " + 행사수[오늘] + "건 있다. 그래도 발행할까?")) return;
    send("발행", null, false, 상자로);
  }};
  function reserve(action, label) {{
    const t = set.querySelector(".when").value;
    if (!t) {{ alert("예약 시간을 먼저 고르세요."); return; }}
    if (deadline && t.slice(0, 10) > deadline &&
        !confirm("경고: 예약 시각이 마감일(" + deadline + ") 뒤다. 그래도 예약할까?")) return;
    const 날 = t.slice(0, 10);
    if ((행사수[날] || 0) > 0 &&
        !confirm(날 + " 에 이미 발행·예약이 " + 행사수[날] + "건 있다. 그래도 예약할까?")) return;
    send(action, {{ time: t }}, true, () => {{
      set.querySelector(".booked").textContent = label + ": " + t.replace("T", " ");
      set.querySelector(".cancel").hidden = false;
      상자로();
    }});
  }}
  set.querySelector(".schedule").onclick = () => reserve("예약", "PC예약");
  set.querySelector(".ghschedule").onclick = () => reserve("깃헙예약", "깃헙예약");
  set.querySelector(".cancel").onclick = () => {{
    send("예약취소", null, true);
    set.querySelector(".booked").textContent = "";
    set.querySelector(".cancel").hidden = true;
  }};
  set.querySelector(".delete").onclick = () => {{
    if (confirm(folder + "\\n화면에서 지울까? (파일·발행에는 영향 없음)"))
      send("숨김", null, true, () => set.remove());
  }};
}});
</script>
</body>
</html>"""


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(제작), **kw)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = 대시보드().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(n))
        act = req.get("action")
        폴더 = 제작 / req.get("folder", "")
        today = date.today().isoformat()

        if not 폴더.is_dir() or 폴더.parent != 제작 or 폴더.name == "폐기":
            msg = "잘못된 폴더 요청"
        elif act == "폐기":
            dest = 제작 / "폐기" / 폴더.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(폴더), str(dest))
            with 예약잠금:
                예약저장([x for x in 예약목록() if x["folder"] != 폴더.name])
            msg = f"폐기 완료 → 제작/폐기/{폴더.name}"
        elif act == "예약":
            t = req.get("time", "")
            if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$", t):
                msg = "예약 시간이 이상함. 다시 고르세요"
            elif t <= datetime.now().strftime("%Y-%m-%dT%H:%M"):
                msg = "지나간 시간엔 예약 못 함"
            elif not (폴더 / "캡션.txt").exists():
                msg = "캡션.txt가 없어서 예약 못 함. 캡션작성 먼저"
            else:
                with 예약잠금:
                    목록 = [x for x in 예약목록() if x["folder"] != 폴더.name]
                    목록.append({"folder": 폴더.name, "time": t})
                    예약저장(목록)
                msg = f"예약됨 → {t.replace('T', ' ')} 에 자동 발행. 그때까지 이 검은 창(서버)을 켜두세요"
        elif act == "깃헙예약":
            t = req.get("time", "")
            if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$", t):
                msg = "예약 시간이 이상함. 다시 고르세요"
            elif t <= datetime.now().strftime("%Y-%m-%dT%H:%M"):
                msg = "지나간 시간엔 예약 못 함"
            elif not (폴더 / "캡션.txt").exists():
                msg = "캡션.txt가 없어서 예약 못 함. 캡션작성 먼저"
            else:
                이유 = 깃허브예약등록(폴더, t)
                if 이유:
                    msg = f"깃헙예약 실패: {이유}"
                else:
                    msg = (f"깃헙예약됨 → {t.replace('T', ' ')} 무렵 자동 발행 (PC 꺼도 됨). "
                           "깃허브 사정에 따라 몇 분 늦을 수 있음")
        elif act == "숨김":
            목록 = 숨김목록()
            if 폴더.name not in 목록:
                목록.append(폴더.name)
            숨김파일.write_text(json.dumps(목록, ensure_ascii=False, indent=1), encoding="utf-8")
            msg = "화면에서 숨김 (파일은 제작/ 에 그대로)"
        elif act == "예약취소":
            with 예약잠금:
                예약저장([x for x in 예약목록() if x["folder"] != 폴더.name])
            msg = "예약 취소됨"
            깃목록 = 깃큐목록()
            if any(x["folder"] == 폴더.name for x in 깃목록):
                깃큐파일.write_text(json.dumps(
                    [x for x in 깃목록 if x["folder"] != 폴더.name],
                    ensure_ascii=False, indent=1), encoding="utf-8")
                깃("add", "깃허브예약.json")
                깃("commit", "-m", f"깃헙예약 취소: {폴더.name}")
                code, out = 깃푸시()
                if code != 0:
                    msg = "예약 취소됨 (단, 깃허브 반영 실패 — 푸시 안 됨)"
        elif act == "발행" and not list(폴더.glob("카드*.html")):
            msg = "이 폴더엔 발행할 카드가 없습니다 (옛 형식). 폐기하거나 다시 제작하세요"
        elif act == "발행" and not (폴더 / "캡션.txt").exists():
            msg = "캡션.txt가 없어서 발행 못 함. 캡션작성 먼저"
        elif act == "발행":
            실패 = 촬영(폴더)
            if 실패:
                (ROOT / "오류기록.txt").open("a", encoding="utf-8").write(
                    f"{today} PNG 촬영 3회 실패: {폴더.name} {실패}\n")
                msg = f"PNG 촬영 실패: {', '.join(실패)}. 오류기록에 적음. 발행 중단"
            else:
                이유 = 전송(폴더)
                if 이유:
                    (ROOT / "오류기록.txt").open("a", encoding="utf-8").write(
                        f"{today} 발행 전송 실패: {폴더.name} {이유}\n")
                    msg = f"인스타 전송 실패: {이유}. 오류기록에 적음 (발행대장엔 기록 안 함)"
                else:
                    제목 = 폴더.name.split("_", 1)[-1]
                    with (ROOT / "발행대장.txt").open("a", encoding="utf-8") as f:
                        f.write(f"{today} [{카테고리(폴더)}] {제목}\n")
                    msg = f"발행 완료 → Make 웹훅으로 전송됨 ({폴더.name}). 발행대장 기록됨"
        else:
            msg = "알 수 없는 요청"

        ok = not any(k in msg for k in
                     ("실패", "못 함", "이상함", "잘못", "없습니다", "알 수 없는"))
        body = json.dumps({"msg": msg, "ok": ok}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def 내_주소():
    # 같은 와이파이의 폰에서 접속할 때 쓸 PC 주소
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "PC-IP"


if __name__ == "__main__":
    threading.Thread(target=예약감시, daemon=True).start()
    webbrowser.open(f"http://localhost:{PORT}/")
    print("전체확인 화면을 브라우저에 띄웠다. 확인이 끝나면 이 검은 창은 닫아라.")
    print(f"폰(같은 와이파이)에서는 브라우저에 이 주소:  http://{내_주소()}:{PORT}/")
    http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
