# 깃허브 액션이 2시간마다 실행하는 예약발행 스크립트. 사용자가 직접 만질 일 없음.
# 하는 일: 깃허브예약.json 에서 시간이 지난 건을 찾아
#   제작/폴더/카드NN.jpg + 캡션.txt 를 Make 웹훅으로 전송(PC 발행 버튼과 같은 모양)
#   성공 → 발행대장.txt 한 줄 + 예약에서 제거 / 실패 → 오류기록.txt 한 줄 + 예약에서 제거
# 웹훅 주소는 저장소에 없고 깃허브 Secrets(MAKE_WEBHOOK)로만 들어온다.

import base64
import json
import os
import re
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
큐파일 = ROOT / "깃허브예약.json"
웹훅 = os.environ.get("MAKE_WEBHOOK", "").strip()


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


def 전송(폴더):
    # 성공하면 None, 실패하면 이유 문자열 (확인서버.py의 전송과 같은 페이로드)
    if not (폴더 / "캡션.txt").exists():
        return "캡션.txt 없음"
    줄들 = (폴더 / "캡션.txt").read_text(encoding="utf-8").splitlines()
    캡션 = chr(10).join(l for l in 줄들 if not l.startswith("[대체텍스트]")).strip()
    images = []
    for jpg in sorted(폴더.glob("카드*.jpg")):
        images.append({"name": jpg.name,
                       "data": base64.b64encode(jpg.read_bytes()).decode()})
    if not images:
        return "보낼 JPEG가 없음 (예약 때 변환된 카드*.jpg가 폴더에 없음)"
    body = json.dumps({"caption": 캡션, "count": len(images), "images": images}).encode()
    if len(body) > 4_500_000:
        return f"전송 용량 초과 ({len(body)//1_000_000}MB)"
    req = urllib.request.Request(웹훅, body, {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            if r.status != 200:
                return f"Make 응답 {r.status}"
    except Exception as e:
        return f"Make 전송 실패: {e}"
    return None


def main():
    if not 큐파일.exists():
        print("예약 없음")
        return
    목록 = json.loads(큐파일.read_text(encoding="utf-8"))
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    now문자 = now.strftime("%Y-%m-%dT%H:%M")
    today = now.strftime("%Y-%m-%d")
    남김 = [x for x in 목록 if x["time"] > now문자]
    실행할 = [x for x in 목록 if x["time"] <= now문자]
    if not 실행할:
        print("아직 시간 안 된 예약", len(남김), "건")
        return
    if not 웹훅:
        print("MAKE_WEBHOOK 시크릿이 비어 있음 — 발행 불가")
        (ROOT / "오류기록.txt").open("a", encoding="utf-8").write(
            f"{today} 깃허브 예약발행 실패: MAKE_WEBHOOK 시크릿 미등록\n")
        return
    for 항목 in 실행할:
        폴더 = ROOT / "제작" / 항목["folder"]
        if not 폴더.is_dir():
            기록 = f"{today} 깃허브 예약발행 취소: {항목['folder']} 폴더 없음\n"
        else:
            이유 = 전송(폴더)
            if 이유:
                기록 = f"{today} 깃허브 예약발행 실패: {폴더.name} {이유}\n"
            else:
                제목 = 폴더.name.split("_", 1)[-1]
                with (ROOT / "발행대장.txt").open("a", encoding="utf-8") as f:
                    f.write(f"{today} [{카테고리(폴더)}] {제목} (깃허브예약)\n")
                기록 = None
                print("발행 완료:", 폴더.name)
        if 기록:
            (ROOT / "오류기록.txt").open("a", encoding="utf-8").write(기록)
            print(기록.strip())
    큐파일.write_text(json.dumps(남김, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
