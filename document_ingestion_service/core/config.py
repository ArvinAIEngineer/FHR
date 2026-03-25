# Configuration management for document_ingestion_service
import os
import yaml
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.yaml")
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Create settings dictionary
        settings = {
            # Azure OpenAI settings
            "azure_openai_endpoint": config_data['environment']['azure_endpoint'],
            "azure_openai_api_key": config_data['environment']['api_key'],
            "azure_openai_chat_deployment": config_data['environment']['azure_deployment_llm'],
            "azure_openai_embedding_deployment": config_data['environment']['azure_deployment_embedding'],
            "azure_openai_api_version": config_data['environment']['openai_api_version'],
            
            # LLM settings
            "llm_model": config_data['environment']['llm_model'],
            "llm_temperature": config_data['environment']['llm_temperature'],
            "llm_max_tokens": config_data['environment']['llm_max_tokens'],
            
            #Ollama settings
            "ollama_base_url": config_data['environment']['ollama_base_url'],
            "ollama_embedding_model": config_data['environment']['ollama_embedding_model'],
            "ollama_llm_model": config_data['environment']['ollama_llm_model'],
            "use_ollama":config_data['environment']['use_ollama'],

            # Vector store settings
            "vectorstore_persist_directory": config_data['vectorstore']['persist_directory'],
            "vectorstore_collection_name": config_data['vectorstore']['collection_name'],
            
            # Text processing settings
            "chunk_size": config_data['text']['chunk_size'],
            "chunk_overlap": config_data['text']['chunk_overlap'],
            
            # Service settings
            "service_host": config_data['service']['host'],
            "service_port": config_data['service']['port'],

            #modules
            #image extraction module
            "image_features_path": config_data['image_summarization']['image_features_path'],
            "image_feature_prompt_path": config_data['image_summarization']['image_feature_prompt_path'],
            "summary_prompt_path": config_data['image_summarization']['summary_prompt_path'],
            "page_image_prompt_en_path": config_data['image_summarization']['page_image_prompt_en_path'],
            "page_image_prompt_ar_path": config_data['image_summarization']['page_image_prompt_ar_path'],

            #table summarization
            "detailed_summary_prompt_path": config_data['table_summarization']['detailed_summary_prompt_path'],
            "num_ctx": config_data['table_summarization']['num_ctx'],
            "num_predict": config_data['table_summarization']['num_predict'],
            "temprature": config_data['table_summarization']['temprature'],

            #topic subtopic
            "topic_subtopic_modelling_english":config_data['topic_subtopic_modelling_english'],
            "topic_description_path_en": config_data['topic_subtopic_modelling_english']['topic_description_path'],
            "subtopic_description_path_en": config_data['topic_subtopic_modelling_english']['subtopic_description_path'],
            "topic_subtopic_mapping_path_en": config_data['topic_subtopic_modelling_english']['topic_subtopic_mapping_path'],

        }
        
        return settings
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        raise

# Create global settings instance
settings = load_config()
