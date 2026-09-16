# 깃허브 액션이 돌리는 예약발행 스크립트. 사용자가 직접 만질 일 없음.
# 하는 일:
#   1) 깃허브예약.json 에서 시간이 지난 건을 찾아, 건 안에 든 R2 이미지 주소를 내려받아
#      base64로 묶어 Make 웹훅으로 전송 (PC 발행 버튼과 같은 페이로드)
#      성공 → 발행대장.txt 한 줄 / 실패 → 오류기록.txt 한 줄. 어느 쪽이든 예약에서 빼고
#      R2 이미지를 24시간 뒤 지우도록 삭제예약.json 에 적는다 (2026-09-16 사용자 지시)
#   2) 삭제예약.json 에서 시간이 지난 건의 R2 이미지를 지운다
# 웹훅 주소는 저장소에 없고 깃허브 Secrets(MAKE_WEBHOOK)로만, R2 키도 Secrets로만 들어온다.

import base64
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r2카드

ROOT = Path(__file__).resolve().parent.parent
큐파일 = ROOT / "깃허브예약.json"
삭제파일 = ROOT / "삭제예약.json"
웹훅 = os.environ.get("MAKE_WEBHOOK", "").strip()


def 읽기(파일):
    try:
        return json.loads(파일.read_text(encoding="utf-8"))
    except Exception:
        return []


def 쓰기(파일, 목록):
    파일.write_text(json.dumps(목록, ensure_ascii=False, indent=1), encoding="utf-8")


def 오류(줄):
    (ROOT / "오류기록.txt").open("a", encoding="utf-8").write(줄 + "\n")
    print(줄)


def 전송(항목):
    # 성공하면 None, 실패하면 이유 문자열 (확인서버.py의 전송과 같은 페이로드)
    images = []
    for img in 항목["images"]:
        try:
            # r2.dev는 기본 파이썬 User-Agent를 403으로 막는다 (2026-09-16 실측)
            요청 = urllib.request.Request(img["url"],
                                          headers={"User-Agent": "Mozilla/5.0 insta-cards"})
            with urllib.request.urlopen(요청, timeout=60) as r:
                images.append({"name": img["name"],
                               "data": base64.b64encode(r.read()).decode()})
        except Exception as e:
            return f"R2에서 이미지 못 받음 ({img['name']}): {e}"
    body = json.dumps({"caption": 항목["caption"], "count": len(images),
                       "images": images}).encode()
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


def 발행(now):
    목록 = 읽기(큐파일)
    now문자 = now.strftime("%Y-%m-%dT%H:%M")
    today = now.strftime("%Y-%m-%d")
    실행할 = [x for x in 목록 if x["time"] <= now문자]
    if not 실행할:
        print("아직 시간 안 된 예약", len(목록), "건")
        return
    삭제목록 = 읽기(삭제파일)
    for 항목 in 실행할:
        if "images" not in 항목:  # 예전 형식(이미지가 저장소에 있던 시절) — 발행 불가
            오류(f"{today} 깃허브 예약발행 취소: {항목['folder']} 옛 형식 예약이라 다시 등록 필요")
            continue
        if not 웹훅:
            줄 = f"{today} 깃허브 예약발행 실패: MAKE_WEBHOOK 시크릿 미등록"
            try:
                이미 = 줄 in (ROOT / "오류기록.txt").read_text(encoding="utf-8")
            except Exception:
                이미 = False
            오류(줄) if not 이미 else print(줄)
            return  # 큐를 건드리지 않고 멈춤 — 시크릿 넣으면 다음 회차에 발행됨
        이유 = 전송(항목)
        if 이유:
            오류(f"{today} 깃허브 예약발행 실패: {항목['folder']} {이유}")
        else:
            제목 = 항목["folder"].split("_", 1)[-1]
            with (ROOT / "발행대장.txt").open("a", encoding="utf-8") as f:
                f.write(f"{today} [{항목.get('category', '미상')}] {제목} (깃허브예약)\n")
            print("발행 완료:", 항목["folder"])
        삭제목록.append({
            "folder": 항목["folder"],
            "keys": [r2카드.키(항목["folder"], img["name"]) for img in 항목["images"]],
            "delete_after": (now + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M")})
    쓰기(큐파일, [x for x in 목록 if x["time"] > now문자])
    쓰기(삭제파일, 삭제목록)


def 청소(now):
    # 발행(성공이든 실패든) 24시간 지난 건의 R2 이미지를 지운다
    목록 = 읽기(삭제파일)
    now문자 = now.strftime("%Y-%m-%dT%H:%M")
    지울것 = [x for x in 목록 if x["delete_after"] <= now문자]
    if not 지울것:
        return
    try:
        r2카드.env()
    except RuntimeError as e:
        print(f"R2 청소 건너뜀 ({e}) — 시크릿 넣으면 다음 회차에 지움")
        return
    남김 = [x for x in 목록 if x["delete_after"] > now문자]
    for 항목 in 지울것:
        try:
            for key in 항목["keys"]:
                r2카드.지우기(key)
            print("R2 삭제 완료:", 항목["folder"])
        except Exception as e:
            남김.append(항목)  # 다음 회차에 다시 시도
            print("R2 삭제 실패(다음에 재시도):", 항목["folder"], e)
    쓰기(삭제파일, 남김)


def main():
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    발행(now)
    청소(now)


if __name__ == "__main__":
    main()
