from nonebot import get_plugin_config
from pydantic import BaseModel, Field, field_validator


RETRY_TIMES = 3
RETRY_DELAY = 1.0


class Config(BaseModel):
    """维维语录插件配置"""

    vvquest_max_num: int = Field(default=10, description="最大返回图片数量限制 (1-50)")
    vvquest_use_forward: bool = Field(default=True, description="是否使用合并转发消息")
    vvquest_api_base: str = Field(
        default="",
        description="本地API完整地址（如 http://localhost:8000/search），留空使用默认在线API",
    )
    vvquest_cooldown: int = Field(
        default=30, description="API请求冷却时间（秒），防止频繁请求 (1-300)"
    )

    @field_validator("vvquest_max_num")
    @classmethod
    def check_max_num(cls, v: int) -> int:
        """验证最大返回数量"""
        return max(1, min(50, v))

    @field_validator("vvquest_cooldown")
    @classmethod
    def check_cooldown(cls, v: int) -> int:
        """验证冷却时间"""
        return max(1, min(300, v))


plugin_config = get_plugin_config(Config)
