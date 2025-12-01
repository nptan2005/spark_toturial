# dags/tasks/upload_to_gcs.py
from google.cloud import storage
import os, glob

def upload_to_gcs(local_dir, gcs_bucket, gcs_prefix):
    client = storage.Client(project=os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT"))
    bucket = client.bucket(gcs_bucket)
    for path in glob.glob(local_dir + '/**/*', recursive=True):
        if os.path.isfile(path):
            dest = os.path.join(gcs_prefix, os.path.relpath(path, local_dir))
            blob = bucket.blob(dest)
            blob.upload_from_filename(path)
            print("uploaded", path, "->", dest)