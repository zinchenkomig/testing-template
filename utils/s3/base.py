import abc

from fastapi import UploadFile
from minio import Minio
import logging


class S3StorageBase:

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def upload_file(self, path, file: UploadFile):
        self._logger.info(f"Uploading {path}")

    def get_file_url(self, path):
        return f'https://testing.s3{path}'


class S3Storage(S3StorageBase):

    def __init__(self, endpoint, access_key, secret_key, bucket_name):
        super().__init__()
        self.endpoint = endpoint
        self.client = Minio(endpoint=endpoint,
                            access_key=access_key, secret_key=secret_key,
                            cert_check=False)
        self.bucket_name = bucket_name

    def upload_file(self, path, file: UploadFile):
        self.client.put_object(
            self.bucket_name, path, file.file, file.size, content_type=file.content_type
        )

    def get_file_url(self, path):
        return f'https://{self.endpoint}/{self.bucket_name}{path}'

