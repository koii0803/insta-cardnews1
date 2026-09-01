#!/usr/bin/env bash
# 템플릿 생성기. 카테고리마다 표지/본문/강조/마무리 4장.
# 파일 이름은 주제풀.txt 의 태그와 똑같이 맞춘다.
set -e
cd "$(dirname "$0")"

TPL=../템플릿

# emit <파일명> <눈썹> <페이지표기> <본문HTML> [flip]
emit() {
if [ "$5" = "flip" ]; then
  B="$ACC"; I="$ONACC"; S="$FSUB"; L="$FLINE"; DOT="$ONACC"
else
  B="$BG";  I="$INK";   S="$SUB";  L="$LINE";  DOT="$ACC"
fi
cat > "$TPL/$1" <<EOF
<!doctype html>
<!-- 글자수 구간: 10자 이하 132px / 11~20자 104px / 21자 이상 84px -->
<html>
<head>
  <meta charset="utf-8">
  <script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap">
  <style>
    body { margin: 0; }
    a { color: $ACC; } a:hover { color: $ACC; }
  </style>
</helmet>
<div style="width:1080px;height:1350px;box-sizing:border-box;background:$B;color:$I;display:flex;flex-direction:column;padding:90px 80px 100px;font-family:'IBM Plex Sans KR','Malgun Gothic',sans-serif;">

  <div style="display:flex;align-items:center;gap:18px;flex-shrink:0;">
    <div style="width:18px;height:18px;background:$DOT;"></div>
    <div style="font-size:30px;font-weight:600;letter-spacing:0.14em;color:$S;">$2</div>
  </div>

  <div style="flex-grow:1;display:flex;flex-direction:column;justify-content:center;gap:40px;padding:56px 0;">
$4
  </div>

  <div style="display:flex;justify-content:space-between;align-items:center;font-size:28px;font-weight:500;color:$S;flex-shrink:0;border-top:2px solid $L;padding-top:26px;">
    <div>@계정명</div>
    <div>$3</div>
  </div>

</div>
</x-dc>
<script data-dc-script data-props='{"\$preview":{"width":1080,"height":1350}}'>
class Component extends DCLogic {}
</script>
</body>
</html>
EOF
}

H1="font-family:'Black Han Sans','Malgun Gothic',sans-serif;font-weight:400;letter-spacing:-0.02em"

# 다음 장으로 넘기는 미끼 (본문 카드 우하단)
bait() {
cat <<HTML
    <div style="display:flex;justify-content:flex-end;align-items:center;gap:14px;margin-top:8px;">
      <div style="font-size:30px;font-weight:600;color:$SUB;">$1</div>
      <div style="font-size:34px;font-weight:700;color:$ACC;">&#8594;</div>
    </div>
HTML
}

# ================================================================ 반전 상식 · 경고
BG="#FFF1CE"; SURF="#FFFFFF"; INK="#171512"; SUB="#6B6255"; ACC="#E04A2F"; ONACC="#FFFFFF"
LINE="#E4D6B0"; FSUB="rgba(255,255,255,0.78)"; FLINE="rgba(255,255,255,0.32)"

INNER=$(cat <<HTML
    <div style="display:inline-flex;align-self:flex-start;background:$ACC;color:$ONACC;font-size:34px;font-weight:700;padding:16px 32px;">지금 확인하세요</div>
    <div style="$H1;font-size:126px;line-height:1.08;">[사물]로<br>닦으면 안 되는 것</div>
    <div style="width:200px;height:14px;background:$ACC;"></div>
    <div style="font-size:46px;line-height:1.5;color:$SUB;">[무심코 하고 있는 행동 한 줄]<br>이유가 있습니다</div>
HTML
)
emit 반전상식-표지.dc.html "반전 상식" "01 / 08" "$INNER"

INNER=$(cat <<HTML
    <div style="display:flex;align-items:center;gap:22px;">
      <div style="width:64px;height:64px;background:$ACC;color:$ONACC;font-size:44px;font-weight:700;display:flex;align-items:center;justify-content:center;">X</div>
      <div style="font-size:44px;font-weight:700;">이렇게 쓰고 있다면</div>
    </div>
    <div style="background:$SURF;padding:48px;font-size:52px;font-weight:700;line-height:1.35;">[잘못된 사용 사례 한 줄]</div>
    <div style="display:flex;flex-direction:column;gap:16px;">
      <div style="font-size:32px;font-weight:600;letter-spacing:0.1em;color:$SUB;">왜 안 되냐면</div>
      <div style="font-size:42px;line-height:1.55;">[이유를 두 줄로. 성분, 잔여물, 손상 같은<br>구체적인 근거를 넣습니다]</div>
    </div>
$(bait "근데 더 심한 게 있음")
HTML
)
emit 반전상식-본문.dc.html "반전 상식" "04 / 08" "$INNER"

INNER=$(cat <<HTML
    <div style="$H1;font-size:112px;line-height:1.14;">[가장 충격적인<br>사실 한 줄]</div>
    <div style="width:200px;height:14px;background:$ONACC;"></div>
    <div style="font-size:44px;line-height:1.5;color:$FSUB;">[그래서 뭘 해야 하는지 한 줄]</div>
HTML
)
emit 반전상식-강조.dc.html "반전 상식" "06 / 08" "$INNER" flip

INNER=$(cat <<HTML
    <div style="$H1;font-size:92px;line-height:1.16;">그럼 어떻게 하냐면</div>
    <div style="display:flex;flex-direction:column;gap:16px;">
      <div style="background:$SURF;padding:32px 40px;font-size:42px;font-weight:600;">[대안 1]</div>
      <div style="background:$SURF;padding:32px 40px;font-size:42px;font-weight:600;">[대안 2]</div>
      <div style="background:$SURF;padding:32px 40px;font-size:42px;font-weight:600;">[대안 3]</div>
    </div>
    <div style="background:$ACC;color:$ONACC;padding:40px;font-size:44px;font-weight:700;line-height:1.4;">집에 있는 사람한테<br>바로 보내주세요</div>
HTML
)
emit 반전상식-마무리.dc.html "반전 상식" "08 / 08" "$INNER"

# ================================================================ 현실 기준 · 논쟁
BG="#F2ECE1"; SURF="#FFFFFF"; INK="#16130E"; SUB="#6A6154"; ACC="#B0202B"; ONACC="#FFFFFF"
LINE="#DDD2BF"; FSUB="rgba(255,255,255,0.78)"; FLINE="rgba(255,255,255,0.32)"

INNER=$(cat <<HTML
    <div style="display:inline-flex;align-self:flex-start;background:$ACC;color:$ONACC;font-size:34px;font-weight:700;padding:16px 32px;">기준 총정리</div>
    <div style="$H1;font-size:132px;line-height:1.08;">[주제]<br>딱 정해줄게</div>
    <div style="width:200px;height:14px;background:$ACC;"></div>
    <div style="font-size:46px;line-height:1.5;color:$SUB;">매번 검색했다면<br>이 [N]장으로 끝납니다</div>
HTML
)
emit 현실기준-표지.dc.html "현실 기준" "01 / 10" "$INNER"

INNER=$(cat <<HTML
    <div style="display:inline-flex;align-self:flex-start;background:$ACC;color:$ONACC;font-size:32px;font-weight:700;padding:14px 28px;">[조건 · 상황]</div>
    <div style="$H1;font-size:180px;line-height:1;letter-spacing:-0.03em;">[금액]</div>
    <div style="background:$SURF;padding:44px;display:flex;flex-direction:column;gap:22px;">
      <div style="font-size:42px;line-height:1.4;font-weight:600;">[해당되는 대상 1]</div>
      <div style="height:2px;background:$LINE;"></div>
      <div style="font-size:42px;line-height:1.4;font-weight:600;">[해당되는 대상 2]</div>
    </div>
    <div style="font-size:42px;line-height:1.55;color:$SUB;">[왜 이 금액인지 한 줄 근거]</div>
$(bait "여기서 한 칸 올라감")
HTML
)
emit 현실기준-본문.dc.html "현실 기준" "05 / 10" "$INNER"

INNER=$(cat <<HTML
    <div style="$H1;font-size:112px;line-height:1.14;">[가장 논쟁되는<br>기준 한 줄]</div>
    <div style="width:200px;height:14px;background:$ONACC;"></div>
    <div style="font-size:44px;line-height:1.5;color:$FSUB;">[이 말이 왜 맞는지 한 줄]</div>
HTML
)
emit 현실기준-강조.dc.html "현실 기준" "08 / 10" "$INNER" flip

INNER=$(cat <<HTML
    <div style="$H1;font-size:88px;line-height:1.16;">한 장 요약</div>
    <div style="display:flex;flex-direction:column;gap:14px;">
      <div style="display:flex;align-items:center;gap:24px;background:$SURF;padding:28px 36px;">
        <div style="font-size:52px;font-weight:700;color:$ACC;min-width:250px;">[값 1]</div>
        <div style="font-size:38px;line-height:1.35;">[조건 1]</div>
      </div>
      <div style="display:flex;align-items:center;gap:24px;background:$SURF;padding:28px 36px;">
        <div style="font-size:52px;font-weight:700;color:$ACC;min-width:250px;">[값 2]</div>
        <div style="font-size:38px;line-height:1.35;">[조건 2]</div>
      </div>
      <div style="display:flex;align-items:center;gap:24px;background:$SURF;padding:28px 36px;">
        <div style="font-size:52px;font-weight:700;color:$ACC;min-width:250px;">[값 3]</div>
        <div style="font-size:38px;line-height:1.35;">[조건 3]</div>
      </div>
      <div style="display:flex;align-items:center;gap:24px;background:$SURF;padding:28px 36px;">
        <div style="font-size:52px;font-weight:700;color:$ACC;min-width:250px;">[값 4]</div>
        <div style="font-size:38px;line-height:1.35;">[조건 4]</div>
      </div>
    </div>
    <div style="background:$ACC;color:$ONACC;padding:40px;font-size:44px;font-weight:700;line-height:1.4;">필요할 때 꺼내볼 수 있게<br>저장해두세요</div>
HTML
)
emit 현실기준-마무리.dc.html "현실 기준" "10 / 10" "$INNER"

# ================================================================ 심리 테스트
BG="#EBE2FF"; SURF="#FFFFFF"; INK="#1C1533"; SUB="#635C7A"; ACC="#7A3BED"; ONACC="#FFFFFF"
LINE="#D6C9F5"; FSUB="rgba(255,255,255,0.78)"; FLINE="rgba(255,255,255,0.32)"

INNER=$(cat <<HTML
    <div style="display:inline-flex;align-self:flex-start;background:$ACC;color:$ONACC;font-size:34px;font-weight:700;padding:16px 32px;">성격 테스트</div>
    <div style="$H1;font-size:120px;line-height:1.1;">[행동]으로 보는<br>내 성격</div>
    <div style="width:200px;height:14px;background:$ACC;"></div>
    <div style="font-size:46px;line-height:1.5;color:$SUB;">고르기만 하면 됩니다<br>30초면 끝나요</div>
HTML
)
emit 심리테스트-표지.dc.html "심리 테스트" "01 / 07" "$INNER"

INNER=$(cat <<HTML
    <div style="$H1;font-size:84px;line-height:1.16;">당신은<br>어느 쪽인가요?</div>
    <div style="display:grid;grid-template-columns:repeat(2, minmax(0, 1fr));gap:20px;">
      <div style="background:$SURF;padding:36px;display:flex;flex-direction:column;gap:16px;">
        <div style="font-size:48px;font-weight:700;color:$ACC;">A</div>
        <div style="font-size:36px;font-weight:600;line-height:1.35;">[선택지 A]</div>
      </div>
      <div style="background:$SURF;padding:36px;display:flex;flex-direction:column;gap:16px;">
        <div style="font-size:48px;font-weight:700;color:$ACC;">B</div>
        <div style="font-size:36px;font-weight:600;line-height:1.35;">[선택지 B]</div>
      </div>
      <div style="background:$SURF;padding:36px;display:flex;flex-direction:column;gap:16px;">
        <div style="font-size:48px;font-weight:700;color:$ACC;">C</div>
        <div style="font-size:36px;font-weight:600;line-height:1.35;">[선택지 C]</div>
      </div>
      <div style="background:$SURF;padding:36px;display:flex;flex-direction:column;gap:16px;">
        <div style="font-size:48px;font-weight:700;color:$ACC;">D</div>
        <div style="font-size:36px;font-weight:600;line-height:1.35;">[선택지 D]</div>
      </div>
    </div>
$(bait "고른 거 기억해두세요")
HTML
)
emit 심리테스트-본문.dc.html "심리 테스트" "02 / 07" "$INNER"

INNER=$(cat <<HTML
    <div style="$H1;font-size:112px;line-height:1.14;">[가장 뜨끔한<br>결과 한 줄]</div>
    <div style="width:200px;height:14px;background:$ONACC;"></div>
    <div style="font-size:44px;line-height:1.5;color:$FSUB;">[찔리면 이 유형이 맞습니다]</div>
HTML
)
emit 심리테스트-강조.dc.html "심리 테스트" "05 / 07" "$INNER" flip

INNER=$(cat <<HTML
    <div style="display:inline-flex;align-self:flex-start;background:$ACC;color:$ONACC;font-size:32px;font-weight:700;padding:14px 28px;">A를 고른 당신</div>
    <div style="$H1;font-size:104px;line-height:1.1;">[유형 이름]</div>
    <div style="background:$SURF;padding:44px;font-size:40px;line-height:1.6;">[유형 설명 세 줄.<br>맞다고 느낄 만한 구체적인 습관과<br>주변 반응까지 적습니다]</div>
    <div style="background:$ACC;color:$ONACC;padding:40px;font-size:44px;font-weight:700;line-height:1.4;">친구는 뭐 나왔는지<br>물어보세요</div>
HTML
)
emit 심리테스트-마무리.dc.html "심리 테스트" "07 / 07" "$INNER"

# ================================================================ 혜택 · 트렌드 · 신상
BG="#DDEFF7"; SURF="#FFFFFF"; INK="#0A2130"; SUB="#4E6B7A"; ACC="#0E7C86"; ONACC="#FFFFFF"
LINE="#BFDDE9"; FSUB="rgba(255,255,255,0.78)"; FLINE="rgba(255,255,255,0.32)"

INNER=$(cat <<HTML
    <div style="display:inline-flex;align-self:flex-start;background:$ACC;color:$ONACC;font-size:34px;font-weight:700;padding:16px 32px;">TOP 3</div>
    <div style="$H1;font-size:120px;line-height:1.1;">모르면 못 받는<br>[기간] [혜택명]</div>
    <div style="width:200px;height:14px;background:$ACC;"></div>
    <div style="font-size:46px;line-height:1.5;color:$SUB;">신청 안 하면 안 줍니다<br>마감 [날짜]</div>
HTML
)
emit 혜택-표지.dc.html "혜택 정보" "01 / 06" "$INNER"

INNER=$(cat <<HTML
    <div style="display:flex;align-items:baseline;gap:24px;">
      <div style="font-size:72px;font-weight:700;color:$ACC;">01</div>
      <div style="font-size:52px;font-weight:700;line-height:1.25;">[혜택 이름]</div>
    </div>
    <div style="background:$SURF;padding:40px;display:flex;flex-direction:column;gap:24px;">
      <div style="display:flex;gap:28px;align-items:baseline;">
        <div style="font-size:32px;font-weight:600;color:$SUB;min-width:150px;">대상</div>
        <div style="font-size:38px;font-weight:600;line-height:1.35;">[해당되는 사람]</div>
      </div>
      <div style="height:2px;background:$LINE;"></div>
      <div style="display:flex;gap:28px;align-items:baseline;">
        <div style="font-size:32px;font-weight:600;color:$SUB;min-width:150px;">금액</div>
        <div style="font-size:38px;font-weight:600;line-height:1.35;">[지원 금액]</div>
      </div>
      <div style="height:2px;background:$LINE;"></div>
      <div style="display:flex;gap:28px;align-items:baseline;">
        <div style="font-size:32px;font-weight:600;color:$SUB;min-width:150px;">기간</div>
        <div style="font-size:38px;font-weight:600;line-height:1.35;">[신청 기간]</div>
      </div>
      <div style="height:2px;background:$LINE;"></div>
      <div style="display:flex;gap:28px;align-items:baseline;">
        <div style="font-size:32px;font-weight:600;color:$SUB;min-width:150px;">신청</div>
        <div style="font-size:38px;font-weight:600;line-height:1.35;">[신청처 이름]</div>
      </div>
    </div>
$(bait "이거 놓치면 아까움")
HTML
)
emit 혜택-본문.dc.html "혜택 정보" "03 / 06" "$INNER"

INNER=$(cat <<HTML
    <div style="$H1;font-size:112px;line-height:1.14;">[놓치면 손해인<br>핵심 한 줄]</div>
    <div style="width:200px;height:14px;background:$ONACC;"></div>
    <div style="font-size:44px;line-height:1.5;color:$FSUB;">[마감일 또는 조건 한 줄]</div>
HTML
)
emit 혜택-강조.dc.html "혜택 정보" "05 / 06" "$INNER" flip

INNER=$(cat <<HTML
    <div style="$H1;font-size:92px;line-height:1.16;">신청은 여기서</div>
    <div style="display:flex;flex-direction:column;gap:16px;">
      <div style="background:$SURF;padding:32px 40px;display:flex;justify-content:space-between;align-items:center;gap:20px;">
        <div style="font-size:38px;font-weight:700;">[혜택 1]</div>
        <div style="font-size:32px;color:$SUB;">[신청처]</div>
      </div>
      <div style="background:$SURF;padding:32px 40px;display:flex;justify-content:space-between;align-items:center;gap:20px;">
        <div style="font-size:38px;font-weight:700;">[혜택 2]</div>
        <div style="font-size:32px;color:$SUB;">[신청처]</div>
      </div>
      <div style="background:$SURF;padding:32px 40px;display:flex;justify-content:space-between;align-items:center;gap:20px;">
        <div style="font-size:38px;font-weight:700;">[혜택 3]</div>
        <div style="font-size:32px;color:$SUB;">[신청처]</div>
      </div>
    </div>
    <div style="background:$ACC;color:$ONACC;padding:40px;font-size:44px;font-weight:700;line-height:1.4;">마감 [날짜]<br>오늘 안에 신청하세요</div>
HTML
)
emit 혜택-마무리.dc.html "혜택 정보" "06 / 06" "$INNER"

# ================================================================ 랭킹
BG="#0F2340"; SURF="#1B3358"; INK="#FFFFFF"; SUB="#9FB4CF"; ACC="#FF8A28"; ONACC="#17130C"
LINE="#2B4A73"; FSUB="rgba(23,19,12,0.72)"; FLINE="rgba(23,19,12,0.28)"

INNER=$(cat <<HTML
    <div style="display:inline-flex;align-self:flex-start;background:$ACC;color:$ONACC;font-size:34px;font-weight:700;padding:16px 32px;">TOP 5</div>
    <div style="$H1;font-size:126px;line-height:1.08;">[주제]<br>TOP 5</div>
    <div style="width:200px;height:14px;background:$ACC;"></div>
    <div style="font-size:46px;line-height:1.5;color:$SUB;">1위는 진짜 예상 못 합니다</div>
HTML
)
emit 랭킹-표지.dc.html "랭킹" "01 / 07" "$INNER"

INNER=$(cat <<HTML
    <div style="display:flex;align-items:baseline;gap:28px;">
      <div style="$H1;font-size:150px;line-height:1;color:$ACC;">3</div>
      <div style="font-size:54px;font-weight:700;line-height:1.25;">[항목 이름]</div>
    </div>
    <div style="height:380px;background:$SURF;border:3px dashed $LINE;display:flex;align-items:center;justify-content:center;font-size:34px;color:$SUB;">이미지 자리</div>
    <div style="font-size:40px;line-height:1.55;color:$SUB;">[왜 이 순위인지 두 줄.<br>숫자나 사실 하나는 꼭 넣습니다]</div>
$(bait "2위부터가 진짜")
HTML
)
emit 랭킹-본문.dc.html "랭킹" "04 / 07" "$INNER"

INNER=$(cat <<HTML
    <div style="$H1;font-size:112px;line-height:1.14;">[1위를 암시하는<br>한 줄]</div>
    <div style="width:200px;height:14px;background:$ONACC;"></div>
    <div style="font-size:44px;line-height:1.5;color:$FSUB;">[다음 장에서 밝힙니다]</div>
HTML
)
emit 랭킹-강조.dc.html "랭킹" "06 / 07" "$INNER" flip

INNER=$(cat <<HTML
    <div style="display:inline-flex;align-self:flex-start;background:$ACC;color:$ONACC;font-size:34px;font-weight:700;padding:16px 32px;">1위</div>
    <div style="$H1;font-size:110px;line-height:1.1;">[1위 항목]</div>
    <div style="background:$SURF;padding:44px;font-size:40px;line-height:1.6;">[1위인 이유를 세 줄로.<br>여기서 가장 강한 사실 하나를<br>터뜨립니다]</div>
    <div style="background:$ACC;color:$ONACC;padding:40px;font-size:44px;font-weight:700;line-height:1.4;">다음 편은 [다음 주제]<br>팔로우하고 기다리세요</div>
HTML
)
emit 랭킹-마무리.dc.html "랭킹" "07 / 07" "$INNER"

echo "템플릿 5종 x 4장 = 20장 생성 완료"
