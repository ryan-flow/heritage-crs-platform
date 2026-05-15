"""SQLAlchemy models package."""

from app.models.activity import Activity  # noqa: F401
from app.models.activity_registration import ActivityRegistration  # noqa: F401
from app.models.ai_qa_log import AIQALog  # noqa: F401
from app.models.content import Content  # noqa: F401
from app.models.content_favorite import ContentFavorite  # noqa: F401
from app.models.crs_ask_log import CrsAskLog  # noqa: F401
from app.models.crs_session import CrsSession  # noqa: F401
from app.models.discussion_comment import DiscussionComment  # noqa: F401
from app.models.discussion_like import DiscussionLike  # noqa: F401
from app.models.discussion_extra import DiscussionFavorite, DiscussionTopicTag  # noqa: F401
from app.models.discussion_topic import DiscussionTopic  # noqa: F401
from app.models.electronic_material import ElectronicMaterial  # noqa: F401
from app.models.local_knowledge_base import LocalKnowledgeBase  # noqa: F401
from app.models.recommend_log import RecommendLog  # noqa: F401
from app.models.user import User  # noqa: F401
