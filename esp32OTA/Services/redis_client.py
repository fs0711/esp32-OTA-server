import json
import logging
import redis
from esp32OTA.config import config

logger = logging.getLogger(__name__)

HISTORY_KEY_PREFIX = "mqtt:history:"


class RedisClient:
    def __init__(self) -> None:
        self._r: redis.Redis | None = None

    def connect(self) -> None:
        try:
            self._r = redis.Redis(
                host=getattr(config, "REDIS_HOST", "localhost"),
                port=getattr(config, "REDIS_PORT", 6379),
                password=getattr(config, "REDIS_PASSWORD", None) or None,
                db=getattr(config, "REDIS_DB", 0),
                decode_responses=True,
                socket_connect_timeout=5,
            )
            self._r.ping()
            logger.info("[REDIS] Connected at %s:%s", getattr(config, "REDIS_HOST", "localhost"), getattr(config, "REDIS_PORT", 6379))
        except Exception as exc:
            logger.error("[REDIS] Connection failed: %s", exc)
            self._r = None

    def disconnect(self) -> None:
        if self._r:
            self._r.close()

    def push_message(self, message: dict) -> None:
        """Store a message in capped topic history. message must have: topic, payload, qos, retain."""
        if not self._r:
            return
        key = HISTORY_KEY_PREFIX + message["topic"]
        history_length = getattr(config, "TOPIC_HISTORY_LENGTH", 30)
        try:
            pipe = self._r.pipeline()
            pipe.lpush(key, json.dumps(message))
            pipe.ltrim(key, 0, history_length - 1)
            pipe.execute()
        except Exception as exc:
            logger.warning("[REDIS] Push failed for topic '%s': %s", message.get("topic"), exc)

    def get_history(self, topic: str) -> list:
        """Return up to TOPIC_HISTORY_LENGTH messages for a topic, newest first."""
        if not self._r:
            return []
        key = HISTORY_KEY_PREFIX + topic
        try:
            return [json.loads(item) for item in self._r.lrange(key, 0, -1)]
        except Exception as exc:
            logger.warning("[REDIS] Get history failed for topic '%s': %s", topic, exc)
            return []

    def get_all_topics(self) -> list:
        """Return all topic paths that have stored history."""
        if not self._r:
            return []
        try:
            keys = self._r.keys(HISTORY_KEY_PREFIX + "*")
            return [k[len(HISTORY_KEY_PREFIX):] for k in keys]
        except Exception as exc:
            logger.warning("[REDIS] Keys lookup failed: %s", exc)
            return []


redis_client = RedisClient()
