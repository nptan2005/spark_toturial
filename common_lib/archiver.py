from pathlib import Path
from datetime import datetime
import shutil

from common_lib.logging_utils import setup_logger


class FileArchiver:
    """
    Safe file archiving utility with logging + date folder + name conflict handling.
    """
    def __init__(self, source: str, destination: str):
        self._source = Path(source)
        self._destination = Path(destination)
        self._note = ""
        self.logger = setup_logger("ARCHIVE")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.info("[FileArchiver] Exit context")
        self._source = None
        self._destination = None
        self._note = None

    @property
    def note(self):
        return self._note

    # -------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------
    def _ensure_folder(self, path: Path):
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            msg = f"[FileArchiver][ensure_folder] Cannot create folder '{path}': {e}"
            self.logger.error(msg)
            raise RuntimeError(msg)

    def _resolve_name_conflict(self, dest_path: Path) -> Path:
        """
        If file exists → append _1, _2, _3...
        """
        if not dest_path.exists():
            return dest_path

        stem = dest_path.stem
        suffix = dest_path.suffix
        parent = dest_path.parent

        counter = 1
        while True:
            new_path = parent / f"{stem}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1

    def _move_file(self, src: Path, dst: Path):
        if not src.exists():
            raise FileNotFoundError(f"Source not found: {src}")

        resolved_dst = self._resolve_name_conflict(dst)

        try:
            shutil.move(str(src), str(resolved_dst))
            self.logger.info(f"[FileArchiver] Move OK → {resolved_dst}")
            return resolved_dst
        except Exception as e:
            msg = f"[FileArchiver][move_file] Move failed: {e}"
            self._note += msg
            self.logger.error(msg)
            raise

    # -------------------------------------------------------
    # Public APIs
    # -------------------------------------------------------
    @property
    def archive_file(self):
        """
        Archive file → destination/YYYYMMDD/<filename.ext>
        Return None if successful, else error string.
        """
        if not self._source.is_file():
            return f"File '{self._source}' does not exist"

        # Folder by date
        current_date = datetime.now().strftime("%Y%m%d")
        dated_folder = self._destination / current_date

        try:
            self._ensure_folder(dated_folder)
        except Exception as e:
            return f"[archive_file] Can't prepare folder → {e}"

        dest_path = dated_folder / self._source.name

        try:
            self._move_file(self._source, dest_path)
        except Exception as e:
            return f"[archive_file] Move error → {e}"

        return None

    @property
    def archive_folder(self):
        """
        Archive file directly into folder → destination/<filename.ext>
        Return None if ok.
        """
        if not self._source.is_file():
            return f"File '{self._source}' does not exist"

        try:
            self._ensure_folder(self._destination)
        except Exception as e:
            return f"[archive_folder] Can't prepare folder → {e}"

        dest_path = self._destination / self._source.name

        try:
            self._move_file(self._source, dest_path)
        except Exception as e:
            return f"[archive_folder] Move failed → {e}"

        return None