import logging

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.auth import get_current_admin_user
from app.db.db import get_session
from app.models.user import AdminUser
from app.schemas.json_response import JsonData
from app.schemas.knowledge_schema import CompleteUploadRequest, UploadRequest
from app.services.knowledge_service import knowledge_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/file/v1",
    tags=["知识库"],
)


@router.post("/upload-request", summary="1. 请求文件上传凭证")
def request_file_upload(
        request_data: UploadRequest,
        session: Session = Depends(get_session),
        current_admin: AdminUser = Depends(get_current_admin_user)
) -> JsonData:
    """
    客户端在此端点请求上传许可。
    - 对于小文件, part_count=1, multipart=False。
    - 对于大文件, part_count>1, multipart=True。
    """
    logger.info(f"管理员 {current_admin.username} 请求上传文件: {request_data.filename}")

    multipart = request_data.part_count > 1

    upload_credentials = knowledge_service.initiate_file_upload(
        session=session,
        admin_user_id=current_admin.id,
        filename=request_data.filename,
        file_ext=request_data.file_ext,
        mime_type=request_data.mime_type,
        size_in_bytes=request_data.size_in_bytes,
        part_count=request_data.part_count,
        multipart=multipart,
        file_hash=request_data.file_hash,
        knowledge_base_id=request_data.knowledge_base_id
    )
    return JsonData.success(upload_credentials)


@router.post("/finalize-upload", summary="2. 确认文件上传完成")
def finalize_file_upload(
    request_data: CompleteUploadRequest,
    session: Session = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin_user)
) -> JsonData:
    """
    当客户端完成文件上传后（无论是分片还是单文件），调用此接口通知后端。
    后端将执行文件合并（如果是分片）或状态检查，并触发后续处理。
    """
    logger.info(f"管理员 {current_admin.username} 请求确认文件上传: {request_data.file_id}")

    db_file = knowledge_service.finalize_upload(
        session=session,
        file_id=request_data.file_id
    )

    return JsonData.success(data={"file_id": db_file.id, "status": db_file.status,"msg":"文件已确认上传，等待后续处理"})
