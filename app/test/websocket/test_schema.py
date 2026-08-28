from app.schemas.websocket import WebSocketEvent

# correct schema
# event = WebSocketEvent(
#     event="NODE_MOVED",
#     version=1,
#     payload={
#         "node_id": "node-1",
#         "position": {
#             "x": 300,
#             "y": 200,
#         },
#     },
# )

# wrong schema
event = WebSocketEvent(
    event="HELLO_WORLD",
    version=1,
    payload={},
)

print(event)
print(event.model_dump())