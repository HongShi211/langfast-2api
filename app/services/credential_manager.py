import asyncio
import httpx
from collections import deque
from typing import Optional
from loguru import logger
from app.core.config import settings

class CredentialManager:
    def __init__(self):
        self.credentials = deque()
        self.lock = asyncio.Lock()
        self.signup_url = f"{settings.SUPABASE_URL}/auth/v1/signup"
        self.headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Content-Type": "application/json"
        }
        # 修正：为 httpx 客户端设置超时
        self.client = httpx.AsyncClient(timeout=30.0)

    async def initialize(self):
        logger.info("正在初始化凭证管理器...")
        await self.maintain_credentials()

    async def _create_new_credential(self) -> Optional[str]:
        try:
            logger.info("正在注册新的匿名账号...")
            # 修正：匿名注册的 body 是一个空 json
            response = await self.client.post(self.signup_url, headers=self.headers, json={})
            response.raise_for_status()
            data = response.json()
            access_token = data.get("access_token")
            if access_token:
                logger.success("成功获取新的匿名凭证。")
                return access_token
            else:
                logger.error(f"注册匿名账号失败，响应中缺少 'access_token': {data}")
                return None
        except httpx.RequestError as e:
            # 修正：捕获并记录更具体的网络错误
            logger.error(f"注册匿名账号时发生网络请求错误: {type(e).__name__} - {e}")
            return None
        except Exception as e:
            logger.error(f"注册匿名账号时发生未知错误: {e}", exc_info=True)
            return None

    async def maintain_credentials(self):
        async with self.lock:
            while len(self.credentials) < settings.MIN_CREDENTIALS:
                if len(self.credentials) >= settings.MAX_CREDENTIALS:
                    logger.info(f"凭证池已满 ({len(self.credentials)}个)，停止补充。")
                    break
              
                new_token = await self._create_new_credential()
                if new_token:
                    self.credentials.append(new_token)
                else:
                    logger.warning("无法创建新凭证，将在下次维护时重试。")
                    break

    async def get_credential(self) -> str:
        async with self.lock:
            if not self.credentials:
                logger.warning("凭证池为空，正在紧急补充...")
                await self.maintain_credentials()
                if not self.credentials:
                    raise Exception("无法获取任何有效凭证。")
          
            token = self.credentials.popleft()
            asyncio.create_task(self.maintain_credentials())
            logger.info(f"提供一个凭证，池中剩余: {len(self.credentials)}")
            return token

    async def close(self):
        await self.client.aclose()
