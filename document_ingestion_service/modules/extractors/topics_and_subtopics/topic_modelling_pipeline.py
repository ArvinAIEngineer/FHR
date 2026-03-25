"""
Topic Modeling Pipeline for classifying text into predefined topics and subtopics.

This module provides a semantic similarity-based approach to classify text segments into
predefined topics and subtopics. It uses embeddings to compare text against topic descriptions
and determines the best matching topic and subtopic based on cosine similarity.

Classes:
    TopicModelling: Main class for topic and subtopic classification using embeddings.
"""
import os
import json
import tomllib
import numpy as np
from tqdm import tqdm
from joblib import Parallel, delayed
import requests # Import requests for direct API calls
from utils.logger import get_logger # Import get_logger utility
from core.config import settings

# Get logger instance
logger = get_logger(__name__)


# Get the current directory to locate configuration files
CURR_DIR = os.path.dirname(os.path.abspath(__file__))


# CONFIG_ARA = tomllib.loads(open(os.path.join(CURR_DIR, "config_ara.toml"), "r").read())

# Determine the number of CPU cores available for parallel processing
WORKERS = os.cpu_count()


class TopicModelling:
    """
    A class for classifying text into predefined topics and subtopics using semantic similarity.

    This class loads predefined topic and subtopic descriptions, generates embeddings for them,
    and provides methods to classify text by comparing its embedding with the topic/subtopic embeddings.

    Attributes:
        model_name (str): Name of the embedding model
        model_url (str): URL or path to the embedding model
        embedder (Embedder): Instance of the Embedder class for generating embeddings
        config (dict): Configuration containing paths to topic and subtopic mappings
        topic_descriptions (dict): Dictionary mapping topic IDs to their descriptions
        subtopics (dict): Dictionary mapping subtopic IDs to their descriptions
        topic_subtopic_mapping (dict): Dictionary mapping topics to their associated subtopics
        topic2embed_map (dict): Dictionary mapping topic IDs to their embeddings
        embed2topic_map (dict): Dictionary mapping topic embeddings to their IDs
        subtopic2embed_map (dict): Dictionary mapping subtopic IDs to their embeddings
        embed2subtopic_map (dict): Dictionary mapping subtopic embeddings to their IDs
    """
    def __init__(self, model_name: str, model_url: str, lang: str = "eng"):
        """
        Initialize the TopicModelling class with a specified embedding model and language.

        Args:
            model_name (str): Name of the embedding model
            model_url (str): URL or path to the embedding model
            lang (str, optional): Language code for topic modeling. Defaults to "eng" (English).
                Currently supported: "eng" (English)
        """
        
    
        self.model_name = model_name
        self.model_url = model_url
        self.headers = {"Content-Type": "application/json"} # Headers for API requests

        # Select the appropriate configuration based on language
        self.config = settings["topic_subtopic_modelling_english"] if lang == "eng" else settings["topic_subtopic_modelling_ar"]

        # Load topic and subtopic descriptions and mappings
        self.topic_descriptions: dict = self.get_mapping(self.config["topic_description_path"])
        self.subtopics: dict = self.get_mapping(self.config["subtopic_description_path"])
        self.topic_subtopic_mapping: dict = self.get_mapping(self.config["topic_subtopic_mapping_path"])

        # Define the prompt template for the LLM
        # Load the prompt template from a file
        self.prompt_template = self.get_prompt("prompts/topic_classification_prompt.txt")

    def get_prompt(self, path: str) -> str:
        """
        Reads and returns the content of a prompt file.

        Args:
            path (str): Relative path to the prompt file.

        Returns:
            str: Content of the prompt file.
        """
        path = os.path.join(CURR_DIR, path)
        with open(path, "r") as f:
            prompt = f.read()
        return prompt

    def get_mapping(self, path: str) -> dict:
        """
        Load a JSON mapping file from the specified path.

        Args:
            path (str): Relative path to the JSON mapping file

        Returns:
            dict: The loaded mapping as a dictionary
        """
        with open(os.path.join(CURR_DIR, path), "r") as f:
            mapp = json.load(f)
        return mapp

    def query_llm(self, payload: dict) -> dict:
        """
        Sends a POST request to the LLM language model API and retrieves the response.

        Args:
            payload (dict): Payload to send to the API.

        Returns:
            dict: Response from the API.
        """
        try:
            url = f"{self.model_url}"
            response = requests.post(url=url, headers=self.headers, json=payload)
            response.raise_for_status() # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error querying LLM API: {e}")
            return {} 
        


    def _validate_topic_subtopic(self, topic, subtopic):
        if topic not in self.topic_descriptions:
            raise ValueError(f"Invalid topic: {topic}")
        if subtopic not in self.subtopics:
            raise ValueError(f"Invalid subtopic: {subtopic}")
        if subtopic not in self.topic_subtopic_mapping.get(topic, []):
            raise ValueError(f"Subtopic '{subtopic}' does not belong to topic '{topic}'")
    


    def classify_with_llm(self, text_content: str) -> dict:
        """
        Classify text content into a topic and subtopic using the LLM. 

        Args:
            text_content (str): The text content to classify.

        Returns:
            dict: A dictionary containing the classified "topic" and "subtopic".
                  Returns an empty dictionary or raises an error if classification fails.
        """
        logger.info(f"Attempting to classify text content: {text_content[:100]}...") 

        try:
            formatted_prompt = self.prompt_template.format(
                topic_descriptions=json.dumps(self.topic_descriptions, indent=2),
                subtopic_descriptions=json.dumps(self.subtopics, indent=2),
                topic_subtopic_mapping=json.dumps(self.topic_subtopic_mapping, indent=2),
                text_content=text_content
            )

            payload = {
                "model": self.model_name,
                "prompt": formatted_prompt,
                "stream": False # We want the full response at once
            }
            # logger.info(f"LLM API payload: {payload}") # Log the payload

            # Invoke the LLM via the API
            response = self.query_llm(payload)
            # logger.info(f"Raw LLM response: {response}") # Log the raw response

            # Check if the response contains the expected 'response' key
            if "response" in response:
                try:
                    classification_result = json.loads(response["response"])
                    logger.info(f"Parsed LLM classification result: {classification_result}") # Log the parsed result

                    # Validate the result
                    if "topic" in classification_result and "subtopic" in classification_result:
                        self._validate_topic_subtopic(classification_result["topic"], classification_result["subtopic"])
                        return classification_result
                    else:
                        logger.warning(f"LLM response missing 'topic' or 'subtopic' keys after JSON parsing: {classification_result}")
                        return {} 
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON from LLM response: {response.get('response', 'No response key')}")
                    return {} 
            else:
                logger.warning(f"LLM response missing 'response' key: {response}")
                return {} 

        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying LLM API: {e}")
            return {}
        except Exception as e:
            logger.error(f"An unexpected error occurred during LLM classification: {e}", exc_info=True) # Log unexpected errors with traceback
            return {} 

    # Commented out old methods
    # def get_embeddings(self, text: list) -> list:
    #     """
    #     Generate embeddings for a list of text segments.

    #     Args:
    #         text (list): List of text segments to embed

    #     Returns:
    #         list: List of embeddings corresponding to the input text segments
    #     """
    #     return self.embedder.get_embeddings(text)

    # def cosine_similarity(self, embed1: list, embed2: list) -> float:
    #     """
    #     Calculate the cosine similarity between two embeddings.

    #     Args:
    #         embed1 (list): First embedding vector
    #         embed2 (list): Second embedding vector

    #     Returns:
    #         float: Cosine similarity score between the two embeddings (range: -1 to 1)
    #     """
    #     return cosine_similarity([embed1], [embed2])[0][0]

    # def get_single_topic(self, embed: list) -> str:
    #     """
    #     Determine the most similar topic for a given embedding.

    #     Args:
    #         embed (list): Embedding vector of the text to classify

    #     Returns:
    #         str: ID of the most similar topic
    #     """
    #     # Calculate cosine similarity between the input embedding and all topic embeddings
    #     cosine_similarities = [self.cosine_similarity(embed, embed1)
    #                           for embed1 in self.topic2embed_map.values()]

    #     # Find the index of the maximum similarity
    #     max_cos_sim_index = np.argmax(cosine_similarities)

    #     # Get the corresponding topic embedding and ID
    #     topic_embed = list(self.topic2embed_map.values())[max_cos_sim_index]
    #     topic = self.embed2topic_map[tuple(topic_embed)]

    #     return topic

    # def get_single_subtopic(self, embed: list, topic: str) -> str:
    #     """
    #     Determine the most similar subtopic for a given embedding within a specific topic.

    #     Args:
    #         embed (list): Embedding vector of the text to classify
    #         topic (str): ID of the topic to search subtopics within

    #     Returns:
    #         str: ID of the most similar subtopic
    #     """
    #     # Get the list of subtopics associated with the given topic
    #     subtopics = self.topic_subtopic_mapping[topic]

    #     # Get embeddings for these subtopics
    #     sub_topic_embeds = [self.subtopic2embed_map[subtopic] for subtopic in subtopics]

    #     # Calculate cosine similarity between the input embedding and all subtopic embeddings
    #     cosine_similarities = [self.cosine_similarity(embed, embed1)
    #                           for embed1 in sub_topic_embeds]

    #     # Find the index of the maximum similarity
    #     max_cos_sim_index = np.argmax(cosine_similarities)

    #     # Get the corresponding subtopic embedding and ID
    #     subtopic_embed = list(sub_topic_embeds)[max_cos_sim_index]
    #     subtopic = self.embed2subtopic_map[tuple(subtopic_embed)]

    #     return subtopic

    def get_single_topic_and_subtopic(self, text: str) -> dict:
        """
        Classify a single text segment into a topic and subtopic using an LLM.

        Args:
            text (str): Text segment to classify

        Returns:
            dict: Dictionary containing the assigned topic and subtopic IDs
        """
        # Commented out old embedding and cosine similarity logic
        # # Generate embedding for the input text
        # embed = self.get_embeddings([text])[0]

        # # Find the most similar topic
        # topic = self.get_single_topic(embed)

        # # Find the most similar subtopic within that topic
        # subtopic = self.get_single_subtopic(embed, topic)

        # Use the LLM for classification
        classification_result = self.classify_with_llm(text)

        # Return the classification result (will be empty dict on failure)
        return classification_result


    def get_many_topics_and_subtopics(self, texts: list) -> list[dict]:
        """
        Classify multiple text segments into topics and subtopics in parallel using an LLM.

        Args:
            texts (list): List of text segments to classify

        Returns:
            list[dict]: List of dictionaries, each containing the assigned topic and subtopic IDs
                       for a corresponding text segment
        """
        # Create a queue of delayed tasks for parallel processing using the LLM classification method
        taskq = tqdm([delayed(self.get_single_topic_and_subtopic)(text) for text in texts],
                     total=len(texts), desc="Getting topics and subtopics with LLM")

        # Execute the tasks in parallel with progress tracking
        with Parallel(n_jobs=min(WORKERS, len(texts)), verbose=0, prefer="threads") as parallel:
            topics_and_subtopics = parallel(taskq)

        return topics_and_subtopics
