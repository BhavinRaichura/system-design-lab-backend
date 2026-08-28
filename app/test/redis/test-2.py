from app.db.redis import redis_client

print(redis_client.ping())