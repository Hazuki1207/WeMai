import time
import threading
import logging
from pathlib import Path
from queue import Queue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class WxImageHandler(FileSystemEventHandler):
    def __init__(self, image_queue: Queue):
        self.image_queue = image_queue

    def on_created(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)

        if path.name.startswith("微信图片_") and path.suffix.lower() == ".jpg":
            # 等文件写完
            time.sleep(0.2)

            try:
                if path.exists() and path.stat().st_size > 0:
                    logger.warning(f"📸 捕获微信图片落盘: {path}")
                    self.image_queue.put(str(path))
            except Exception as e:
                logger.error(f"处理图片事件失败: {e}")


class WxImageWatcher:
    def __init__(self, watch_dir: Path):
        self.watch_dir = watch_dir
        self.queue = Queue()
        self.observer = Observer()

    def start(self):
        handler = WxImageHandler(self.queue)
        self.observer.schedule(handler, str(self.watch_dir), recursive=False)
        self.observer.start()

        logger.warning(f"👀 watchdog 正在监听目录: {self.watch_dir}")

    def stop(self):
        self.observer.stop()
        self.observer.join()
