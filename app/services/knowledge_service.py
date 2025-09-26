import logging
from typing import Optional, List, Dict, Any
from sqlmodel import Session

from app.core.constants import FileStatus
from app.models.knowledge import KnowledgeFile
from app.services.minio_service import minio_service
from app.core.config import settings
from app.core.exceptions import ApiException

logger = logging.getLogger(__name__)

class KnowledgeService:

    def initiate_file_upload(
        self,
        session: Session,
        admin_user_id: int,
        filename: str,
        file_ext: Optional[str],
        mime_type: Optional[str],
        size_in_bytes: Optional[int],
        part_count: int,
        multipart: bool,
        file_hash: Optional[str] = None,
        knowledge_base_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        处理文件上传请求，根据是否分片返回不同的凭证，并存储完整文件信息。
        """
        # 1. 在数据库中创建文件记录，包含所有已知信息
        db_file = KnowledgeFile(
            filename=filename,
            file_ext=file_ext,
            mime_type=mime_type,
            size_in_bytes=size_in_bytes,
            admin_user_id=admin_user_id,
            knowledge_base_id=knowledge_base_id,
            file_hash=file_hash,
            status="pending"  # 初始状态
        )
        session.add(db_file)
        session.flush()  # 获取新记录的ID

        file_id = db_file.id
        object_name = f"kb_{knowledge_base_id or 'uncategorized'}/{file_id}/{filename}"
        db_file.file_path = object_name  # 设置文件在MinIO中的路径

        # 2. 根据是否分片，执行不同逻辑
        if multipart:
            # --- 分片上传逻辑 ---
            upload_id = minio_service.create_multipart_upload(
                bucket_name=settings.MINIO_DEFAULT_BUCKET,
                object_name=object_name
            )
            if not upload_id:
                raise ApiException("无法在MinIO中创建分片上传任务")

            db_file.upload_id = upload_id  # 存储upload_id
            db_file.status = "uploading"  # 更新状态为待上传
            session.add(db_file)

            presigned_urls = []
            for i in range(1, part_count + 1):
                url = minio_service.generate_presigned_upload_url(
                    bucket_name=settings.MINIO_DEFAULT_BUCKET,
                    object_name=object_name
                )
                if url:
                    presigned_urls.append({"part_number": i, "url": url})

            if len(presigned_urls) != part_count:
                raise ApiException("生成部分分片的上传URL失败")

            return {
                "file_id": file_id,
                "multipart": True,
                "upload_id": upload_id,
                "presigned_urls": presigned_urls
            }
        else:
            # --- 普通单文件上传逻辑 ---
            presigned_url = minio_service.generate_presigned_upload_url(
                bucket_name=settings.MINIO_DEFAULT_BUCKET,
                object_name=object_name,
                expires_in_minutes=20
            )
            if not presigned_url:
                raise ApiException("无法生成文件上传URL")

            db_file.status = "uploading"
            session.add(db_file)

            return {
                "file_id": file_id,
                "multipart": False,
                "presigned_url": presigned_url
            }

    def finalize_upload(self, session: Session, file_id: int) -> KnowledgeFile:
        """
        验证并确认文件上传完成（支持分片和非分片），成功后更新数据库状态。
        """
        # 1. 从数据库获取文件信息
        db_file = session.get(KnowledgeFile, file_id)
        if not db_file:
            raise ApiException(f"文件记录不存在: {file_id}")
        if not db_file.file_path:
            raise ApiException(f"文件 {file_id} 缺少有效的对象路径")

        # 2. 判断是分片上传还是单文件上传
        if db_file.upload_id:
            # --- 分片上传确认逻辑 ---
            logger.info(f"开始合并分片文件: {file_id}")
            # 从MinIO查询已上传的分片列表
            uploaded_parts = minio_service.list_uploaded_parts(
                bucket_name=settings.MINIO_DEFAULT_BUCKET,
                object_name=db_file.file_path,
                upload_id=db_file.upload_id
            )

            if uploaded_parts is None:
                raise ApiException("无法从MinIO获取分片信息")

            # 准备合并所需的分片信息
            parts_for_completion = [
                {"part_number": part.part_number, "etag": part.etag}
                for part in uploaded_parts
            ]

            # 执行合并
            success = minio_service.complete_multipart_upload(
                bucket_name=settings.MINIO_DEFAULT_BUCKET,
                object_name=db_file.file_path,
                upload_id=db_file.upload_id,
                parts=parts_for_completion
            )

            if not success:
                db_file.status = FileStatus.FAILED
                session.add(db_file)
                raise ApiException("在MinIO中合并文件失败")
        else:
            # --- 单文件上传确认逻辑 ---
            logger.info(f"开始确认单文件上传: {file_id}")
            # 通过stat_object检查文件是否存在于MinIO中
            try:
                minio_service.stat_object(settings.MINIO_DEFAULT_BUCKET, db_file.file_path)
            except Exception as e:
                db_file.status = FileStatus.FAILED
                session.add(db_file)
                logger.error(f"确认文件 {file_id} 在MinIO中失败: {e}")
                raise ApiException("文件上传失败，未在存储中找到该文件")

        # 3. 统一更新数据库状态为'completed'，并准备触发后续任务
        db_file.status = FileStatus.COMPLETED
        session.add(db_file)

        # TODO: 在这里触发向量化后台任务
        # background_tasks.add_task(vectorize_file, file_id)
        logger.info(f"文件 {file_id} 已成功上传并确认，状态更新为completed。")

        return db_file

# 创建一个全局KnowledgeService实例
knowledge_service = KnowledgeService()
