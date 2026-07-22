from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    app_title: str = "ScreenSorts API"
    app_version: str = "0.1.0"
    app_description: str = "AI-Powered Semantic Screenshot Search Engine"

    cors_origins: str = "http://localhost:3000"

    repo_demo_dir: str = "data/demo"
    repo_user_dir: str = "data/user"
    repo_metadata_dir: str = "data/metadata"
    repo_datasets_dir: str = "data/datasets"

    demo_sample_size: int = 100
    demo_random_seed: int = 42

    ocr_results_dir: str = "data/ocr_results"
    ocr_batch_size: int = 10

    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    embedding_dimension: int = 384
    embedding_batch_size: int = 32
    embeddings_dir: str = "data/embeddings"

    chroma_persist_dir: str = "vector_store"
    chroma_collection_name: str = "screensorts"
    chroma_batch_size: int = 50

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def repo_demo_path(self) -> Path:
        return self._resolve(self.repo_demo_dir)

    @property
    def repo_user_path(self) -> Path:
        return self._resolve(self.repo_user_dir)

    @property
    def repo_metadata_path(self) -> Path:
        return self._resolve(self.repo_metadata_dir)

    @property
    def repo_datasets_path(self) -> Path:
        return self._resolve(self.repo_datasets_dir)

    @property
    def ocr_results_path(self) -> Path:
        return self._resolve(self.ocr_results_dir)

    @property
    def embeddings_path(self) -> Path:
        return self._resolve(self.embeddings_dir)

    @property
    def chroma_persist_path(self) -> Path:
        return self._resolve(self.chroma_persist_dir)

    def _resolve(self, path_str: str) -> Path:
        p = Path(path_str)
        if p.is_absolute():
            return p
        return _PROJECT_ROOT / p


settings = Settings()
