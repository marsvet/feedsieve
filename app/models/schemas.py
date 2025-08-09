"""
数据传输对象定义

使用 Pydantic 定义 API 的请求和响应模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from ..core.constants import RecordStatus


# 基础模型
class MediaItem(BaseModel):
    """媒体项目模型"""
    url: str
    type: str
    preview_image_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    blurhash: Optional[str] = None


class Feed(BaseModel):
    """Feed 源模型"""
    title: str
    description: Optional[str] = None
    siteUrl: str
    checkedAt: Optional[datetime] = None
    ttl: Optional[int] = None
    url: str
    lastModifiedHeader: Optional[str] = None
    etagHeader: Optional[str] = None
    rsshubRoute: Optional[str] = None
    rsshubNamespace: Optional[str] = None
    errorMessage: Optional[str] = None
    errorAt: Optional[datetime] = None


class Entry(BaseModel):
    """Feed 条目模型"""
    id: Optional[str] = None
    publishedAt: Optional[datetime] = None
    insertedAt: Optional[datetime] = None
    feedId: Optional[str] = None
    title: str
    description: Optional[str] = None
    content: str
    author: Optional[str] = None
    url: str
    guid: Optional[str] = None
    media: Optional[List[MediaItem]] = None


# Webhook 相关模型
class WebhookPayload(BaseModel):
    """Webhook 载荷模型"""
    entry: Entry
    feed: Feed
    view: int


# Record 相关模型
class RecordCreate(BaseModel):
    """创建记录请求模型"""
    feed_url: str
    title: Optional[str] = None
    summary: Optional[str] = None
    article_url: Optional[str] = None


class RecordUpdate(BaseModel):
    """更新记录请求模型"""
    status: Optional[RecordStatus] = None
    filter_result: Optional[Dict[str, Any]] = None
    filtered: Optional[bool] = None
    readwise_id: Optional[str] = None
    error_message: Optional[str] = None


class RecordResponse(BaseModel):
    """记录响应模型"""
    id: int
    feed_url: str
    title: Optional[str] = None
    summary: Optional[str] = None
    article_url: Optional[str] = None
    status: str
    filter_result: Optional[Dict[str, Any]] = None
    filtered: Optional[bool] = None
    readwise_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecordListResponse(BaseModel):
    """记录列表响应模型"""
    records: List[RecordResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Queue 相关模型
class QueueCreate(BaseModel):
    """创建队列项请求模型"""
    feed_url: str
    title: str
    content: str
    article_url: str


class QueueResponse(BaseModel):
    """队列项响应模型"""
    id: int
    feed_url: str
    title: str
    content: str
    article_url: str
    created_at: datetime

    class Config:
        from_attributes = True


# 统计相关模型
class RecordStats(BaseModel):
    """记录统计模型"""
    total: int
    skip: int
    success_filtered: int
    success_unfiltered: int
    failed: int
    success_rate: float


# 操作请求模型
class RetryRequest(BaseModel):
    """重试请求模型"""
    record_id: int


class DeleteRequest(BaseModel):
    """删除请求模型"""
    record_id: int


# 健康检查模型
class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    timestamp: datetime
    database: bool
    queue_service: bool
    details: Optional[Dict[str, Any]] = None


# 配置相关模型
class APIResponse(BaseModel):
    """通用 API 响应模型"""
    success: bool
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
