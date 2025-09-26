from enum import Enum

class FileStatus(str, Enum):
    """
    文件处理状态枚举。
    继承自str，使其值可以直接被序列化为JSON。
    """
    PENDING = "pending"          # 待处理/待上传：记录已创建，但上传尚未开始。
    UPLOADING = "uploading"      # 上传中：已生成上传凭证，文件正在上传过程中。
    COMPLETED = "completed"      # 上传完成/待处理：文件已成功上传到对象存储，等待后续处理（如向量化）。
    PROCESSING = "processing"    # 向量化处理中：向量化任务已启动，正在进行中。
    VECTORIZED = "vectorized"    # 向量化完成：文件已成功向量化并存入向量数据库。
    FAILED = "failed"            # 处理失败：在任何步骤中发生不可恢复的错误。

class SupportedMimeTypes(str, Enum):
    """
    系统支持或计划支持的MIME类型枚举。
    """
    # --- 文本文档 (当前核心支持) ---
    PDF = "application/pdf"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    DOC = "application/msword"
    TXT = "text/plain"
    MD = "text/markdown"
    JSON = "application/json"
    XML = "application/xml"
    HTML = "text/html"
    CSV = "text/csv"

    # --- 演示文稿 ---
    PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    PPT = "application/vnd.ms-powerpoint"

    # --- 电子表格 ---
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    XLS = "application/vnd.ms-excel"

    # --- 常见图片 (未来可支持) ---
    PNG = "image/png"
    JPEG = "image/jpeg"
    GIF = "image/gif"
    WEBP = "image/webp"
    SVG = "image/svg+xml"

    # --- 常见音频 (未来可支持) ---
    MP3 = "audio/mpeg"
    WAV = "audio/wav"

    # --- 常见视频 (未来可支持) ---
    MP4 = "video/mp4"
    MOV = "video/quicktime"

# 创建一个集合，方便快速检查一个MIME类型是否被支持
# 初期我们只支持文本文档
SUPPORTED_DOCUMENT_MIME_TYPES = {
    SupportedMimeTypes.PDF.value,
    SupportedMimeTypes.DOCX.value,
    SupportedMimeTypes.DOC.value,
    SupportedMimeTypes.TXT.value,
    SupportedMimeTypes.MD.value,
    SupportedMimeTypes.JSON.value,
    SupportedMimeTypes.XML.value,
    SupportedMimeTypes.HTML.value,
    SupportedMimeTypes.CSV.value,
}
