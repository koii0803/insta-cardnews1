# 카드 JPEG를 Cloudflare R2에 올리고 지우는 공용 모듈. 사용자가 직접 만질 일 없음.
# 계정·키는 환경변수로만 받는다 (PC엔 사용자 환경변수, 깃허브 액션엔 Secrets):
#   R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET, R2_PUBLIC_URL, CLOUDFLARE_ACCOUNT_ID_2
# babcheck-img 버킷을 다른 프로젝트와 나눠 쓰므로 insta-cards/ 접두어 밖은 절대 못 지운다.

import os
import urllib.parse

PREFIX = "insta-cards/"
변수들 = ("R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET",
          "R2_PUBLIC_URL", "CLOUDFLARE_ACCOUNT_ID_2")


def env():
    v = {k: os.environ.get(k, "").strip() for k in 변수들}
    빠짐 = [k for k in 변수들 if not v[k]]
    if 빠짐:
        raise RuntimeError("R2 환경변수 없음: " + ", ".join(빠짐))
    return v


def client():
    import boto3
    v = env()
    return boto3.client(
        "s3",
        endpoint_url="https://%s.r2.cloudflarestorage.com" % v["CLOUDFLARE_ACCOUNT_ID_2"],
        aws_access_key_id=v["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=v["R2_SECRET_ACCESS_KEY"])


def 키(폴더명, 파일명):
    return f"{PREFIX}{폴더명}/{파일명}"


def 공개주소(key):
    return env()["R2_PUBLIC_URL"].rstrip("/") + "/" + urllib.parse.quote(key)


def 올리기(로컬경로, key):
    client().upload_file(str(로컬경로), env()["R2_BUCKET"], key,
                         ExtraArgs={"ContentType": "image/jpeg"})
    return 공개주소(key)


def 지우기(key):
    if not key.startswith(PREFIX):
        raise RuntimeError(f"{PREFIX} 밖은 못 지움: {key}")
    client().delete_object(Bucket=env()["R2_BUCKET"], Key=key)


# ── 예약표·장부(글자 파일) ── Worker와 같은 자리를 읽고 쓴다
큐키 = PREFIX + "예약.json"
발행대장키 = PREFIX + "발행대장.txt"
오류키 = PREFIX + "오류기록.txt"


def 글읽기(key):
    # 없으면 "" (연결 실패는 예외로 올림)
    try:
        r = client().get_object(Bucket=env()["R2_BUCKET"], Key=key)
        return r["Body"].read().decode("utf-8")
    except client().exceptions.NoSuchKey:
        return ""


def 글쓰기(key, 내용, 종류="text/plain; charset=utf-8"):
    if not key.startswith(PREFIX):
        raise RuntimeError(f"{PREFIX} 밖은 못 씀: {key}")
    client().put_object(Bucket=env()["R2_BUCKET"], Key=key,
                        Body=내용.encode("utf-8"), ContentType=종류)


def 큐읽기():
    import json
    try:
        return json.loads(글읽기(큐키) or "[]")
    except Exception:
        return []


def 큐쓰기(목록):
    import json
    글쓰기(큐키, json.dumps(목록, ensure_ascii=False, indent=1), "application/json")
