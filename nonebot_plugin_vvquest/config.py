from pydantic import BaseModel, field_validator

class Config(BaseModel):
    # 配置前缀
    __config_name__ = "vvquest"
    """维维语录插件配置"""
    max_num: int = 10
    """最大返回图片数量限制 (1-50)"""
    use_forward: bool = True
    """是否使用合并转发消息"""
    api_base: str = ""
    """本地API完整地址（如 http://localhost:8000/search），留空使用默认在线API"""
    cooldown: int = 30
    """API请求冷却时间（秒），防止频繁请求 (1-300)"""

    @field_validator("max_num")
    @classmethod
    def check_max_num(cls, v: int) -> int:
        """验证最大返回数量"""
        return max(1, min(50, v))

    @field_validator("cooldown")
    @classmethod
    def check_cooldown(cls, v: int) -> int:
        """验证冷却时间"""
        return max(1, min(300, v))