"""In-process mock server for testing Gnani STT WebSocket streaming."""

import asyncio
import json
from typing import Any, Dict, List, Optional
from websockets.asyncio.server import serve, ServerConnection


class FakeSttServer:
    """Mock server running on websockets.asyncio.server.serve simulating Gnani STT WebSocket."""

    def __init__(self, close_with_4001: bool = False):
        self.close_with_4001 = close_with_4001
        self.recorded_headers: Dict[str, str] = {}
        self.frames_received: List[bytes] = []
        self.server = None
        self.port: Optional[int] = None

    async def handler(self, websocket: ServerConnection):
        # Record upgrade headers from request.headers
        if hasattr(websocket, "request") and hasattr(websocket.request, "headers"):
            self.recorded_headers = {k.lower(): v for k, v in websocket.request.headers.items()}
        elif hasattr(websocket, "request_headers"):
            self.recorded_headers = {k.lower(): v for k, v in websocket.request_headers.items()}

        if self.close_with_4001:
            await websocket.close(code=4001, reason="Unauthorized API Key")
            return

        # Send connected
        connected_msg = {
            "type": "connected",
            "message": "Connected successfully",
            "timestamp": 123456789,
            "config": {"sample_rate": 16000, "chunk_size": 1024},
        }
        await websocket.send(json.dumps(connected_msg))

        segment_index = 0
        frame_counter = 0

        async for message in websocket:
            if isinstance(message, bytes):
                self.frames_received.append(message)
                frame_counter += 1

                # Every 20 frames, send processing and transcript
                if frame_counter % 20 == 0:
                    await websocket.send(json.dumps({"type": "processing", "timestamp": 12345}))
                    transcript_msg = {
                        "type": "transcript",
                        "timestamp": 12346,
                        "text": f"Mock segment {segment_index}",
                        "audio_duration_ms": 640,
                        "segment_id": f"seg-{segment_index}",
                        "segment_index": segment_index,
                        "latency": 150,
                    }
                    await websocket.send(json.dumps(transcript_msg))
                    segment_index += 1

    async def start(self) -> int:
        self.server = await serve(self.handler, "127.0.0.1", 0)
        for sock in self.server.sockets:
            self.port = sock.getsockname()[1]
            break
        return self.port

    async def stop(self) -> None:
        if self.server:
            self.server.close()
            await self.server.wait_closed()
