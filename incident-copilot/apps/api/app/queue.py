import redis
from rq import Queue

from app.settings import settings

redis_conn = redis.from_url(settings.redis_url)
incident_queue = Queue("incident", connection=redis_conn)

