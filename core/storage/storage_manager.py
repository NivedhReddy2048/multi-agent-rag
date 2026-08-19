"""Cloud File Storage Abstraction Layer supporting Local, AWS S3, Azure Blob, and GCP Storage."""

import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from core.logger import get_logger

logger = get_logger("core.storage.manager")


class StorageProvider(ABC):
    """Abstract Base Class for Multi-Cloud File Storage."""

    @abstractmethod
    def upload_file(self, file_name: str, content: bytes) -> str:
        """Upload file content and return storage path / URI."""
        pass

    @abstractmethod
    def download_file(self, file_name: str) -> bytes:
        """Download file content by name."""
        pass

    @abstractmethod
    def delete_file(self, file_name: str) -> bool:
        """Delete file by name."""
        pass

    @abstractmethod
    def list_files(self) -> List[str]:
        """List all stored file names."""
        pass


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage adapter for development."""

    def __init__(self, base_dir: str = "data/cloud_storage"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def upload_file(self, file_name: str, content: bytes) -> str:
        file_path = os.path.join(self.base_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"[LocalStorage] Saved file '{file_name}' ({len(content)} bytes)")
        return file_path

    def download_file(self, file_name: str) -> bytes:
        file_path = os.path.join(self.base_dir, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File '{file_name}' not found.")
        with open(file_path, "rb") as f:
            return f.read()

    def delete_file(self, file_name: str) -> bool:
        file_path = os.path.join(self.base_dir, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def list_files(self) -> List[str]:
        return os.listdir(self.base_dir)


class S3StorageProvider(StorageProvider):
    """Mock AWS S3 Cloud Storage Adapter."""

    def __init__(self, bucket_name: str = "ekip-s3-bucket"):
        self.bucket_name = bucket_name
        self._storage: Dict[str, bytes] = {}

    def upload_file(self, file_name: str, content: bytes) -> str:
        self._storage[file_name] = content
        logger.info(f"[S3Storage] Uploaded '{file_name}' to bucket '{self.bucket_name}'")
        return f"s3://{self.bucket_name}/{file_name}"

    def download_file(self, file_name: str) -> bytes:
        if file_name not in self._storage:
            raise FileNotFoundError(f"File '{file_name}' not in S3 bucket.")
        return self._storage[file_name]

    def delete_file(self, file_name: str) -> bool:
        if file_name in self._storage:
            del self._storage[file_name]
            return True
        return False

    def list_files(self) -> List[str]:
        return list(self._storage.keys())


class AzureBlobStorageProvider(StorageProvider):
    """Mock Azure Blob Storage Adapter."""

    def __init__(self, container_name: str = "ekip-azure-container"):
        self.container_name = container_name
        self._storage: Dict[str, bytes] = {}

    def upload_file(self, file_name: str, content: bytes) -> str:
        self._storage[file_name] = content
        return f"https://ekip.blob.core.windows.net/{self.container_name}/{file_name}"

    def download_file(self, file_name: str) -> bytes:
        return self._storage.get(file_name, b"")

    def delete_file(self, file_name: str) -> bool:
        return self._storage.pop(file_name, None) is not None

    def list_files(self) -> List[str]:
        return list(self._storage.keys())


class GCSStorageProvider(StorageProvider):
    """Mock Google Cloud Storage Adapter."""

    def __init__(self, bucket_name: str = "ekip-gcs-bucket"):
        self.bucket_name = bucket_name
        self._storage: Dict[str, bytes] = {}

    def upload_file(self, file_name: str, content: bytes) -> str:
        self._storage[file_name] = content
        return f"gs://{self.bucket_name}/{file_name}"

    def download_file(self, file_name: str) -> bytes:
        return self._storage.get(file_name, b"")

    def delete_file(self, file_name: str) -> bool:
        return self._storage.pop(file_name, None) is not None

    def list_files(self) -> List[str]:
        return list(self._storage.keys())


class StorageManager:
    """Delegator manager choosing active cloud storage backend (local, s3, azure, gcs)."""

    def __init__(self, provider_type: str = "local"):
        if provider_type == "s3":
            self.provider = S3StorageProvider()
        elif provider_type == "azure":
            self.provider = AzureBlobStorageProvider()
        elif provider_type == "gcs":
            self.provider = GCSStorageProvider()
        else:
            self.provider = LocalStorageProvider()

    def upload_file(self, file_name: str, content: bytes) -> str:
        return self.provider.upload_file(file_name, content)

    def download_file(self, file_name: str) -> bytes:
        return self.provider.download_file(file_name)

    def delete_file(self, file_name: str) -> bool:
        return self.provider.delete_file(file_name)

    def list_files(self) -> List[str]:
        return self.provider.list_files()


# Global singleton instance
storage_manager = StorageManager()
