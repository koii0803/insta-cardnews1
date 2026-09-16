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
