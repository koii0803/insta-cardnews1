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
# 예외: 스타일 8~18 전용 폰트 (2026-09-04 사용자 승인 — 카드제작 스킬 4-3절)
글씨체표 = {"도현": "Do Hyeon"}

# 스타일 8~18 폰트 (작업파일/ 로컬 파일로 심는다. 웹폰트 의존 금지)
잘난 = "'Jalnan','Do Hyeon',sans-serif"                      # 만화 팝체 — 스타일 8 표지
쑥쑥 = "'Cafe24 Ssukssuk','Malgun Gothic',sans-serif"        # 손글씨체 — 스타일 12
프리 = "'Pretendard','Malgun Gothic',sans-serif"             # 깔끔 고딕 — 스타일 9~11·13~18


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


# ── 스타일 8~18 부품 (2026-09-04 — 카드제작 스킬 4-3절 도감 기준. 글씨체·글자 위치가 정체성) ──
# 텍스트 안전 사각형(좌우 80 / 상 90 / 하 100)은 전부 지킨다.

def 신카드(배경, 안쪽, 글꼴=None):
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>body{{margin:0;}}</style>
</head>
<body>
<div style="width:1080px;height:1350px;box-sizing:border-box;position:relative;overflow:hidden;{배경}font-family:{글꼴 or 프리};">
{안쪽}
</div>
</body>
</html>
"""


def 사진배경(사진, 위치="center"):
    return f"background:url('{사진}') {위치}/cover no-repeat;"


def 화면자리(라벨="화면 캡처 자리"):
    # 실제 캡처가 없을 때 쓰는 직접 만든 예시 상자 (스킬 4절: 화면이 필요한 것은 SVG·상자로 대체)
    return (f'<div style="background:#1E1E1E;border:2px solid #3A3A3A;border-radius:20px;height:480px;'
            f'display:flex;flex-direction:column;">'
            f'<div style="display:flex;gap:10px;padding:20px 24px;">'
            f'<div style="width:16px;height:16px;border-radius:50%;background:#FF5F57;"></div>'
            f'<div style="width:16px;height:16px;border-radius:50%;background:#FEBC2E;"></div>'
            f'<div style="width:16px;height:16px;border-radius:50%;background:#28C840;"></div></div>'
            f'<div style="flex-grow:1;display:flex;align-items:center;justify-content:center;color:#666;font-size:30px;">{라벨}</div></div>')


def 외곽선글자(내용, 크기, 채움, 겉선두께, 겉선색, 속선두께=0, 속선색="#FFFFFF", 기울기=0, 글꼴=None):
    # 겹층으로 이중 외곽선: 맨 밑 두꺼운 겉선 → 중간 속선 → 맨 위 채움 글자
    스타일 = f"font-family:{글꼴 or 잘난};font-size:{크기}px;line-height:1.18;letter-spacing:-0.01em;"
    h = f'<div style="position:relative;transform:rotate({기울기}deg);{스타일}">'
    h += f'<div style="position:absolute;inset:0;-webkit-text-stroke:{겉선두께}px {겉선색};color:{겉선색};">{내용}</div>'
    if 속선두께:
        h += f'<div style="position:absolute;inset:0;-webkit-text-stroke:{속선두께}px {속선색};color:{속선색};">{내용}</div>'
    h += f'<div style="position:relative;color:{채움};">{내용}</div></div>'
    return h


# ── 스타일 8: 팝스티커 총정리형 ──
def 스타일8표지(c):
    안쪽 = f'<div style="position:absolute;inset:0;{사진배경(c["사진"])}"></div>'
    안쪽 += '<div style="position:absolute;left:0;right:0;bottom:0;height:50%;background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,0.50) 100%);"></div>'
    안쪽 += '<div style="position:absolute;left:80px;right:80px;bottom:100px;display:flex;flex-direction:column;align-items:center;gap:30px;">'
    if c.get("윗줄"):
        안쪽 += 외곽선글자(f'{c.get("이모지", "💰")} {c["윗줄"]}', 44, "#FFFFFF", 12, "#111111", 글꼴=잘난)
    안쪽 += 외곽선글자(줄바꿈(c["제목"]), 100, c.get("제목색", "#FFD335"), 24, "#111111", 12, "#FFFFFF", 기울기=-2)
    안쪽 += "</div>"
    return 신카드("", 안쪽, 잘난)


def 스타일8본문(c):
    배경 = ("background:#F1F1F1;background-image:linear-gradient(#E2E2E2 1px,transparent 1px),"
            "linear-gradient(90deg,#E2E2E2 1px,transparent 1px);background-size:54px 54px;")
    안쪽 = '<div style="position:absolute;left:80px;right:80px;top:90px;bottom:100px;display:flex;flex-direction:column;justify-content:center;gap:44px;">'
    if c.get("제목"):
        안쪽 += f'<div style="text-align:center;">{외곽선글자(c["제목"], 58, "#111111", 10, "#FFFFFF", 글꼴=잘난)}</div>'
    for 박스 in c["박스"]:
        행들 = "".join(f'<div style="font-size:33px;font-weight:500;color:#444;line-height:1.55;">▶{k}: {v}</div>' for k, v in 박스["행"])
        안쪽 += (f'<div style="background:#FFFFFF;border-radius:28px;padding:44px 48px;box-shadow:0 6px 18px rgba(0,0,0,0.06);'
                 f'display:flex;flex-direction:column;gap:20px;">'
                 f'<div style="font-size:44px;font-weight:700;color:#111;">{박스.get("이모지", "💵")} {박스["제목"]}</div>{행들}</div>')
    안쪽 += "</div>"
    return 신카드(배경, 안쪽)


# ── 스타일 9: 미니멀 광고형 (전 장 동일 — 사진이 힘 있어야 성립) ──
def 스타일9(c):
    안쪽 = ""
    if c.get("배지"):
        안쪽 += (f'<div style="position:absolute;top:90px;left:0;right:0;display:flex;justify-content:center;">'
                 f'<div style="background:#FFFFFF;color:#111;font-size:28px;font-weight:600;letter-spacing:0.08em;'
                 f'padding:14px 34px;border-radius:999px;">{c["배지"]}</div></div>')
    줄들 = "<br>".join(c.get("줄", []))
    안쪽 += (f'<div style="position:absolute;left:80px;right:80px;bottom:100px;text-align:center;color:#FFFFFF;'
             f'display:flex;flex-direction:column;gap:30px;text-shadow:0 2px 16px rgba(0,0,0,0.45);">'
             f'<div style="font-size:64px;font-weight:700;line-height:1.25;">{줄바꿈(c["제목"])}</div>')
    if 줄들:
        안쪽 += f'<div style="font-size:33px;font-weight:400;line-height:1.9;color:rgba(255,255,255,0.94);">{줄들}</div>'
    안쪽 += "</div>"
    return 신카드(사진배경(c["사진"], c.get("사진위치", "center")), 안쪽)


# ── 스타일 10: 토스 정보형 ──
def 스타일10표지(c):
    안쪽 = '<div style="position:absolute;left:0;right:0;bottom:0;height:52%;background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,0.60) 100%);"></div>'
    안쪽 += ('<div style="position:absolute;left:80px;right:80px;bottom:100px;color:#FFFFFF;display:flex;flex-direction:column;gap:24px;">'
             + (f'<div style="font-size:33px;font-weight:500;color:rgba(255,255,255,0.90);">{c["안내"]}</div>' if c.get("안내") else "")
             + f'<div style="font-size:76px;font-weight:800;line-height:1.25;letter-spacing:-0.02em;">{줄바꿈(c["제목"])}</div></div>')
    return 신카드(사진배경(c["사진"], c.get("사진위치", "center")), 안쪽)


def 스타일10본문(c):
    배경 = f'background:{c.get("배경", "linear-gradient(180deg,#DCE9FF 0%,#EDE7FF 100%)")};'
    강조 = c.get("강조색", "#3182F6")
    핵심 = c.get("핵심")  # 파랑 채움할 행 번호 (1부터)
    안쪽 = '<div style="position:absolute;left:80px;right:80px;top:90px;bottom:100px;display:flex;flex-direction:column;gap:28px;">'
    안쪽 += f'<div style="font-size:32px;font-weight:700;color:{강조};letter-spacing:0.04em;">{c.get("스텝", "")} {c.get("스텝제목", "")}</div>'
    안쪽 += f'<div style="font-size:68px;font-weight:800;color:#111;line-height:1.3;letter-spacing:-0.02em;">{줄바꿈(c["제목"])}</div>'
    if c.get("설명"):
        안쪽 += f'<div style="font-size:34px;font-weight:400;color:#666;line-height:1.6;">{줄바꿈(c["설명"])}</div>'
    행들 = ""
    for i, (라벨, 값) in enumerate(c.get("행", []), 1):
        if 핵심 == i:
            행들 += (f'<div style="display:flex;justify-content:space-between;align-items:center;background:{강조};'
                     f'border-radius:18px;padding:30px 36px;margin:6px -12px;">'
                     f'<div style="font-size:32px;font-weight:600;color:rgba(255,255,255,0.85);">{라벨}</div>'
                     f'<div style="font-size:36px;font-weight:800;color:#FFFFFF;">{값}</div></div>')
        else:
            행들 += (f'<div style="display:flex;justify-content:space-between;align-items:center;padding:26px 24px;'
                     f'border-bottom:2px solid #F0F0F5;">'
                     f'<div style="font-size:32px;font-weight:500;color:#888;">{라벨}</div>'
                     f'<div style="font-size:34px;font-weight:700;color:#111;">{값}</div></div>')
    if 행들:
        안쪽 += f'<div style="background:#FFFFFF;border-radius:26px;padding:26px 28px;margin-top:14px;">{행들}</div>'
    안쪽 += "</div>"
    return 신카드(배경, 안쪽)


# ── 스타일 11: 다크 스펙정리형 (한 장 = 항목 하나) ──
def 스타일11표지(c):
    안쪽 = '<div style="position:absolute;left:0;right:0;bottom:0;height:52%;background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,0.68) 100%);"></div>'
    if c.get("로고"):
        안쪽 += (f'<div style="position:absolute;top:90px;left:0;right:0;display:flex;justify-content:center;">'
                 f'<div style="background:#FFFFFF;color:#111;font-size:28px;font-weight:700;padding:14px 34px;border-radius:999px;">{c["로고"]}</div></div>')
    안쪽 += (f'<div style="position:absolute;left:80px;right:80px;bottom:100px;display:flex;justify-content:space-between;align-items:flex-end;gap:30px;">'
             f'<div style="font-size:62px;font-weight:800;color:#FFFFFF;line-height:1.3;">{줄바꿈(c["제목"])}</div>'
             f'<div style="font-size:24px;color:rgba(255,255,255,0.60);white-space:nowrap;">{c.get("출처", "")}</div></div>')
    return 신카드(사진배경(c["사진"], c.get("사진위치", "center")), 안쪽)


def 스타일11본문(c):
    윗그림 = (f'<div style="position:absolute;inset:0;{사진배경(c["캡처"])}"></div>'
              f'<div style="position:absolute;inset:0;background:rgba(8,14,28,0.45);"></div>') if c.get("캡처") else \
             '<div style="position:absolute;inset:0;background:linear-gradient(135deg,#16233A 0%,#0C1626 100%);"></div>'
    항목들 = "".join(
        f'<div style="display:flex;align-items:center;gap:22px;">'
        f'<div style="background:#2E62FF;color:#FFF;font-size:26px;font-weight:700;padding:10px 24px;border-radius:999px;white-space:nowrap;">{k}</div>'
        f'<div style="font-size:32px;font-weight:600;color:#E8EEF9;">{v}</div></div>' for k, v in c.get("항목", []))
    불릿들 = "".join(f'<div style="font-size:30px;color:#C9D6EA;line-height:1.6;">• {x}</div>' for x in c.get("불릿", []))
    안쪽 = f'<div style="position:relative;height:430px;">{윗그림}</div>'
    안쪽 += ('<div style="position:absolute;left:80px;right:80px;top:470px;bottom:100px;display:flex;flex-direction:column;gap:26px;">'
             f'<div style="display:flex;justify-content:space-between;align-items:baseline;gap:24px;">'
             f'<div style="font-size:58px;font-weight:800;color:#FFFFFF;">{c["제목"]}</div>'
             f'<div style="font-size:36px;font-weight:700;color:#9FB4D8;white-space:nowrap;">{c.get("가격", "")}</div></div>')
    if c.get("설명"):
        안쪽 += f'<div style="font-size:30px;color:#8CA0BE;line-height:1.6;">{줄바꿈(c["설명"])}</div>'
    안쪽 += f'<div style="display:flex;flex-direction:column;gap:20px;margin-top:8px;">{항목들}</div>'
    if 불릿들:
        안쪽 += f'<div style="display:flex;flex-direction:column;gap:12px;margin-top:8px;">{불릿들}</div>'
    안쪽 += "</div>"
    return 신카드("background:#0C1626;", 안쪽)


# ── 스타일 12: 노트 테스트형 (손글씨체) ──
def 스타일12표지(c):
    안쪽 = '<div style="position:absolute;left:0;right:0;bottom:0;height:46%;background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,0.42) 100%);"></div>'
    if c.get("로고"):
        안쪽 += f'<div style="position:absolute;top:90px;left:80px;font-size:32px;color:#FFFFFF;text-shadow:0 2px 10px rgba(0,0,0,0.5);font-family:{쑥쑥};">{c["로고"]}</div>'
    내용 = 줄바꿈(c["제목"])
    글자 = (f'<div style="position:relative;font-family:{쑥쑥};font-size:92px;line-height:1.25;text-align:center;">'
            f'<div style="position:absolute;inset:0;-webkit-text-stroke:16px #FFFFFF;color:#FFFFFF;">{내용}</div>'
            f'<div style="position:relative;background:linear-gradient(180deg,#FF9EC4,#FF5E9E);-webkit-background-clip:text;'
            f'background-clip:text;color:transparent;">{내용}</div></div>')
    안쪽 += f'<div style="position:absolute;left:80px;right:80px;bottom:100px;display:flex;justify-content:center;">{글자}</div>'
    return 신카드(사진배경(c["사진"], c.get("사진위치", "center")), 안쪽, 쑥쑥)


def 스타일12본문(c):
    배경 = ("background:#FFFFFF;background-image:linear-gradient(#E8EEF5 1px,transparent 1px),"
            "linear-gradient(90deg,#E8EEF5 1px,transparent 1px);background-size:48px 48px;")
    def 그림칸(측):
        그림 = 측.get("그림", "")
        if 그림 and ("." in 그림):  # 파일이면 이미지, 아니면 이모지 크게
            return f'<img src="{그림}" style="height:300px;object-fit:contain;">'
        return f'<div style="font-size:170px;line-height:1;">{그림}</div>'
    안쪽 = '<div style="position:absolute;left:80px;right:80px;top:90px;bottom:100px;display:flex;flex-direction:column;align-items:center;justify-content:space-between;">'
    안쪽 += (f'<div style="border:4px solid #111;background:#FFFFFF;padding:26px 44px;font-size:46px;font-weight:600;'
             f'color:#111;text-align:center;line-height:1.4;">{줄바꿈(c["질문"])}</div>')
    if c.get("안내"):
        안쪽 += f'<div style="font-size:30px;color:#666;">*{c["안내"]}*</div>'
    안쪽 += '<div style="display:flex;gap:60px;align-items:flex-end;justify-content:center;">'
    for 글쇠, 바탕 in (("에이", "#CBE4FF"), ("비", "#FFD3E3")):
        측 = c[글쇠]
        표 = "A" if 글쇠 == "에이" else "B"
        안쪽 += (f'<div style="display:flex;flex-direction:column;align-items:center;gap:28px;max-width:420px;">{그림칸(측)}'
                 f'<div style="background:{바탕};border-radius:999px;padding:18px 40px;font-size:38px;font-weight:600;'
                 f'color:#111;text-align:center;line-height:1.35;">{표}. {측["글"]}</div></div>')
    안쪽 += "</div>"
    안쪽 += f'<div style="font-size:32px;color:#C0392B;">{c.get("하단", "★답변을 기억해 주세요!")}</div>'
    안쪽 += "</div>"
    return 신카드(배경, 안쪽, 쑥쑥)


# ── 스타일 13: 줄글 칼럼형 (읽는 글 — "한 장 3~5줄" 예외) ──
def 스타일13표지(c):
    자리들 = [(110, 220, -8), (740, 260, 6), (180, 540, 4), (780, 580, -6), (460, 380, -3), (620, 740, 8)]
    안쪽 = '<div style="position:absolute;left:0;right:0;bottom:0;height:48%;background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,0.58) 100%);"></div>'
    for 단어, (x, y, r) in zip(c.get("단어들", []), 자리들):
        안쪽 += (f'<div style="position:absolute;left:{x}px;top:{y}px;transform:rotate({r}deg);'
                 f'font-family:Georgia,serif;font-style:italic;font-size:36px;color:rgba(255,255,255,0.85);'
                 f'text-shadow:0 2px 8px rgba(0,0,0,0.4);">{단어}</div>')
    if c.get("코너명"):
        안쪽 += f'<div style="position:absolute;top:90px;left:80px;font-size:30px;font-weight:600;color:#FFFFFF;text-shadow:0 2px 8px rgba(0,0,0,0.5);">{c["코너명"]}</div>'
    안쪽 += (f'<div style="position:absolute;left:80px;right:80px;bottom:100px;color:#FFFFFF;font-size:64px;'
             f'font-weight:700;line-height:1.3;">{줄바꿈(c["제목"])}</div>')
    return 신카드(사진배경(c["사진"], c.get("사진위치", "center")), 안쪽)


def 스타일13본문(c):
    문단들 = "".join(f'<div style="font-size:32px;color:#333;line-height:1.75;">{줄바꿈(x)}</div>' for x in c["문단"])
    안쪽 = ('<div style="position:absolute;left:80px;right:80px;top:90px;bottom:100px;display:flex;flex-direction:column;gap:36px;">'
            f'<div style="font-size:54px;font-weight:800;color:#111;line-height:1.3;">{줄바꿈(c["제목"])}</div>{문단들}')
    if c.get("이미지"):
        안쪽 += (f'<div style="margin-top:auto;display:flex;flex-direction:column;gap:14px;">'
                 f'<img src="{c["이미지"]}" style="width:100%;max-height:360px;object-fit:cover;">'
                 + (f'<div style="font-size:28px;color:#777;">↑{c["캡션"]}</div>' if c.get("캡션") else "") + "</div>")
    안쪽 += "</div>"
    return 신카드("background:#FFFFFF;", 안쪽)


# ── 스타일 14: 형광 툴소개형 ──
def 스타일14표지(c):
    형광 = c.get("형광", "#CCFF33")
    안쪽 = '<div style="position:absolute;left:0;right:0;bottom:0;height:52%;background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,0.65) 100%);"></div>'
    if c.get("해시배지"):
        안쪽 += (f'<div style="position:absolute;top:90px;left:80px;background:{형광};color:#111;font-size:30px;'
                 f'font-weight:700;padding:12px 26px;border-radius:10px;">{c["해시배지"]}</div>')
    안쪽 += ('<div style="position:absolute;left:80px;right:80px;bottom:100px;display:flex;flex-direction:column;gap:14px;">'
             f'<div style="font-size:66px;font-weight:800;color:#FFFFFF;line-height:1.25;">{줄바꿈(c["제목흰"])}</div>'
             f'<div style="font-size:66px;font-weight:800;color:{형광};line-height:1.25;">{줄바꿈(c["제목형광"])}</div>')
    if c.get("해시들"):
        안쪽 += f'<div style="font-size:28px;color:rgba(255,255,255,0.75);margin-top:16px;">{c["해시들"]}</div>'
    안쪽 += "</div>"
    if c.get("계정"):
        안쪽 += f'<div style="position:absolute;right:80px;bottom:100px;font-size:26px;color:rgba(255,255,255,0.7);">{c["계정"]}</div>'
    return 신카드(사진배경(c["사진"], c.get("사진위치", "center")), 안쪽)


def 스타일14본문(c):
    형광 = c.get("형광", "#CCFF33")
    그림 = (f'<img src="{c["스크린샷"]}" style="width:100%;max-height:540px;object-fit:cover;border-radius:20px;">'
            if c.get("스크린샷") else 화면자리(c.get("자리라벨", "툴 화면 캡처 자리")))
    안쪽 = ('<div style="position:absolute;left:80px;right:80px;top:90px;bottom:100px;display:flex;flex-direction:column;gap:34px;">'
            '<div style="text-align:center;display:flex;flex-direction:column;gap:12px;">'
            + (f'<div style="font-size:34px;font-weight:700;color:{형광};">{c["번호"]}</div>' if c.get("번호") else "")
            + f'<div style="font-size:72px;font-weight:800;color:{형광};letter-spacing:-0.01em;">{c["툴명"]}</div>'
            + (f'<div style="font-size:34px;color:#FFFFFF;">{c["부제"]}</div>' if c.get("부제") else "")
            + f'</div>{그림}'
            f'<div style="font-size:34px;font-weight:600;color:#FFFFFF;line-height:1.7;margin-top:auto;">{줄바꿈(c["문단"])}</div></div>')
    return 신카드("background:#101010;", 안쪽)


# ── 스타일 15: 포토에세이 말풍선형 (좌우 지그재그가 정체성) ──
def 스타일15표지(c):
    안쪽 = '<div style="position:absolute;left:0;right:0;bottom:0;height:50%;background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,0.45) 100%);"></div>'
    안쪽 += '<div style="position:absolute;left:80px;right:80px;bottom:100px;display:flex;flex-direction:column;align-items:flex-start;gap:22px;">'
    if c.get("배지"):
        안쪽 += f'<div style="background:#FFD335;color:#111;font-size:30px;font-weight:700;padding:12px 26px;border-radius:6px;">{c["배지"]}</div>'
    안쪽 += f'<div style="background:#FFFFFF;padding:30px 40px;font-size:54px;font-weight:800;color:#111;line-height:1.35;">{줄바꿈(c["제목"])}</div>'
    if c.get("부제"):
        안쪽 += f'<div style="font-size:30px;color:#FFFFFF;text-shadow:0 2px 10px rgba(0,0,0,0.55);">{c["부제"]}</div>'
    안쪽 += "</div>"
    return 신카드(사진배경(c["사진"], c.get("사진위치", "center")), 안쪽)


def 스타일15본문(c):
    색표 = {"회": ("rgba(240,240,240,0.95)", "#1B1B1B"), "검": ("rgba(17,17,17,0.88)", "#FFFFFF"), "노": ("#FFD335", "#111111")}
    안쪽 = '<div style="position:absolute;inset:0;background:rgba(0,0,0,0.22);"></div>'
    안쪽 += f'<div style="position:absolute;top:90px;left:0;right:0;text-align:center;font-size:26px;color:rgba(255,255,255,0.85);">{c.get("계정", "@계정명")}</div>'
    안쪽 += '<div style="position:absolute;left:80px;right:80px;top:170px;bottom:100px;display:flex;flex-direction:column;justify-content:center;gap:28px;">'
    for 박스 in c["박스들"]:
        바탕, 글색 = 색표.get(박스.get("색", "회"), 색표["회"])
        정렬 = "flex-end" if 박스.get("쪽") == "우" else "flex-start"
        안쪽 += (f'<div style="align-self:{정렬};max-width:78%;background:{바탕};color:{글색};padding:24px 34px;'
                 f'border-radius:8px;font-size:34px;font-weight:600;line-height:1.55;">{줄바꿈(박스["글"])}</div>')
    안쪽 += "</div>"
    return 신카드(사진배경(c["사진"], c.get("사진위치", "center")), 안쪽)


# ── 스타일 16: 블랙 인사이트형 (문장이 힘 — "한 장 3~5줄" 예외) ──
def 형광치환(s, 색, 배경=False):
    시작 = f'<span style="background:{색};color:#111;padding:2px 12px;">' if 배경 else f'<span style="color:{색};">'
    return (s or "").replace("<형광>", 시작).replace("</형광>", "</span>")


def 스타일16표지(c):
    형광 = c.get("형광", "#D6FF4B")
    안쪽 = '<div style="position:absolute;left:0;right:0;bottom:0;height:52%;background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,0.70) 100%);"></div>'
    if c.get("로고"):
        안쪽 += f'<div style="position:absolute;top:90px;right:80px;font-size:30px;font-weight:800;color:{형광};">{c["로고"]}</div>'
    안쪽 += ('<div style="position:absolute;left:80px;right:80px;bottom:100px;display:flex;flex-direction:column;gap:24px;">'
             f'<div style="font-size:62px;font-weight:800;color:#FFFFFF;line-height:1.4;">{형광치환(줄바꿈(c["제목"]), 형광, 배경=True)}</div>'
             + (f'<div style="font-size:30px;color:rgba(255,255,255,0.80);">{c["부제"]}</div>' if c.get("부제") else "") + "</div>")
    return 신카드(사진배경(c["사진"], c.get("사진위치", "center")), 안쪽)


def 스타일16본문(c):
    형광 = c.get("형광", "#D6FF4B")
    줄들 = "".join(f'<div style="font-size:42px;font-weight:700;color:#FFFFFF;line-height:1.6;">{형광치환(x, 형광)}</div>'
                  for x in c["줄들"])
    안쪽 = ((f'<div style="position:absolute;top:90px;left:0;right:0;text-align:center;font-size:32px;font-weight:800;'
             f'letter-spacing:0.12em;color:{형광};">{c["로고"]}</div>') if c.get("로고") else "")
    안쪽 += (f'<div style="position:absolute;left:80px;right:80px;top:170px;bottom:100px;display:flex;flex-direction:column;'
             f'justify-content:center;align-items:center;text-align:center;gap:56px;">{줄들}</div>')
    return 신카드("background:#000000;", 안쪽)


# ── 스타일 17: 매거진 에세이형 (잔잔한 톤, 어그로 없음) ──
def 스타일17표지(c):
    안쪽 = '<div style="position:absolute;left:0;right:0;top:0;height:55%;background:linear-gradient(180deg,rgba(0,0,0,0.48) 0%,rgba(0,0,0,0) 100%);"></div>'
    안쪽 += (f'<div style="position:absolute;top:90px;left:80px;right:80px;display:flex;justify-content:space-between;'
             f'font-size:28px;color:rgba(255,255,255,0.92);">'
             f'<div>{c.get("헤더좌", "")}</div><div>{c.get("헤더우", "")}</div></div>')
    안쪽 += (f'<div style="position:absolute;top:180px;left:80px;right:80px;display:flex;flex-direction:column;gap:30px;">'
             f'<div style="font-size:62px;font-weight:500;color:#FFFFFF;line-height:1.45;letter-spacing:-0.01em;">{줄바꿈(c["제목"])}</div>')
    if c.get("부제"):
        안쪽 += f'<div style="align-self:flex-end;text-align:right;font-size:26px;color:rgba(255,255,255,0.88);line-height:1.8;">{줄바꿈(c["부제"])}</div>'
    안쪽 += "</div>"
    return 신카드(사진배경(c["사진"], c.get("사진위치", "center")), 안쪽)


def 스타일17본문(c):
    줄들 = "".join(f'<div style="font-size:34px;font-weight:400;color:#444;line-height:1.7;">{줄바꿈(x)}</div>' for x in c["줄들"])
    안쪽 = ('<div style="position:absolute;left:80px;right:80px;top:90px;bottom:100px;display:flex;flex-direction:column;gap:34px;">'
            f'<div style="font-size:110px;font-weight:700;color:{c.get("숫자색", "#C9B8E8")};line-height:1;">{c.get("숫자", "")}</div>'
            + (f'<div style="font-size:40px;font-weight:700;color:#333;">{c["소제목"]}</div>' if c.get("소제목") else "")
            + f'<div style="display:flex;flex-direction:column;gap:26px;margin-top:10px;">{줄들}</div></div>')
    return 신카드(f'background:{c.get("배경", "#F5F0E7")};', 안쪽)


# ── 스타일 18: 매거진 제품픽형 (한 장 = 제품 하나) ──
def 스타일18표지(c):
    안쪽 = '<div style="position:absolute;left:0;right:0;bottom:0;height:46%;background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,0.55) 100%);"></div>'
    if c.get("로고"):
        안쪽 += (f'<div style="position:absolute;top:90px;left:0;right:0;text-align:center;font-family:Georgia,serif;'
                 f'font-size:52px;letter-spacing:0.22em;color:#FFFFFF;text-shadow:0 2px 12px rgba(0,0,0,0.4);">{c["로고"]}</div>')
    if c.get("인서트"):
        안쪽 += (f'<div style="position:absolute;right:80px;top:420px;width:250px;background:#FFFFFF;padding:12px;'
                 f'box-shadow:0 8px 24px rgba(0,0,0,0.35);"><img src="{c["인서트"]}" style="width:100%;display:block;"></div>')
    안쪽 += '<div style="position:absolute;left:80px;right:80px;bottom:100px;display:flex;flex-direction:column;align-items:flex-start;gap:22px;">'
    if c.get("카테고리"):
        안쪽 += f'<div style="background:#111;color:#FFF;font-size:28px;font-weight:600;letter-spacing:0.1em;padding:12px 28px;">{c["카테고리"]}</div>'
    안쪽 += f'<div style="font-size:56px;font-weight:700;color:#FFFFFF;line-height:1.3;">{줄바꿈(c["제목"])}</div></div>'
    return 신카드(사진배경(c["사진"], c.get("사진위치", "center")), 안쪽)


def 스타일18본문(c):
    배경 = f'background:radial-gradient(circle at 50% 42%,{c.get("배경중심", "#FFF6C9")} 0%,{c.get("배경끝", "#F4E29A")} 100%);'
    안쪽 = ('<div style="position:absolute;left:80px;right:80px;top:90px;bottom:100px;display:flex;flex-direction:column;">'
            f'<div style="flex-grow:1;display:flex;align-items:center;justify-content:center;">'
            f'<img src="{c["제품사진"]}" style="max-width:640px;max-height:660px;object-fit:contain;filter:drop-shadow(0 24px 40px rgba(0,0,0,0.18));"></div>'
            f'<div style="align-self:flex-start;background:#111;color:#FFF;padding:28px 36px;display:flex;flex-direction:column;gap:12px;">'
            f'<div style="font-size:32px;font-weight:600;line-height:1.4;">{c["설명"]}</div>'
            f'<div style="font-size:28px;color:rgba(255,255,255,0.80);">{c["정보"]}</div></div></div>')
    return 신카드(배경, 안쪽)


신스타일 = {
    "8표지": 스타일8표지, "8본문": 스타일8본문,
    "9장": 스타일9,
    "10표지": 스타일10표지, "10본문": 스타일10본문,
    "11표지": 스타일11표지, "11본문": 스타일11본문,
    "12표지": 스타일12표지, "12본문": 스타일12본문,
    "13표지": 스타일13표지, "13본문": 스타일13본문,
    "14표지": 스타일14표지, "14본문": 스타일14본문,
    "15표지": 스타일15표지, "15본문": 스타일15본문,
    "16표지": 스타일16표지, "16본문": 스타일16본문,
    "17표지": 스타일17표지, "17본문": 스타일17본문,
    "18표지": 스타일18표지, "18본문": 스타일18본문,
}


def 카드html(c, t, 쪽, 전체):
    if c["유형"] in 신스타일:
        return 신스타일[c["유형"]](c)
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
    # 로컬 폰트를 모든 카드에 심는다 (웹폰트 로드 실패/지연 시에도 항상 제 글씨체가 뜨게)
    폰트파일 = [
        ("Do Hyeon", "DoHyeon.ttf", "truetype", 400),
        ("Jalnan", "Jalnan.ttf", "truetype", 400),
        ("Cafe24 Ssukssuk", "Cafe24Ssukssuk.ttf", "truetype", 400),
        ("Pretendard", "Pretendard-Regular.otf", "opentype", 400),
        ("Pretendard", "Pretendard-Bold.otf", "opentype", 700),
    ]
    faces = "".join(
        f"@font-face{{font-family:'{이름}';src:url('file:///{(Path(__file__).parent / 파일).resolve().as_posix()}') format('{형식}');font-weight:{굵기};}}"
        for 이름, 파일, 형식, 굵기 in 폰트파일)
    로컬폰트 = f"<style>{faces}</style>\n<style>"
    for i, c in enumerate(카드들, 1):
        c.setdefault("라벨", 스펙["라벨"])
        c.setdefault("꼬리", 스펙.get("꼬리", False))
        c.setdefault("글씨체", 스펙.get("글씨체", "도현"))
        h = 카드html(c, t, i, 전체).replace("<style>", 로컬폰트, 1)
        (폴더 / f"카드{i:02d}.html").write_text(h, encoding="utf-8")
    print(f"완료: 카드 {전체}장 → {폴더}  (확인은 루트의 전체확인열기.bat)")
