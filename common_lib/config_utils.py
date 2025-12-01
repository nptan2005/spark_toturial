import yaml
import os
from functools import lru_cache

class ConfigUtils:

    @staticmethod
    def check_import():
        """Placeholder — sau này có logic validate gì thì thêm vào."""
        return True

    @staticmethod
    @lru_cache(maxsize=32)
    def load_config(file_path: str, model_class):
        """
        Load YAML → parse bằng pydantic model_class.

        Args:
            file_path: đường dẫn YAML
            model_class: class pydantic (_ImportConfig hoặc _ExportConfig)

        Returns:
            Instance của model_class
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Config file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        try:
            return model_class(**data)
        except Exception as e:
            raise ValueError(f"Config parse failed for {file_path}: {e}")
        
    @staticmethod
    def read_file(file_path: str, mode: str = "r"):
        """
        Đọc file an toàn, trả về nội dung dạng str hoặc bytes.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, mode) as f:
            return f.read()