"""知识库 API 的请求/响应模型。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="", max_length=2000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("知识库名称不能为空")
        return stripped


class KnowledgeBaseOut(BaseModel):
    id: str
    name: str
    description: str
    document_count: int = 0
    created_at: datetime
    updated_at: datetime


class DocumentOut(BaseModel):
    id: str
    knowledge_base_id: str
    filename: str
    file_size: int
    status: str
    chunk_count: int
    error_message: str
    created_at: datetime
    updated_at: datetime
