#!/usr/bin/env bash
# 템플릿과 제작물을 한 장짜리 미리보기 HTML 로 모읍니다. (브라우저에서 바로 열림)
set -e
cd "$(dirname "$0")"

OUT=preview.html
SCALE=0.30
SEARCH="../템플릿 ../제작/2026-09-01_결혼식축의금 ."

# .dc.html 에서 카드 본체만 뽑고, 남아있는 테마 홀은 기본색으로 치환
extract() {
  awk '/<\/helmet>/{f=1;next} /<\/x-dc>/{f=0} f' "$1" \
  | sed -e 's/{{t\.bg}}/#F2ECE1/g' \
        -e 's/{{t\.surface}}/#FFFFFF/g' \
        -e 's/{{t\.ink}}/#16130E/g' \
        -e 's/{{t\.sub}}/#6A6154/g' \
        -e 's/{{t\.accent}}/#B0202B/g' \
        -e 's/{{t\.onAccent}}/#FFFFFF/g' \
        -e 's/{{t\.line}}/#DDD2BF/g'
}

# card <파일> <라벨>
card() {
  SRC=""
  for d in $SEARCH; do [ -f "$d/$1" ] && { SRC="$d/$1"; break; }; done
  [ -n "$SRC" ] || { echo "없음: $1" >&2; return; }
  echo "<figure><div class=\"frame\"><div class=\"inner\">" >> $OUT
  extract "$SRC" >> $OUT
  echo "</div></div><figcaption>$2</figcaption></figure>" >> $OUT
}

# 카테고리 4장 한 줄
set4() {
  echo "<h2>$1</h2><div class=\"row\">" >> $OUT
  card "$1-표지.dc.html" "표지"
  card "$1-본문.dc.html" "본문"
  card "$1-강조.dc.html" "강조 (색반전)"
  card "$1-마무리.dc.html" "마무리"
  echo '</div>' >> $OUT
}

cat > $OUT <<EOF
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>카드뉴스 템플릿</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap">
<style>
  body { margin:0; padding:48px; background:#2A2723; color:#EDE7DC;
         font-family:'IBM Plex Sans KR','Malgun Gothic',sans-serif; }
  h1 { font-size:26px; margin:0 0 8px; letter-spacing:-0.01em; }
  h2 { font-size:15px; font-weight:600; letter-spacing:0.12em; color:#B9AE9C;
       margin:56px 0 20px; padding-bottom:10px; border-bottom:1px solid #4A443C; }
  p.lead { font-size:14px; color:#B9AE9C; margin:0 0 8px; line-height:1.6; }
  .row { display:flex; flex-wrap:wrap; gap:24px; }
  figure { margin:0; display:flex; flex-direction:column; gap:8px; }
  .frame { width:calc(1080px * $SCALE); height:calc(1350px * $SCALE);
           overflow:hidden; background:#fff; }
  .inner { width:1080px; height:1350px; transform:scale($SCALE);
           transform-origin:top left; }
  figcaption { font-size:12px; color:#B9AE9C; letter-spacing:0.02em; }
</style>
</head>
<body>
<h1>카드뉴스 템플릿</h1>
<p class="lead">1080 &times; 1350 원본을 30% 로 줄여서 보여줍니다. 파일 이름은 주제풀 태그와 같습니다.</p>
EOF

echo '<h2>공통 골격</h2><div class="row">' >> $OUT
card Skeleton.dc.html "골격 스펙"
card Themes.dc.html "테마 5종"
echo '</div>' >> $OUT

set4 반전상식
set4 현실기준
set4 심리테스트
set4 혜택
set4 랭킹

echo '<h2>제작물 — 결혼식 축의금 10장</h2><div class="row">' >> $OUT
card Main.dc.html "01 표지"
for i in 02 03 04 05 06 07 08 09 10; do card "Card$i.dc.html" "$i"; done
echo '</div>' >> $OUT

echo '</body></html>' >> $OUT
echo "$OUT 생성 완료"
