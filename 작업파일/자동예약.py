# 사람 검수 없이 발행 시각을 자동으로 뽑아 깃헙예약에 넣는다 (2026-09-16 사용자 지시).
# 쓰는 법: python 작업파일/자동예약.py <제작폴더명>   (예: 2026-09-17_단풍시기)
# 시각 규칙: 오전 06:00~08:30 / 오후 15:00~18:00 두 창, 창마다 하루 1건(하루 최대 2건),
#            창 고르는 순서는 날마다 랜덤, 창 안에서 분 단위 랜덤.
# 실제 촬영·R2 업로드·푸시는 확인서버.py의 깃허브예약등록을 그대로 쓴다 (중복 코드 없음).

import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import 확인서버

창들 = [("06:00", "08:30"), ("15:00", "18:00")]
창당한도 = 1
간격 = timedelta(minutes=40)


def 분으로(t):
    시, 분 = map(int, t.split(":"))
    return 시 * 60 + 분


def 시각뽑기(예약된, now):
    # 예약된: 기존 깃헙예약의 datetime 목록. 성공 시 "YYYY-MM-DDTHH:MM", 자리 없으면 None
    for 며칠뒤 in range(14):
        날 = date.today() + timedelta(days=며칠뒤)
        그날 = [t for t in 예약된 if t.date() == 날]
        for 시작, 끝 in random.sample(창들, len(창들)):  # 하루 1건인 날은 오전/오후가 섞이게
            창안 = [t for t in 그날 if 시작 <= t.strftime("%H:%M") <= 끝]
            if len(창안) >= 창당한도:
                continue
            후보들 = []
            for 분 in range(분으로(시작), 분으로(끝) + 1):
                t = datetime.combine(날, datetime.min.time()) + timedelta(minutes=분)
                if t < now + timedelta(minutes=10):  # 너무 임박한 시각 제외
                    continue
                if all(abs(t - 기존) >= 간격 for 기존 in 그날):
                    후보들.append(t)
            if 후보들:
                return random.choice(후보들).strftime("%Y-%m-%dT%H:%M")
    return None


def main():
    if len(sys.argv) != 2:
        print("쓰는 법: python 작업파일/자동예약.py <제작폴더명>")
        sys.exit(1)
    폴더 = 확인서버.제작 / sys.argv[1]
    if not 폴더.is_dir():
        print("폴더 없음:", 폴더)
        sys.exit(1)
    예약된 = []
    for x in 확인서버.깃큐목록():
        try:
            예약된.append(datetime.strptime(x["time"], "%Y-%m-%dT%H:%M"))
        except Exception:
            pass
    t = 시각뽑기(예약된, datetime.now())
    if not t:
        print("2주 안에 빈 자리가 없음 — 예약 과다, 사람 확인 필요")
        sys.exit(1)
    이유 = 확인서버.깃허브예약등록(폴더, t)
    if 이유:
        print("예약 실패:", 이유)
        확인서버.ROOT.joinpath("오류기록.txt").open("a", encoding="utf-8").write(
            f"{date.today().isoformat()} 자동예약 실패: {폴더.name} {이유}\n")
        sys.exit(1)
    print(f"예약 완료: {폴더.name} → {t.replace('T', ' ')} (깃헙예약, PC 꺼져도 발행됨)")


if __name__ == "__main__":
    main()
