import boto3
import cloudinary
import cloudinary.uploader
import io
import json
import os
from dotenv import load_dotenv

# โหลดค่าจาก .env
load_dotenv()

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

# โหลด config แล้วเติมค่าจาก .env
def get_config():
    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)

    # ✅ แทนค่า .env ลงใน config ทุกครั้ง
    cfg["aws"]["bucket"] = os.getenv("bucketAWS", cfg["aws"].get("bucket", ""))
    cfg["aws"]["region"] = os.getenv("regionAWS", cfg["aws"].get("region", ""))
    cfg["aws"]["access_key"] = os.getenv("accessKeyAWS", cfg["aws"].get("access_key", ""))
    cfg["aws"]["secret_key"] = os.getenv("secretKeyAWS", cfg["aws"].get("secret_key", ""))

    cfg["cloudinary"]["cloud_name"] = os.getenv("cloudnameCLOUDINARY", cfg["cloudinary"].get("cloud_name", ""))
    cfg["cloudinary"]["api_key"] = os.getenv("apikeyCLOUDINARY", cfg["cloudinary"].get("api_key", ""))
    cfg["cloudinary"]["api_secret"] = os.getenv("apisecretCLOUDINARY", cfg["cloudinary"].get("api_secret", ""))

    return cfg


def get_active_provider():
    return get_config()["active_provider"]


def set_active_provider(name):
    cfg = get_config()
    cfg["active_provider"] = name
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


# Factory: เลือก client ตาม provider ที่กำลังใช้งาน
def get_client():
    cfg = get_config()
    provider = cfg["active_provider"]

    if provider == "aws":
        a = cfg["aws"]
        s3 = boto3.client(
            "s3",
            region_name=a["region"],
            aws_access_key_id=a["access_key"],
            aws_secret_access_key=a["secret_key"]
        )
        return S3Client(s3, a["bucket"])

    elif provider == "cloudinary":
        c = cfg["cloudinary"]
        cloudinary.config(
            cloud_name=c["cloud_name"],
            api_key=c["api_key"],
            api_secret=c["api_secret"]
        )
        return CloudinaryClient()

    else:
        raise ValueError(f"Unknown provider: {provider}")


# ----------------- AWS S3 client -----------------
class S3Client:
    def __init__(self, s3, bucket):
        self.s3 = s3
        self.bucket = bucket

    def upload(self, fileobj, filename):
        self.s3.upload_fileobj(fileobj, self.bucket, filename)
        return filename

    def list(self):
        objs = self.s3.list_objects_v2(Bucket=self.bucket).get("Contents", [])
        return [{"key": o["Key"], "size": o["Size"]} for o in objs]

    def download(self, key):
        buff = io.BytesIO()
        self.s3.download_fileobj(self.bucket, key, buff)
        return buff.getvalue()

    def delete(self, key):
        self.s3.delete_object(Bucket=self.bucket, Key=key)


# ----------------- Cloudinary client -----------------
class CloudinaryClient:
    def upload(self, fileobj, filename):
        res = cloudinary.uploader.upload(fileobj, public_id=filename)
        return res["secure_url"]

    def list(self):
        from cloudinary.api import resources
        res = resources(max_results=30)
        return [{"key": r["public_id"], "size": r["bytes"]} for r in res["resources"]]

    def download(self, key):
        from urllib.request import urlopen
        url = cloudinary.CloudinaryImage(key).build_url()
        return urlopen(url).read()

    def delete(self, key):
        cloudinary.uploader.destroy(key)
