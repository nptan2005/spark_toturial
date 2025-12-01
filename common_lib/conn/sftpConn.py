import os
import re
import stat
import time
import paramiko
from pathlib import PurePosixPath, PureWindowsPath

from ..config_models import configuration
from ..logging_utils import setup_logger
from .conn_kit_constants import ConnKitConstant


class SftpConn:
    """
    Lightweight SFTP wrapper for:
    - connect / retry
    - upload / download / move / copy
    - check file / folder
    - create nested folder
    - detect server OS (Windows/Linux)
    """

    def __init__(self,
                 connectionName: str = ConnKitConstant.SFTP_CONN_DEFAULT,
                 source_path: str = None,
                 destination_path: str = None):

        if not connectionName:
            raise ValueError("connectionName cannot be None")

        self._config = configuration.sftp[connectionName]
        self._connectionName = connectionName
        self._os_type = "unknown"

        self._source_path = source_path
        self._destination_path = destination_path
        self._is_successful = False

        self._ssh = None
        self._sftp = None

        self._logger = setup_logger("SFTP")
        self._logger.setLevel(30)

        self._connect_with_retry()

    # ---------------------------------------------------------------------
    # Context Manager
    # ---------------------------------------------------------------------
    def __enter__(self):
        self._logger.info(f"[ENTER] SFTP Ready: {self._connectionName}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ---------------------------------------------------------------------
    # Connection
    # ---------------------------------------------------------------------
    def _connect_with_retry(self, retries=3, delay=4):
        """
        Simple retry logic.
        """
        for attempt in range(1, retries + 1):
            try:
                self._ssh = paramiko.SSHClient()
                self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self._ssh.connect(
                    hostname=self._config.host,
                    port=self._config.port,
                    username=self._config.username,
                    password=self._config.password,
                    timeout=10
                )

                self._sftp = self._ssh.open_sftp()
                self._os_type = self._detect_remote_os()
                self._logger.info(f"[CONNECTED] SFTP {self._connectionName} (OS={self._os_type})")
                self._is_successful = True
                return

            except Exception as e:
                self._logger.warning(f"[RETRY {attempt}] Connect fail → {e}")
                time.sleep(delay)

        self._logger.error("[FAILED] Cannot establish SFTP connection.")

    def close(self):
        try:
            if self._sftp:
                self._sftp.close()
            if self._ssh:
                self._ssh.close()
            self._logger.info(f"[CLOSE] Closed connection {self._connectionName}")
        except Exception as e:
            self._logger.error(f"[CLOSE ERROR] {e}")

    # ---------------------------------------------------------------------
    # Helper: OS Detection & Path Normalize
    # ---------------------------------------------------------------------
    def _detect_remote_os(self):
        """
        Detect OS by probing common system paths.
        """
        try:
            self._sftp.stat("/etc")
            return "linux"
        except Exception:
            pass

        try:
            self._sftp.stat("C:\\Windows")
            return "windows"
        except Exception:
            pass

        return "unknown"

    def _to_remote_path(self, path: str) -> str:
        """
        Convert path to correct OS format.
        """
        if not path:
            return path

        if self._os_type == "windows":
            return str(PureWindowsPath(path))
        else:
            return str(PurePosixPath(path).as_posix())

    # ---------------------------------------------------------------------
    # General Existence Checks
    # ---------------------------------------------------------------------
    def is_file(self, remote_path: str) -> bool:
        remote = self._to_remote_path(remote_path)
        try:
            st = self._sftp.stat(remote)
            return stat.S_ISREG(st.st_mode)
        except Exception:
            return False

    def is_dir(self, remote_path: str) -> bool:
        remote = self._to_remote_path(remote_path)
        try:
            st = self._sftp.stat(remote)
            return stat.S_ISDIR(st.st_mode)
        except Exception:
            return False

    # ---------------------------------------------------------------------
    # Directory Creation
    # ---------------------------------------------------------------------
    def ensure_dir(self, remote_dir: str):
        """
        Create folder recursively.
        """
        remote = self._to_remote_path(remote_dir)

        parts = remote.replace("\\", "/").split("/")
        cur = ""

        for part in parts:
            if not part:
                continue
            cur = f"{cur}/{part}".replace("//", "/")
            try:
                self._sftp.stat(cur)
            except FileNotFoundError:
                self._logger.info(f"[MKDIR] {cur}")
                self._sftp.mkdir(cur)

        return True

    def ensure_daily_dir(self, remote_base: str):
        d = time.strftime("%Y%m%d")
        path = f"{remote_base}/{d}"
        if self.ensure_dir(path):
            return self._to_remote_path(path)
        return None

    # ---------------------------------------------------------------------
    # File Operations
    # ---------------------------------------------------------------------
    def read_file(self) -> str | None:
        try:
            remote = self._to_remote_path(self._source_path)
            if not self.is_file(remote):
                return None
            with self._sftp.open(remote, "r") as f:
                return f.read().decode()
        except Exception as e:
            self._logger.error(f"[READ ERROR] {e}")
            return None

    def upload(self):
        try:
            if not os.path.isfile(self._source_path):
                self._logger.warning(f"[UPLOAD] Local file not exist: {self._source_path}")
                return False

            base_dir = os.path.dirname(self._destination_path)
            daily_folder = self.ensure_daily_dir(base_dir)
            if not daily_folder:
                return False

            filename = os.path.basename(self._source_path)
            remote = f"{daily_folder}/{filename}"
            remote_final = self._to_remote_path(remote)

            self._sftp.put(self._source_path, remote_final)
            return True
        except Exception as e:
            self._logger.error(f"[UPLOAD ERROR] {e}")
            return False

    def download(self, delete_after=False):
        try:
            remote = self._to_remote_path(self._source_path)
            if not self.is_file(remote):
                return False

            self._sftp.get(remote, self._destination_path)
            if delete_after:
                self.delete(self._source_path)
            return True
        except Exception as e:
            self._logger.error(f"[DOWNLOAD ERROR] {e}")
            return False

    def move(self):
        try:
            src = self._to_remote_path(self._source_path)
            dst = self._to_remote_path(self._destination_path)

            if not self.is_file(src):
                return False

            self.ensure_dir(os.path.dirname(dst))
            self._sftp.rename(src, dst)
            return True
        except Exception as e:
            self._logger.error(f"[MOVE ERROR] {e}")
            return False

    def delete(self, remote_path: str):
        try:
            remote = self._to_remote_path(remote_path)
            if self.is_file(remote):
                self._sftp.remove(remote)
            return True
        except Exception as e:
            self._logger.error(f"[DELETE ERROR] {e}")
            return False

    def list_files(self, remote_dir: str, pattern: str = None):
        try:
            path = self._to_remote_path(remote_dir)
            if not self.is_dir(path):
                return []

            result = []
            for entry in self._sftp.listdir_attr(path):
                if stat.S_ISREG(entry.st_mode):
                    name = entry.filename
                    if pattern is None or re.match(pattern, name):
                        result.append(name)

            return result
        except Exception as e:
            self._logger.error(f"[LIST ERROR] {e}")
            return []