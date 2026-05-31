from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "China Intangible Cultural Heritage Platform API"
    app_env: str = "dev"
    app_debug: bool = True
    api_prefix: str = "/api/v1"

    # Database (PostgreSQL)
    database_url: str = ""
    admin_username: str = "admin"
    admin_password: str = ""
    admin_token: str = ""

    doubao_api_url: str = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    doubao_api_key: str = ""
    doubao_model: str = "doubao-seed-2-0-pro-260215"
    # ── 豆包 TTS 配置（主引擎） ──
    doubao_tts_appid: str = ""          # 豆包语音 APP ID
    doubao_tts_access_token: str = ""   # 豆包语音 Access Token（Header 鉴权用）
    doubao_tts_speaker: str = "zh_female_vv_uranus_bigtts"  # 默认音色：Vivi 2.0（活泼自然）
    doubao_tts_encoding: str = "mp3"    # 音频编码 mp3/wav/ogg_opus
    doubao_tts_speed: float = 1.0       # 语速 [0.1, 2]
    doubao_tts_volume: float = 1.0      # 音量 [0.5, 2]

    # ── Edge TTS 配置（降级回退） ──
    tts_voice: str = "zh-CN-XiaoyiNeural"
    tts_rate: str = "+0%"
    tts_volume: str = "+0%"
    tts_storage_dir: str = "storage/tts"
    ai_system_prompt: str = (
        "你是「黑塔」，中国非物质文化遗产数字平台的AI导览官。"
        "你像一位博学的非遗守护者：温润如玉、娓娓道来，既有学者的深度，又有讲故事的天赋。"
        "服务范围：中国非物质文化遗产的所有方面——传统技艺、戏曲艺术、民俗节庆、非遗保护政策、传承人故事和体验方式。"
        "超出范围的问题，温和引导回非遗话题。"
        "严禁编造项目背景、人物、年份、地域、政策和保护成果。不确定的信息宁可不说。"
        "回答风格：自然优雅的口语化中文，像在茶室里聊天。控制在200字左右，重点突出。"
        "禁止使用编号、项目符号、Markdown格式、来源说明或免责声明。"
        "当你知道用户关注的方向时，主动关联推荐，例如：'说到这里，你可能也会对XX感兴趣。'"
        "你可以推荐平台的非遗内容文章、线下体验活动和社区讨论话题，但不要承诺纪录片、线下场馆参观、课程报名等平台不提供的功能。"
    )

    @property
    def db_url(self) -> str:
        """PostgreSQL connection URL. Set DATABASE_URL in .env or environment."""
        url = self.database_url
        if not url:
            raise ValueError(
                "DATABASE_URL is not set. "
                "Example: postgresql://heritage:heritage123@localhost:5432/heritage"
            )
        return url

    @property
    def backend_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()

# ── 启动时校验关键配置 ──
import logging as _cfg_logging
_cfg_logger = _cfg_logging.getLogger("app.config")

_missing = []
if not settings.database_url:
    _missing.append("DATABASE_URL")
if not settings.admin_token:
    _missing.append("ADMIN_TOKEN")
if not settings.doubao_api_key:
    _cfg_logger.warning("DOUBAO_API_KEY 未配置，AI功能将不可用")
if _missing:
    _cfg_logger.critical("缺少必要环境变量: %s — 请在 .env 中配置", ", ".join(_missing))
    raise SystemExit(1)

