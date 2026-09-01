# 카드 생성기 — 제작 폴더의 카드셋.json 을 읽어 카드NN.html 을 만든다. (확인은 루트의 전체확인열기.bat)
# 실행: python 카드생성.py "제작/날짜_제목"
#
# 카드셋.json 형식:
# {
#   "카테고리": "반전상식", "라벨": "반전 상식", "테마": "standard",
#   "마감일": null 또는 "2026-12-31",
#   "카드": [
#     {"유형":"표지", "사진":"배경사진1.jpg", "배지":"뱃지글", "제목":"큰 글", "부제":"작은 글 (\n 줄바꿈)"},
#     {"유형":"본문", "번호":"01", "소제목":"...", "줄":["문장1","문장2"]},
#     {"유형":"본문표", "번호":"02", "소제목":"...", "행":[["라벨","값"],...]},
#     {"유형":"강조", "사진":null, "제목":"큰 글", "부제":"작은 글"},
#     {"유형":"목록", "번호":"03", "소제목":"...", "행":[["왼쪽","오른쪽"],...], "박스":"밑 강조 한 줄"}
#   ]
# }
# 사진이 있으면 그 카드는 사진 배경(어두운 막 0.90) + 흰 글자가 된다.

import json
import re
import sys
from pathlib import Path


def 제목크기(제목):
    # 표지 제목 글자수 → 10자 이하 132 / 11~20자 104 / 21자 이상 84 (스킬 규격)
    n = len(re.sub(r"<[^>]+>", "", 제목 or "").replace("\n", "").replace(" ", ""))
    return 132 if n <= 10 else 104 if n <= 20 else 84

# 글씨체는 도현 단일 (2026-09-01 사용자 확정)
글씨체표 = {"도현": "Do Hyeon"}


def 폰트(c):
    이름 = c.get("글씨체", "도현")
    if 이름 not in 글씨체표:
        raise SystemExit(f"허용 안 된 글씨체: {이름} (허용: {', '.join(글씨체표)})")
    fam = 글씨체표[이름]
    return fam.replace(" ", "+"), fam


테마 = {
    "alert":    {"bg": "#FFF1CE", "ink": "#171512", "sub": "#6B6255", "accent": "#E04A2F", "on": "#FFFFFF", "line": "#E4D6B0", "surface": "#FFFFFF"},
    "standard": {"bg": "#F2ECE1", "ink": "#16130E", "sub": "#6A6154", "accent": "#B0202B", "on": "#FFFFFF", "line": "#DDD2BF", "surface": "#FFFFFF"},
    "test":     {"bg": "#EBE2FF", "ink": "#1C1533", "sub": "#635C7A", "accent": "#7A3BED", "on": "#FFFFFF", "line": "#D6C9F5", "surface": "#FFFFFF"},
    "benefit":  {"bg": "#DDEFF7", "ink": "#0A2130", "sub": "#4E6B7A", "accent": "#0E7C86", "on": "#FFFFFF", "line": "#BFDDE9", "surface": "#FFFFFF"},
    "soft":     {"bg": "#F7F3EC", "ink": "#211E19", "sub": "#867E70", "accent": "#E96D3F", "on": "#FFFFFF", "line": "#E7DECD", "surface": "#FFFFFF"},
}

머리 = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={폰트링크}&display=swap">
<style>body{{margin:0;}}</style>
</head>
<body>
<div style="width:1080px;height:1350px;box-sizing:border-box;{배경}color:{잉크};display:flex;flex-direction:column;padding:90px 80px 100px;font-family:'Do Hyeon','Malgun Gothic',sans-serif;">
  <div style="display:flex;align-items:center;gap:18px;flex-shrink:0;">
    <div style="width:18px;height:18px;background:{점}"></div>
    <div style="font-size:30px;font-weight:600;letter-spacing:0.14em;color:{보조};">{라벨}</div>
  </div>
  <div style="flex-grow:1;display:flex;flex-direction:column;justify-content:{세로};gap:40px;padding:56px 0;">
"""

세로표 = {"상": "flex-start", "중": "center", "하": "flex-end"}

꼬리 = """  </div>
  <div style="display:flex;justify-content:space-between;align-items:center;font-size:28px;font-weight:500;color:{보조};flex-shrink:0;border-top:2px solid {줄};padding-top:26px;">
    <div>@계정명</div>
    <div>{쪽} / {전체}</div>
  </div>
</div>
</body>
</html>
"""


def 줄바꿈(s):
    return (s or "").replace("\n", "<br>")


def 표지사진html(c, t, 쪽, 전체):
    # 밝은 표지: 사진을 그대로 밝게 보여주고, 하단 어두운 띠 위에 글자를 얹는다
    사진 = c["사진"]
    폰트링크, 폰트명 = 폰트(c)
    h = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={폰트링크}&display=swap">
<style>body{{margin:0;}}</style>
</head>
<body>
<div style="width:1080px;height:1350px;box-sizing:border-box;position:relative;background:url('{사진}') center/cover no-repeat;font-family:'{폰트명}','Malgun Gothic',sans-serif;overflow:hidden;">
  <div style="position:absolute;left:0;right:0;bottom:0;height:62%;background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,0.55) 45%,rgba(0,0,0,0.88) 100%);"></div>
  <div style="position:absolute;left:80px;right:80px;bottom:100px;color:#FFFFFF;display:flex;flex-direction:column;gap:30px;">
"""
    if c.get("배지"):
        배지색 = c.get("배지색", t["accent"])  # 색 로테이션 (2026-09-02): 세트마다 배지색 교체 가능
        h += f'<div style="display:inline-flex;align-self:flex-start;background:{배지색};color:{t["on"]};font-size:34px;font-weight:700;padding:14px 30px;">{c["배지"]}</div>\n'
    크기 = 제목크기(c["제목"])
    if c.get("외곽선"):
        내용 = 줄바꿈(c["제목"])
        h += f'''<div style="position:relative;font-family:'{폰트명}','Malgun Gothic',sans-serif;font-weight:400;letter-spacing:-0.02em;font-size:{크기}px;line-height:1.18;">
  <div style="position:absolute;inset:0;-webkit-text-stroke:18px #FFFFFF;text-shadow:0 6px 22px rgba(0,0,0,0.35);">{내용}</div>
  <div style="position:relative;">{내용}</div>
</div>
'''
    else:
        h += f'<div style="font-family:\'{폰트명}\',\'Malgun Gothic\',sans-serif;font-weight:400;letter-spacing:-0.02em;font-size:{크기}px;line-height:1.14;text-shadow:0 4px 24px rgba(0,0,0,0.45);">{줄바꿈(c["제목"])}</div>\n'
    if c.get("부제"):
        h += f'<div style="font-size:44px;line-height:1.5;color:rgba(255,255,255,0.88);text-shadow:0 2px 14px rgba(0,0,0,0.55);">{줄바꿈(c["부제"])}</div>\n'
    if c.get("꼬리", True):
        h += f"""    <div style="display:flex;justify-content:space-between;align-items:center;font-size:28px;font-weight:500;color:rgba(255,255,255,0.75);border-top:2px solid rgba(255,255,255,0.30);padding-top:24px;">
      <div>@계정명</div>
      <div>{쪽:02d} / {전체:02d}</div>
    </div>
"""
    h += """  </div>
</div>
</body>
</html>
"""
    return h


def 셀럽픽html(c, t):
    # 벤치마킹 계정 재현: 사진 전체 배경 + 하단 그라데이션 + 좌하단 제품컷 + 우하단 텍스트
    폰트링크, 폰트명 = 폰트(c)
    위치 = c.get("사진위치", "center")
    h = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={폰트링크}&display=swap">
<style>body{{margin:0;}}</style>
</head>
<body>
<div style="width:1080px;height:1350px;box-sizing:border-box;position:relative;background:url('{c["사진"]}') {위치}/cover no-repeat;font-family:'Do Hyeon','Malgun Gothic',sans-serif;overflow:hidden;">
  <div style="position:absolute;left:0;right:0;bottom:0;height:55%;background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,0.55) 50%,rgba(0,0,0,0.85) 100%);"></div>
  <div style="position:absolute;left:80px;right:80px;bottom:100px;display:flex;align-items:flex-end;justify-content:space-between;gap:40px;">
    <div style="flex-shrink:0;width:300px;display:flex;flex-direction:column;gap:18px;">
      <div style="background:#FFFFFF;border-radius:18px;padding:18px;"><img src="{c["제품사진"]}" style="width:100%;display:block;border-radius:10px;"></div>
      <div style="display:flex;flex-direction:column;gap:10px;align-items:flex-start;">
        <div style="background:{t["accent"]};color:#FFF;font-size:26px;font-weight:700;padding:8px 18px;border-radius:8px;">{c["브랜드"]}</div>
        <div style="background:#FFFFFF;color:#111;font-size:28px;font-weight:700;padding:10px 18px;border-radius:8px;">{c["제품명"]}</div>
      </div>
    </div>
    <div style="text-align:right;color:#FFFFFF;display:flex;flex-direction:column;gap:22px;">
      <div style="font-family:'{폰트명}','Malgun Gothic',sans-serif;font-size:52px;">{c["픽"]}</div>
      <div style="font-size:33px;line-height:1.65;color:rgba(255,255,255,0.94);">{"<br>".join(c["줄"])}</div>
    </div>
  </div>
</div>
</body>
</html>
"""
    return h


def 꿀팁html(c, t):
    # 스타일 3: 사진 전체 배경 + 어두운 그라데이션 + 아이콘 제목 + 색 강조 불릿 (제목·줄에 HTML 스팬 허용)
    # 텍스트 안전 사각형 (2026-09-02 사용자 확정): 표지와 같은 좌우 80 / 상 90 / 하 100 박스 안에만 글자.
    # 카드마다 "세로위치": "상" 또는 "하"(기본) — 위에 두면 그라데이션도 위가 어둡게 뒤집힌다.
    폰트링크, 폰트명 = 폰트(c)
    위치 = c.get("사진위치", "center")
    불릿 = "".join(
        f'<div style="display:flex;gap:16px;align-items:flex-start;">'
        f'<div style="font-size:20px;line-height:2.6;">●</div>'
        f'<div style="font-size:33px;font-weight:600;line-height:1.6;">{x}</div></div>' for x in c["줄"])
    if c.get("세로위치") == "상":
        막 = "linear-gradient(0deg,rgba(0,0,0,0.15) 0%,rgba(0,0,0,0.30) 40%,rgba(0,0,0,0.72) 62%,rgba(0,0,0,0.90) 100%)"
        붙임 = "top:90px;"
    else:
        막 = "linear-gradient(180deg,rgba(0,0,0,0.15) 0%,rgba(0,0,0,0.30) 40%,rgba(0,0,0,0.72) 62%,rgba(0,0,0,0.90) 100%)"
        붙임 = "bottom:100px;"
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={폰트링크}&display=swap">
<style>body{{margin:0;}}</style>
</head>
<body>
<div style="width:1080px;height:1350px;box-sizing:border-box;position:relative;background:url('{c["사진"]}') {위치}/cover no-repeat;font-family:'{폰트명}','Malgun Gothic',sans-serif;overflow:hidden;">
  <div style="position:absolute;inset:0;background:{막};"></div>
  <div style="position:absolute;left:80px;right:80px;{붙임}color:#FFFFFF;display:flex;flex-direction:column;gap:38px;">
    <div style="font-family:'{폰트명}','Malgun Gothic',sans-serif;font-size:66px;line-height:1.2;">{(c.get("아이콘") + " ") if c.get("아이콘") else ""}{c["제목"]}</div>
    <div style="display:flex;flex-direction:column;gap:30px;">{불릿}</div>
  </div>
</div>
</body>
</html>
"""


def 카드html(c, t, 쪽, 전체):
    사진 = c.get("사진")
    if c["유형"] == "셀럽픽":
        return 셀럽픽html(c, t)
    if c["유형"] == "꿀팁":
        return 꿀팁html(c, t)
    if 사진 and c["유형"] == "표지":
        return 표지사진html(c, t, 쪽, 전체)
    if 사진:
        배경 = f"background:linear-gradient(rgba(7,18,22,0.90),rgba(7,18,22,0.90)),url('{사진}') center/cover no-repeat;"
        잉크, 보조, 줄, 강조색, 강조글 = "#FFFFFF", "rgba(255,255,255,0.78)", "rgba(255,255,255,0.32)", "#4FD1DB", "#07161A"
    elif c["유형"] == "강조":
        배경 = f"background:{t['accent']};"
        잉크, 보조, 줄, 강조색, 강조글 = t["on"], "rgba(255,255,255,0.80)", "rgba(255,255,255,0.32)", t["on"], t["accent"]
    else:
        배경 = f"background:{t['bg']};"
        잉크, 보조, 줄, 강조색, 강조글 = t["ink"], t["sub"], t["line"], t["accent"], t["on"]

    폰트링크, 폰트명 = 폰트(c)
    h = 머리.format(배경=배경, 잉크=잉크, 점=f"{강조색};", 보조=보조, 라벨=c.get("라벨", ""), 폰트링크=폰트링크,
                   세로=세로표.get(c.get("세로위치", "중"), "center"))
    u = c["유형"]

    if u in ("표지", "강조"):
        if c.get("배지"):
            h += f'<div style="display:inline-flex;align-self:flex-start;background:{강조색};color:{강조글};font-size:34px;font-weight:700;padding:16px 32px;">{c["배지"]}</div>\n'
        크기 = {"표지": 104, "강조": 112}[u]
        h += f'<div style="font-family:\'{폰트명}\',\'Malgun Gothic\',sans-serif;font-weight:400;letter-spacing:-0.02em;font-size:{크기}px;line-height:1.14;">{줄바꿈(c["제목"])}</div>\n'
        h += f'<div style="width:200px;height:14px;background:{강조색};"></div>\n'
        if c.get("부제"):
            h += f'<div style="font-size:44px;line-height:1.55;color:{보조};">{줄바꿈(c["부제"])}</div>\n'

    elif u in ("본문", "본문표", "목록"):
        h += '<div style="display:flex;align-items:baseline;gap:24px;">\n'
        if c.get("번호"):
            h += f'<div style="font-size:72px;font-weight:700;color:{강조색};">{c["번호"]}</div>\n'
        h += f'<div style="font-size:52px;font-weight:700;line-height:1.25;">{c["소제목"]}</div>\n</div>\n'

        if u == "본문":
            내용 = f'<div style="height:2px;background:{줄};"></div>'.join(
                f'<div style="font-size:44px;font-weight:600;line-height:1.5;">{줄바꿈(x)}</div>' for x in c["줄"])
            h += f'<div style="background:{t["surface"]};color:{t["ink"]};padding:48px 40px;display:flex;flex-direction:column;gap:28px;">{내용}</div>\n'
        elif u == "본문표":
            내용 = f'<div style="height:2px;background:{줄};"></div>'.join(
                f'<div style="display:flex;gap:28px;align-items:baseline;">'
                f'<div style="font-size:32px;font-weight:600;color:{t["sub"]};min-width:150px;">{a}</div>'
                f'<div style="font-size:38px;font-weight:600;line-height:1.35;">{줄바꿈(b)}</div></div>' for a, b in c["행"])
            h += f'<div style="background:{t["surface"]};color:{t["ink"]};padding:40px;display:flex;flex-direction:column;gap:24px;">{내용}</div>\n'
        else:
            내용 = "".join(
                f'<div style="background:{t["surface"]};color:{t["ink"]};padding:32px 40px;display:flex;justify-content:space-between;align-items:center;gap:20px;">'
                f'<div style="font-size:38px;font-weight:700;">{a}</div>'
                f'<div style="font-size:32px;color:{t["sub"]};">{b}</div></div>' for a, b in c["행"])
            h += f'<div style="display:flex;flex-direction:column;gap:16px;">{내용}</div>\n'
            if c.get("박스"):
                h += f'<div style="background:{t["accent"]};color:{t["on"]};padding:40px;font-size:44px;font-weight:700;line-height:1.4;">{줄바꿈(c["박스"])}</div>\n'

    if not c.get("꼬리", True):
        return h + "  </div>\n</div>\n</body>\n</html>\n"
    return h + 꼬리.format(보조=보조, 줄=줄, 쪽=f"{쪽:02d}", 전체=f"{전체:02d}")


if __name__ == "__main__":
    폴더 = Path(sys.argv[1]).resolve()
    스펙 = json.loads((폴더 / "카드셋.json").read_text(encoding="utf-8"))
    t = 테마[스펙["테마"]]
    카드들 = 스펙["카드"]
    전체 = len(카드들)
    # 로컬 도현 폰트를 모든 카드에 심는다 (구글 폰트 로드 실패/지연 시에도 항상 도현이 뜨게)
    폰트경로 = (Path(__file__).parent / "DoHyeon.ttf").resolve().as_posix()
    로컬폰트 = f"<style>@font-face{{font-family:'Do Hyeon';src:url('file:///{폰트경로}') format('truetype');}}</style>\n<style>"
    for i, c in enumerate(카드들, 1):
        c.setdefault("라벨", 스펙["라벨"])
        c.setdefault("꼬리", 스펙.get("꼬리", False))
        c.setdefault("글씨체", 스펙.get("글씨체", "도현"))
        h = 카드html(c, t, i, 전체).replace("<style>", 로컬폰트, 1)
        (폴더 / f"카드{i:02d}.html").write_text(h, encoding="utf-8")
    print(f"완료: 카드 {전체}장 → {폴더}  (확인은 루트의 전체확인열기.bat)")
