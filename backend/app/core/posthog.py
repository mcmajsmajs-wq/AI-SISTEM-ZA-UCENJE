# -*- coding: utf-8 -*-
"""
PostHog analytics client — initialized once at import time.
Import posthog_client from here; never import from app.main.
"""

import logging
import atexit
from app.core.config import settings

logger = logging.getLogger(__name__)

_posthog_api_key = getattr(settings, "POSTHOG_API_KEY", None) or ""
_posthog_host = getattr(settings, "POSTHOG_HOST", None) or "https://app.posthog.com"

try:
    from posthog import Posthog

    if _posthog_api_key:
        posthog_client = Posthog(
            project_api_key=_posthog_api_key,
            host=_posthog_host,
        )
    else:
        posthog_client = Posthog(
            project_api_key="",
            host=_posthog_host,
            disabled=True,
        )
    atexit.register(posthog_client.shutdown)
except ImportError:
    logger.warning("posthog not installed, analytics disabled")
    posthog_client = None
except Exception as e:
    logger.warning(f"Failed to initialize posthog: {e}")
    posthog_client = None
