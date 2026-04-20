import os
import threading
from pathlib import Path

import win32con
import win32file

ACTIONS = {
  1: "created",
  2: "deleted",
  3: "modified",
  4: "renamed_from",
  5: "renamed_to",
}


class FolderWatcher(threading.Thread):
  def __init__(self, path: Path, callback: Callable):
    super().__init__(daemon=True)
    self.path = path
    self.callback = callback

  def run(self):
    hDir = win32file.CreateFile(
      self.path,
      win32con.FILE_LIST_DIRECTORY,
      win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
      None,
      win32con.OPEN_EXISTING,
      win32con.FILE_FLAG_BACKUP_SEMANTICS,
      None,
    )

    while True:
      results = win32file.ReadDirectoryChangesW(
        hDir,
        4096,
        True,
        win32con.FILE_NOTIFY_CHANGE_FILE_NAME
        | win32con.FILE_NOTIFY_CHANGE_DIR_NAME
        | win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES
        | win32con.FILE_NOTIFY_CHANGE_SIZE
        | win32con.FILE_NOTIFY_CHANGE_LAST_WRITE,
        None,
      )

      for action, filename in results:
        full_path = os.path.join(self.path, filename)
        self.callback(action, full_path)
