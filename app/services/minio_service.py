import logging
from typing import Optional

from minio import Minio
from minio.error import S3Error
from app.core.config import settings

logger = logging.getLogger(__name__)

class MinioService:
    """
    用于于minio交互的service层
    """
    def __init__(self):
        """
        初始化minio
        """
        try:
            self.client = Minio(
                endpoint= settings.MINIO_ENDPOINT,
                access_key= settings.MINIO_ACCESS_KEY,
                secret_key= settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            logger.info("初始化minio成功!")
        except Exception as e:
            logger.error(f"初始化minio失败: {e}")
            self.client = None

    def check_bucket_exists_and_create(self,bucket_name: str):
        """
        校验存储桶是否存在，如果不存在就创建一个
        :param bucket_name:
        :return:
        """
        if not self.client:
            logger.error("请先初始化minio")
            return
        try:
            found = self.client.bucket_exists(bucket_name)
            if not found:
                self.client.make_bucket(bucket_name)
                logger.info(f"成功创建存储桶: {bucket_name}")
            else:
                logger.info(f"存储桶已存在: {bucket_name}")
        except S3Error as e:
            logger.error(f"创建存储桶:{bucket_name}失败: {e}")

    def generate_presigned_upload_url(self, bucket_name: str, object_name: str, expires_in_minutes: int = 15) -> Optional[str]:
        """
        生成一个用于PUT请求的预签名上传URL。

        :param bucket_name: 存储桶名称。
        :param object_name: 在存储桶中的对象名称（文件路径）。
        :param expires_in_minutes: URL的有效时间（分钟）。
        :return: 预签名URL字符串，如果失败则返回None。
        """
        if not self.client:
            logger.error("MinIO客户端未初始化，无法生成URL。")
            return None

        from datetime import timedelta
        try:
            # 使用presigned_put_object生成上传URL
            url = self.client.presigned_put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=timedelta(minutes=expires_in_minutes)
            )
            logger.info(f"成功为对象 '{object_name}' 生成预签名上传URL")
            return url
        except S3Error as e:
            logger.error(f"为对象 '{object_name}' 生成预签名URL失败: {e}")
            return None

    def create_multipart_upload(self, bucket_name: str, object_name: str) -> Optional[str]:
        """
        初始化一个分片上传任务，并返回upload_id。

        :param bucket_name: 存储桶名称。
        :param object_name: 在存储桶中的对象名称（文件路径）。
        :return: upload_id字符串，如果失败则返回None。
        """
        if not self.client:
            logger.error("MinIO客户端未初始化，无法创建分片上传任务。")
            return None
        try:
            # 使用create_multipart_upload初始化
            upload_id = self.client._create_multipart_upload(bucket_name, object_name)
            logger.info(f"成功为对象 '{object_name}' 创建分片上传任务，Upload ID: {upload_id}")
            return upload_id
        except S3Error as e:
            logger.error(f"为对象 '{object_name}' 创建分片上传任务失败: {e}")
            return None

    def complete_multipart_upload(self, bucket_name: str, object_name: str, upload_id: str, parts: list) -> bool:
        """
        完成分片上传，将所有分片合并成一个对象。

        :param bucket_name: 存储桶名称。
        :param object_name: 对象名称。
        :param upload_id: 初始化时获取的Upload ID。
        :param parts: 分片信息列表，格式为{'part_number': int, 'etag': str}。
        :return: 成功返回True，失败返回False。
        """
        if not self.client:
            logger.error("MinIO客户端未初始化，无法完成分片上传。")
            return False
        try:
            # 使用complete_multipart_upload完成合并
            self.client._complete_multipart_upload(bucket_name, object_name, upload_id, parts)
            logger.info(f"成功合并对象 '{object_name}' (Upload ID: {upload_id})")
            return True
        except S3Error as e:
            logger.error(f"合并对象 '{object_name}' (Upload ID: {upload_id}) 失败: {e}")
            return False

    def list_uploaded_parts(self, bucket_name: str, object_name: str, upload_id: str) -> Optional[list]:
        """
        查询一个分片上传任务中所有已成功上传的分片。

        :param bucket_name: 存储桶名称。
        :param object_name: 对象名称。
        :param upload_id: 初始化时获取的Upload ID。
        :return: 包含分片信息的列表，失败则返回None。
        """
        if not self.client:
            logger.error("MinIO客户端未初始化，无法查询分片列表。")
            return None
        try:
            parts = self.client._list_parts(bucket_name, object_name, upload_id)
            return list(parts)
        except S3Error as e:
            logger.error(f"查询对象 '{object_name}' (Upload ID: {upload_id}) 的分片列表失败: {e}")
            return None

    def stat_object(self, bucket_name: str, object_name: str):
        """
        获取对象的状态信息。如果对象不存在，会抛出S3Error异常。
        """
        if not self.client:
            logger.error("MinIO客户端未初始化，无法获取对象状态。")
            raise ConnectionError("MinIO client not initialized")
        return self.client.stat_object(bucket_name, object_name)

    def download_file(self, bucket_name: str, object_name: str) -> Optional[bytes]:
        """
        从MinIO下载一个文件。

        :param bucket_name: 存储桶名称。
        :param object_name: 对象名称。
        :return: 文件的二进制内容，如果失败则返回None。
        """
        if not self.client:
            logger.error("MinIO客户端未初始化，无法下载文件。")
            return None
        try:
            response = self.client.get_object(bucket_name, object_name)
            file_data = response.read()
            logger.info(f"成功从MinIO下载文件: {object_name}")
            return file_data
        except S3Error as e:
            logger.error(f"从MinIO下载文件 {object_name} 失败: {e}")
            return None
        finally:
            if 'response' in locals() and response:
                response.close()
                response.release_conn()

    def generate_presigned_download_url(self, bucket_name: str, object_name: str, expires_in_minutes: int = 60) -> Optional[str]:
        """
        生成一个用于GET请求的预签名下载URL。

        :param bucket_name: 存储桶名称。
        :param object_name: 对象名称。
        :param expires_in_minutes: URL的有效时间（分钟）。
        :return: 预签名URL字符串，如果失败则返回None。
        """
        if not self.client:
            logger.error("MinIO客户端未初始化，无法生成下载URL。")
            return None

        from datetime import timedelta
        try:
            url = self.client.get_presigned_url(
                "GET",
                bucket_name=bucket_name,
                object_name=object_name,
                expires=timedelta(minutes=expires_in_minutes),
            )
            logger.info(f"成功为对象 '{object_name}' 生成预签名下载URL")
            return url
        except S3Error as e:
            logger.error(f"为对象 '{object_name}' 生成预签名下载URL失败: {e}")
            return None

# 创建一个全局minioService实例
minio_service = MinioService()
# 检查默认桶是否存在
minio_service.check_bucket_exists_and_create(settings.MINIO_DEFAULT_BUCKET)