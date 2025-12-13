import asyncio
import aiofiles
import logging
from typing import Any, Callable
from fastapi import UploadFile, HTTPException
from pathlib import Path
from PIL import Image
from io import BytesIO

logger = logging.getLogger("examarchitect")


class NigerianNetworkAdapter:
    """Handles network operations with resilience for Nigerian conditions"""

    @staticmethod
    async def robust_api_call(
            api_call: Callable[[], Any],
            max_retries: int = 3,
            timeout: int = 30,
            backoff_factor: float = 2.0
    ) -> Any:
        """Execute API call with retry logic"""
        for attempt in range(max_retries):
            try:
                coro = api_call()
                return await asyncio.wait_for(coro, timeout=timeout)
            except (asyncio.TimeoutError, ConnectionError, Exception) as e:
                logger.warning(f"API call attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                wait_time = backoff_factor ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)

    @staticmethod
    async def compress_and_save_upload(
            file: UploadFile,
            dest_path: Path,
            max_dimensions: tuple = (1024, 1024),  # Renamed to match FileProcessor
            max_bytes: int = 10 * 1024 * 1024,
            compress_images: bool = True,
            quality: int = 75  # Added missing parameter
    ) -> Path:
        """
        Save upload to dest_path with optional image compression.
        """
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # CRITICAL FIX: Reset file pointer before reading
            # This prevents saving 0-byte files if the file was read previously
            await file.seek(0)

            # Check if file is an image
            file_ext = dest_path.suffix.lower()
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}

            if compress_images and file_ext in image_extensions:
                # Compress image
                return await NigerianNetworkAdapter._compress_and_save_image(
                    file, dest_path, max_dimensions, max_bytes, quality
                )
            else:
                # Save as-is with size validation
                size = 0
                async with aiofiles.open(dest_path, 'wb') as out_f:
                    while True:
                        chunk = await file.read(1024 * 1024)  # 1MB chunks
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > max_bytes:
                            # Cleanup
                            await out_f.close()
                            if dest_path.exists():
                                dest_path.unlink()
                            raise HTTPException(
                                status_code=413,
                                detail=f"File too large. Max size: {max_bytes / 1024 / 1024}MB"
                            )
                        await out_f.write(chunk)

                logger.info(f"Saved file: {dest_path.name} ({size} bytes)")

                # Reset pointer again for subsequent processors (OCR/RAG)
                await file.seek(0)
                return dest_path

        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Failed to save upload: {e}")
            if dest_path.exists():
                try:
                    dest_path.unlink()
                except:
                    pass
            raise HTTPException(500, f"File upload failed: {str(e)}")

    @staticmethod
    async def _compress_and_save_image(
            file: UploadFile,
            dest_path: Path,
            max_size: tuple,
            max_bytes: int,
            quality: int = 75
    ) -> Path:
        """Compress and save image file."""
        try:
            content = await file.read()

            if len(content) > max_bytes:
                raise HTTPException(413, f"File too large. Max size: {max_bytes / 1024 / 1024}MB")

            def compress_sync():
                img = Image.open(BytesIO(content))
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background

                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)

                img.save(dest_path, 'JPEG', quality=quality, optimize=True)
                return dest_path.stat().st_size

            compressed_size = await asyncio.to_thread(compress_sync)

            # Reset file pointer
            await file.seek(0)
            return dest_path

        except Exception as e:
            logger.error(f"Image compression failed: {e}")
            # Fallback to saving original
            async with aiofiles.open(dest_path, 'wb') as f:
                await f.write(content)
            await file.seek(0)
            return dest_path