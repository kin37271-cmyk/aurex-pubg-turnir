import asyncio
import os
import re
import shutil
import logging
from typing import Optional

logger = logging.getLogger("AurexTunnel")

class CloudflareTunnelManager:
    """Cloudflare Quick Tunnel (trycloudflare.com) boshqaruvchi klassi"""
    
    def __init__(self, port: int = 8080, exe_name: str = "cloudflared.exe"):
        self.port = port
        self.exe_name = exe_name
        self.process: Optional[asyncio.subprocess.Process] = None
        self.tunnel_url: Optional[str] = None
        self._drain_task: Optional[asyncio.Task] = None

    def find_executable(self) -> Optional[str]:
        """Loyiha katalogi yoki tizim PATH dan cloudflared.exe ni topish"""
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        local_exe = os.path.join(current_dir, self.exe_name)
        if os.path.exists(local_exe):
            return local_exe
        
        path_exe = shutil.which(self.exe_name)
        if path_exe:
            return path_exe
        return None

    def is_available(self) -> bool:
        return self.find_executable() is not None

    async def start(self, timeout: float = 30.0) -> Optional[str]:
        """Cloudflare tunnelni ishga tushirish va https://*.trycloudflare.com manzilini olish"""
        exe_path = self.find_executable()
        if not exe_path:
            logger.warning("⚠️ cloudflared.exe topilmadi. Avtomatik tunnel ishga tushirilmadi.")
            return None

        logger.info(f"🌐 Cloudflare HTTPS tunneli ishga tushirilmoqda (port {self.port})...")
        try:
            self.process = await asyncio.create_subprocess_exec(
                exe_path, "tunnel", "--url", f"http://127.0.0.1:{self.port}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
        except Exception as e:
            logger.error(f"❌ Cloudflare tunnelni ochishda xatolik: {e}")
            return None

        start_time = asyncio.get_event_loop().time()
        url_regex = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')

        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.warning(f"⚠️ Cloudflare tunnel URL aniqlanmadi (kutish vaqti tugadi - {timeout}s)")
                break

            try:
                line_bytes = await asyncio.wait_for(self.process.stdout.readline(), timeout=3.0)
            except asyncio.TimeoutError:
                if self.process.returncode is not None:
                    logger.error(f"❌ Cloudflare jarayoni to'xtab qoldi (exit code: {self.process.returncode})")
                    break
                continue

            if not line_bytes:
                if self.process.returncode is not None:
                    break
                continue

            line = line_bytes.decode("utf-8", errors="ignore").strip()
            match = url_regex.search(line)
            if match:
                self.tunnel_url = match.group(0)
                logger.info(f"✅ Cloudflare HTTPS Manzili tayyor: {self.tunnel_url}")
                break

        # Fonda qolgan loglarni o'qib turish (bufer to'lib qolmasligi uchun)
        self._drain_task = asyncio.create_task(self._drain_output())
        return self.tunnel_url

    async def _drain_output(self):
        try:
            while self.process and self.process.stdout and not self.process.stdout.at_eof():
                await self.process.stdout.readline()
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    async def stop(self):
        """Tunnel jarayonini to'xtatish"""
        if self._drain_task and not self._drain_task.done():
            self._drain_task.cancel()

        if self.process:
            logger.info("🛑 Cloudflare tunnel to'xtatilmoqda...")
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            logger.info("✅ Cloudflare tunnel to'xtatildi.")
            self.process = None
