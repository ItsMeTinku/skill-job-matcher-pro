"""models/__init__.py — imports all models so SQLAlchemy finds them."""
from .user import User        # noqa: F401
from .resume import Resume    # noqa: F401
from .job import Job          # noqa: F401
from .match import MatchResult  # noqa: F401
from .user_skill import UserSkill  # noqa: F401
