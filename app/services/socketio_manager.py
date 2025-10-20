import asyncio
import socketio
import json
from loguru import logger

class SocketIOManager:
    def __init__(self, access_token: str, socket_url: str):
        self.sio = socketio.AsyncClient(logger=False, engineio_logger=False)
        self.access_token = access_token
        self.socket_url = socket_url
        self.queue = asyncio.Queue()
        self.is_connected = asyncio.Event()
        self.is_finished = asyncio.Event()

        self._setup_event_handlers()

    def _setup_event_handlers(self):
        @self.sio.event
        async def connect():
            logger.success("Socket.IO 连接成功。")
            self.is_connected.set()

        @self.sio.event
        async def disconnect():
            logger.warning("Socket.IO 连接断开。")
            self.is_connected.clear()
            if not self.is_finished.is_set():
                await self.queue.put(None)
                self.is_finished.set()

        # --- [修改] 监听正确的事件名称 'execution:chunk' ---
        @self.sio.on('execution:chunk')
        async def on_execution_chunk(data):
            logger.debug(f"收到 'execution:chunk' 事件，内容: {data}")
            processed_data = data
            if isinstance(data, str):
                try:
                    processed_data = json.loads(data)
                except json.JSONDecodeError:
                    logger.warning(f"收到的字符串不是有效的JSON，将作为普通文本处理: {data}")
                    processed_data = {"content": data}
          
            if not isinstance(processed_data, dict):
                 logger.warning(f"处理后的数据仍然不是字典。类型: {type(processed_data)}")
                 processed_data = {"content": str(processed_data)}

            await self.queue.put(processed_data)
            
            # --- [新增] 检查完成状态 ---
            if processed_data.get('status') == 'completed':
                logger.info("Socket.IO 收到 'completed' 状态，标记为完成。")
                if not self.is_finished.is_set():
                    await self.queue.put(None)
                    self.is_finished.set()

        @self.sio.on('completion_finished')
        async def on_completion_finished(data):
            logger.info(f"Socket.IO 收到 'completion_finished' 事件。数据: {data}")
            if not self.is_finished.is_set():
                await self.queue.put(None)
                self.is_finished.set()
      
        @self.sio.on('*')
        async def catch_all(event, data):
            # --- [修改] 调整未知事件的日志，避免 'execution:chunk' 被重复记录 ---
            if event not in ['execution:chunk', 'completion_finished']:
                logger.info(f"捕获到未知 Socket.IO 事件: '{event}', 数据: {data}")

    async def connect(self):
        try:
            await self.sio.connect(
                self.socket_url,
                auth={'token': self.access_token},
                transports=['websocket'],
                wait_timeout=20
            )
            await self.is_connected.wait()
        except Exception as e:
            logger.error(f"Socket.IO 连接失败: {e}", exc_info=True)
            self.is_finished.set()
            raise

    async def disconnect(self):
        if self.sio.connected:
            await self.sio.disconnect()

    async def get_data(self):
        return await self.queue.get()
