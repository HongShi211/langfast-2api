import httpx
import json
import uuid
import time
import asyncio
import base64
from typing import Dict, Any, AsyncGenerator, Optional

from fastapi.responses import StreamingResponse, JSONResponse
from loguru import logger

from app.core.config import settings
from app.services.credential_manager import CredentialManager
from app.services.socketio_manager import SocketIOManager
from app.utils.sse_utils import create_sse_data, create_chat_completion_chunk, DONE_CHUNK, create_chat_completion_response

# 日志记录辅助函数 (无变动)
async def log_request(request):
    logger.debug(f"--- [HTTP Request] --->")
    logger.debug(f"Request: {request.method} {request.url}")
    logger.debug(f"Headers: {request.headers}")
    if request.content:
        try:
            content = json.loads(request.content)
            logger.debug(f"Body: \n{json.dumps(content, indent=2, ensure_ascii=False)}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.debug(f"Body (raw): {request.content}")
    logger.debug(f"--- [HTTP Request] ---")

async def log_response(response):
    await response.aread()
    logger.debug(f"<--- [HTTP Response] ---")
    logger.debug(f"Status: {response.status_code}")
    logger.debug(f"Headers: {response.headers}")
    try:
        content = response.json()
        logger.debug(f"Body: \n{json.dumps(content, indent=2, ensure_ascii=False)}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.debug(f"Body (raw): {response.text}")
    logger.debug(f"<--- [HTTP Response] ---")

# JWT 解码辅助函数 (无变动)
def get_user_id_from_token(token: str) -> Optional[str]:
    if not token: return None
    try:
        parts = token.split('.')
        if len(parts) != 3: return None
        payload_b64 = parts[1]
        payload_b64 += '=' * (-len(payload_b64) % 4)
        payload_json = base64.b64decode(payload_b64).decode('utf-8')
        payload = json.loads(payload_json)
        return payload.get('sub')
    except Exception as e:
        logger.error(f"从 token 解码用户 ID 时发生错误: {e}", exc_info=True)
        return None

class LangfastProvider:
    def __init__(self):
        self.credential_manager = CredentialManager()
        self.initiate_url = f"{settings.SUPABASE_URL}/functions/v1/initiate-prompt-run"
        self.client = httpx.AsyncClient(
            timeout=30.0,
            event_hooks={'request': [log_request], 'response': [log_response]}
        )

    async def initialize(self):
        await self.credential_manager.initialize()

    async def close(self):
        await self.credential_manager.close()
        await self.client.aclose()

    # --- [修改] 重构 chat_completion 以支持流式和非流式 ---
    async def chat_completion(self, request_data: Dict[str, Any]) -> StreamingResponse | JSONResponse:
        is_streaming = request_data.get("stream", False)
        request_id = f"chatcmpl-{uuid.uuid4()}"
        model = request_data.get("model", settings.DEFAULT_MODEL)

        try:
            access_token = await self.credential_manager.get_credential()
            user_id = get_user_id_from_token(access_token)
            if not user_id:
                raise Exception("无法从凭证中解析用户ID，请求中断。")

            socket_manager = SocketIOManager(access_token, settings.SOCKET_URL)
            await socket_manager.connect()

            headers = {
                "apikey": settings.SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            # 【关键修改】在准备 payload 时过滤不支持的参数
            payload = self._prepare_payload(request_data, user_id)

            logger.info(f"正在向上游发送聊天触发请求 (stream={is_streaming})...")
            response = await self.client.post(self.initiate_url, headers=headers, json=payload)
            response.raise_for_status()
            logger.success("聊天触发请求成功。等待 Socket.IO 数据...")

            if is_streaming:
                return StreamingResponse(
                    self._stream_generator(request_id, model, socket_manager),
                    media_type="text/event-stream"
                )
            else:
                final_data = await self._collect_full_response(socket_manager)
                await socket_manager.disconnect()
                response_json = create_chat_completion_response(
                    request_id,
                    model,
                    final_data.get("content", ""),
                    final_data.get("finish_reason", "stop")
                )
                return JSONResponse(content=response_json)

        except Exception as e:
            logger.error(f"处理聊天请求时发生顶层错误: {e}", exc_info=True)
            if is_streaming:
                async def error_stream():
                    chunk = create_chat_completion_chunk(request_id, model, f"内部服务器错误: {e}", "stop")
                    yield create_sse_data(chunk)
                    yield DONE_CHUNK
                return StreamingResponse(error_stream(), media_type="text/event-stream")
            else:
                return JSONResponse(
                    status_code=500,
                    content={"error": {"message": f"内部服务器错误: {e}", "type": "server_error"}}
                )

    # --- [修改] 实现增量计算的流式生成器 ---
    async def _stream_generator(self, request_id: str, model: str, socket_manager: SocketIOManager) -> AsyncGenerator[str, None]:
        last_content = ""
        try:
            while not socket_manager.is_finished.is_set():
                data = await socket_manager.get_data()
                if data is None:
                    break

                full_content = data.get("content", "")
                if full_content and full_content != last_content:
                    # 计算增量
                    delta_content = full_content[len(last_content):]
                    chunk = create_chat_completion_chunk(request_id, model, delta_content)
                    yield create_sse_data(chunk)
                    last_content = full_content
        
        except Exception as e:
            logger.error(f"处理流时发生严重错误: {e}", exc_info=True)
            error_chunk = create_chat_completion_chunk(request_id, model, f"内部服务器错误: {e}", "stop")
            yield create_sse_data(error_chunk)
        finally:
            final_chunk = create_chat_completion_chunk(request_id, model, "", "stop")
            yield create_sse_data(final_chunk)
            yield DONE_CHUNK
            await socket_manager.disconnect()

    # --- [新增] 用于非流式响应的函数 ---
    async def _collect_full_response(self, socket_manager: SocketIOManager) -> Dict[str, Any]:
        final_data = {}
        while not socket_manager.is_finished.is_set():
            data = await socket_manager.get_data()
            if data is None:
                break
            final_data = data # 不断覆盖，直到最后一个
        return final_data

    # --- [关键修改] 修改 _prepare_payload 方法以过滤不支持的参数 ---
    def _prepare_payload(self, request_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        # 定义上游不支持的参数列表
        # 根据错误日志 "Unsupported parameter: 'temperature' is not supported with this model."
        # 我们将这些参数从发送给上游的请求中移除
        unsupported_params = {
            'temperature', 'top_p', 'frequency_penalty', 'presence_penalty', 'max_tokens'
        }
        
        # 过滤 prompt_meta 中的参数
        prompt_meta = {
            "model": request_data.get("model", settings.DEFAULT_MODEL),
            "messages": request_data.get("messages", []),
            # 移除不支持的参数，但保留默认值以防内部逻辑需要
            # "temperature": request_data.get("temperature", 0.7),
            # "top_p": request_data.get("top_p", 1),
            # "frequency_penalty": request_data.get("frequency_penalty", 0),
            # "presence_penalty": request_data.get("presence_penalty", 0),
            # "max_completion_tokens": request_data.get("max_tokens", 16384),
            "response_format": "text",
            "stream": True, # 上游始终使用流式，由我们决定如何返回给客户端
        }
        
        # 记录被过滤的参数，方便调试
        filtered_params = []
        for param in unsupported_params:
            if param in request_data:
                filtered_params.append(param)
        
        if filtered_params:
            logger.info(f"已过滤掉上游不支持的参数: {', '.join(filtered_params)}")
        
        return {
            "run_id": str(uuid.uuid4()),
            "prompt_id": "6456df9f-f4fd-42b3-97ff-df29af7188b7",
            "prompt_meta": prompt_meta,
            "test_cases": [],
            "created_by": user_id
        }

    async def get_models(self) -> JSONResponse:
        return JSONResponse(content={
            "object": "list",
            "data": [{"id": name, "object": "model", "created": int(time.time()), "owned_by": "lzA6"} for name in settings.KNOWN_MODELS]
        })
