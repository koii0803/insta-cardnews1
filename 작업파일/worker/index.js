// 인스타 예약발행 Worker. 사용자가 직접 만질 일 없음.
// 크론(매시 :00·:45)에 깨서:
//   1) R2 insta-cards/예약.json 에서 시간 지난 건을 찾아 R2 이미지를 base64로 묶어 Make 웹훅 전송
//      성공 → insta-cards/발행대장.txt 한 줄 / 실패 → insta-cards/오류기록.txt 한 줄
//      어느 쪽이든 예약에서 빼고, 24시간 뒤 이미지를 지우도록 insta-cards/삭제예약.json 에 적는다
//   2) 삭제예약.json 에서 시간 지난 건의 R2 이미지를 지운다
// 웹훅 주소는 Worker Secret MAKE_WEBHOOK 으로만 들어온다. insta-cards/ 밖은 절대 안 지운다.

const PREFIX = "insta-cards/";
const 큐키 = PREFIX + "예약.json";
const 삭제키 = PREFIX + "삭제예약.json";
const 발행대장키 = PREFIX + "발행대장.txt";
const 오류키 = PREFIX + "오류기록.txt";

function 한국시각(d = new Date()) {
  // "YYYY-MM-DDTHH:MM" (Asia/Seoul)
  const p = new Intl.DateTimeFormat("sv-SE", {
    timeZone: "Asia/Seoul", year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hour12: false }).format(d);
  return p.replace(" ", "T");
}

async function 읽기JSON(env, key) {
  const o = await env.R2.get(key);
  if (!o) return [];
  try { return JSON.parse(await o.text()); } catch { return []; }
}
async function 쓰기JSON(env, key, v) {
  await env.R2.put(key, JSON.stringify(v, null, 1), { httpMetadata: { contentType: "application/json" } });
}
async function 줄추가(env, key, 줄) {
  const o = await env.R2.get(key);
  const 기존 = o ? await o.text() : "";
  await env.R2.put(key, 기존 + 줄 + "\n", { httpMetadata: { contentType: "text/plain; charset=utf-8" } });
  console.log(줄);
}

function b64(buf) {
  let s = "", bytes = new Uint8Array(buf);
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(s);
}

async function 전송(env, 항목) {
  // 성공 null, 실패 이유 문자열 (확인서버.py의 전송과 같은 페이로드)
  const images = [];
  for (const img of 항목.images) {
    const o = await env.R2.get(PREFIX + 항목.folder + "/" + img.name);
    if (!o) return `R2에 이미지 없음 (${img.name})`;
    images.push({ name: img.name, data: b64(await o.arrayBuffer()) });
  }
  const body = JSON.stringify({ caption: 항목.caption, count: images.length, images });
  if (body.length > 4_500_000) return `전송 용량 초과 (${Math.floor(body.length / 1_000_000)}MB)`;
  try {
    const r = await fetch(env.MAKE_WEBHOOK, { method: "POST", headers: { "Content-Type": "application/json" }, body });
    if (r.status !== 200) return `Make 응답 ${r.status}`;
  } catch (e) { return `Make 전송 실패: ${e}`; }
  return null;
}

async function 발행(env, now) {
  const 목록 = await 읽기JSON(env, 큐키);
  const today = now.slice(0, 10);
  const 실행할 = 목록.filter(x => x.time <= now);
  if (!실행할.length) { console.log("아직 시간 안 된 예약", 목록.length, "건"); return; }
  if (!env.MAKE_WEBHOOK) { console.log("MAKE_WEBHOOK 시크릿 미등록 — 큐 유지"); return; }
  const 삭제목록 = await 읽기JSON(env, 삭제키);
  const 이후 = 한국시각(new Date(Date.now() + 24 * 3600 * 1000));
  for (const 항목 of 실행할) {
    const 이유 = await 전송(env, 항목);
    if (이유) await 줄추가(env, 오류키, `${today} 예약발행 실패: ${항목.folder} ${이유}`);
    else {
      const 제목 = 항목.folder.split(/_(.+)/)[1] || 항목.folder;
      await 줄추가(env, 발행대장키, `${today} [${항목.category || "미상"}] ${제목} (자동예약)`);
    }
    삭제목록.push({ folder: 항목.folder, keys: 항목.images.map(i => PREFIX + 항목.folder + "/" + i.name), delete_after: 이후 });
  }
  await 쓰기JSON(env, 큐키, 목록.filter(x => x.time > now));
  await 쓰기JSON(env, 삭제키, 삭제목록);
}

async function 청소(env, now) {
  const 목록 = await 읽기JSON(env, 삭제키);
  const 지울것 = 목록.filter(x => x.delete_after <= now);
  if (!지울것.length) return;
  const 남김 = 목록.filter(x => x.delete_after > now);
  for (const 항목 of 지울것) {
    try {
      for (const key of 항목.keys) { if (!key.startsWith(PREFIX)) throw new Error("접두어 밖: " + key); await env.R2.delete(key); }
      console.log("R2 삭제 완료:", 항목.folder);
    } catch (e) { 남김.push(항목); console.log("R2 삭제 실패(다음에 재시도):", 항목.folder, e); }
  }
  await 쓰기JSON(env, 삭제키, 남김);
}

async function 한바퀴(env) {
  const now = 한국시각();
  await 발행(env, now);
  await 청소(env, now);
  return now;
}

export default {
  async scheduled(event, env, ctx) { ctx.waitUntil(한바퀴(env)); },
  async fetch(req, env) {
    // 상태 보기: GET / → 큐·삭제예약 JSON. 수동 실행: GET /run?token=<RUN_TOKEN 시크릿>
    const url = new URL(req.url);
    if (url.pathname === "/run") {
      if (!env.RUN_TOKEN || url.searchParams.get("token") !== env.RUN_TOKEN) return new Response("금지", { status: 403 });
      return new Response("실행 " + await 한바퀴(env));
    }
    const 큐 = await 읽기JSON(env, 큐키);
    return new Response(JSON.stringify({ now: 한국시각(), 예약: 큐.map(x => ({ folder: x.folder, time: x.time })) }, null, 1),
      { headers: { "Content-Type": "application/json; charset=utf-8" } });
  },
};
