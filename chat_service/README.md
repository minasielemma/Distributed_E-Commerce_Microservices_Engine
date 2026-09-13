# Chat Service Guidelines

Please see the root documentation file [`CHAT_SERVICE_GUIDELINES.md`](file:///home/minasie/Desktop/micro_service/CHAT_SERVICE_GUIDELINES.md) for mandatory rules on:
1. Frontend `extractRoomId` property lookup order (`room_id` / `room` before `id`).
2. Dual `room` and `room_id` serialization standards on `ChatMessageSerializer`.
3. `broadcast_room_ws` and WebSocket consumer payload integrity.
4. Container test verification with `docker exec micro_service-chat_service-1 python manage.py test chat.tests`.
