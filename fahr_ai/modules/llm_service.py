import yaml
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from utils.logger import get_logger
import os

class LLMClient:
    _instance = None  # singleton instance

    def __new__(cls, config_path: str = "configs/llm_config.yaml"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(config_path)
        return cls._instance

    def _initialize(self, config_path: str):
        """Load configuration and initialize LLM."""
        self.base_logger = get_logger("LLMClient")
        self.configs = self._load_llm_config(config_path)

        # Decide which model class to use (Azure or OpenAI)
        if self.configs.get("use_azure", False):
            self.model = AzureChatOpenAI(
                deployment_name=self.configs["AZURE_OPENAI_DEPLOYMENT_NAME"],
                model=self.configs["AZURE_OPENAI_DEPLOYMENT_NAME"],
                api_key=self.configs["AZURE_OPENAI_API_KEY"],
                azure_endpoint=self.configs["AZURE_OPENAI_ENDPOINT"],
                api_version=self.configs.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
                temperature=self.configs.get("temperature", 0),
                request_timeout=self.configs.get("request_timeout", 30),
            )
            self.base_logger.info(f"LLM initialized: {self.configs['AZURE_OPENAI_DEPLOYMENT_NAME']}")

        else:
            self.model = ChatOpenAI(
                model_name=self.configs["OLLAMA_MODEL_NAME"],
                openai_api_base=self.configs.get("OPENAI_API_BASE_URL", None),
                openai_api_key=self.configs.get("OPENAI_API_KEY", None),
                temperature=self.configs.get("temperature", 0),
            )
            self.base_logger.info(f"LLM initialized: {self.configs['OLLAMA_MODEL_NAME']}")

    def _load_llm_config(self, config_path: str) -> dict:
        """Load LLM configuration from YAML file."""
        try:
            with open(config_path, "r") as config_file:
                configs = yaml.safe_load(config_file)
            return configs
        except (FileNotFoundError, KeyError, yaml.YAMLError) as e:
            self.base_logger.error(f"Error loading LLM config: {e}")
            raise

    def get_model(self):
        """Return the initialized LLM model."""
        return self.model