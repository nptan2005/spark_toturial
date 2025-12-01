# dags/tasks/copy_silver_to_local.py
from minio import Minio
import os, shutil, glob

client = Minio("minio:9000",
               access_key=os.getenv("MINIO_ROOT_USER","admin"),
               secret_key=os.getenv("MINIO_ROOT_PASSWORD","admin123"),
               secure=False)

# download parquet folder
def download_parquet(bucket='silver', prefix='parquet/transactions', local_dir='/tmp/silver/transactions'):
    if os.path.exists(local_dir):
        shutil.rmtree(local_dir)
    os.makedirs(local_dir)
    # list objects under prefix
    for obj in client.list_objects(bucket, prefix=prefix, recursive=True):
        dest = os.path.join(local_dir, os.path.relpath(obj.object_name, prefix))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        client.fget_object(bucket, obj.object_name, dest)
    return local_dir