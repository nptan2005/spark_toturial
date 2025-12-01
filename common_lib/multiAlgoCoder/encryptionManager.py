import os
from pathlib import Path
import threading
from typing import Dict, ClassVar

from pydantic import BaseModel, Field
from ..utilities.utils import Utils as utils
from .decoder import decoder


class _SingletonBase:
    """
    Thread-safe singleton base.
    """
    _instances = {}
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__new__(cls)
                cls._instances[cls] = instance
        return cls._instances[cls]


class EncryptionManager(BaseModel, _SingletonBase):
    """
    Manage encrypted password/key files located under:
       common_lib/bin/{data, iv, key}

    This class is:
    - Pydantic-safe (no non-annotated fields)
    - Singleton-safe
    """

    # ===============================================================
    # CONSTANT PATHS (ClassVar — NOT Pydantic fields)
    # ===============================================================
    ROOT_BIN: ClassVar[Path] = Path(__file__).resolve().parent.parent / "bin"

    DATA_FOLDER: ClassVar[Path] = ROOT_BIN / "data"
    IV_FOLDER: ClassVar[Path] = ROOT_BIN / "iv"
    KEY_FOLDER: ClassVar[Path] = ROOT_BIN / "key"

    MASTER_KEY_FILE: ClassVar[Path] = KEY_FOLDER / "master_key_ase.bin"
    MASTER_KEY_IV_FILE: ClassVar[Path] = IV_FOLDER / "master_key_iv_ase.bin"
    KEY_FILE: ClassVar[Path] = KEY_FOLDER / "key_ase.bin"

    # ===============================================================
    # REAL Pydantic fields
    # ===============================================================
    master_key: bytes = Field(default_factory=bytes)
    iv_master_key: bytes = Field(default_factory=bytes)
    key: bytes = Field(default_factory=bytes)

    encryption_dict: Dict[str, bytes] = Field(default_factory=dict)
    iv_dict: Dict[str, bytes] = Field(default_factory=dict)

    # ===============================================================
    # INIT
    # ===============================================================
    def __init__(self, **data):
        super().__init__(**data)
        self._load_core_keys()
        self._load_all_encryption_data()

    # ===============================================================
    # LOAD KEYS
    # ===============================================================
    def _load_core_keys(self):
        self.master_key = utils.readFile(self.MASTER_KEY_FILE, "rb")
        self.iv_master_key = utils.readFile(self.MASTER_KEY_IV_FILE, "rb")
        self.key = utils.readFile(self.KEY_FILE, "rb")

    # ===============================================================
    # LOAD ENCRYPTION MAP
    # ===============================================================
    def _load_folder(self, folder: Path, target_dict: Dict[str, bytes]):
        if not folder.exists():
            return
        for f in folder.iterdir():
            if f.suffix == ".bin":
                key_prefix = f.stem.split("_")[0]
                if key_prefix not in target_dict:
                    target_dict[key_prefix] = utils.readFile(f, "rb")

    def _load_all_encryption_data(self):
        self._load_folder(self.DATA_FOLDER, self.encryption_dict)
        self._load_folder(self.IV_FOLDER, self.iv_dict)

    # ===============================================================
    # UPDATE FUNCTIONS
    # ===============================================================
    def update_encryption_data(self):
        """Refresh data & IV folder."""
        self._load_folder(self.DATA_FOLDER, self.encryption_dict)
        self._load_folder(self.IV_FOLDER, self.iv_dict)

    # ===============================================================
    # GETTERS — Auto-load if missing
    # ===============================================================
    def get_encrypted_data(self, key_prefix: str) -> bytes:
        if key_prefix not in self.encryption_dict:
            self._load_all_encryption_data()
        return self.encryption_dict.get(key_prefix)

    def get_iv(self, key_prefix: str) -> bytes:
        if key_prefix not in self.iv_dict:
            self._load_all_encryption_data()
        return self.iv_dict.get(key_prefix)

    # ===============================================================
    # DECRYPT
    # ===============================================================
    def decrypt(self, key_prefix: str) -> bytes:
        data = self.get_encrypted_data(key_prefix)
        iv = self.get_iv(key_prefix)

        if not data or not iv:
            raise ValueError(f"[EncryptionManager] Missing data/IV for key '{key_prefix}'")

        with decoder(self.master_key, None, self.iv_master_key) as de:
            de.AESEncryptKey = self.key
            return de.AESDecryptData(data, iv)