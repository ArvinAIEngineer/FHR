import os
import requests
import tomllib

from joblib import Parallel, delayed
from core.config import settings
from utils.logger import get_logger # Import get_logger utility


CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
WORKERS = os.cpu_count()


class SummarizeTable:
    """
    A class to summarize tables using a language model.

    Attributes:
        model_name (str): The name of the language model.
        model_url (str): The URL endpoint for the language model.
        config (dict): Configuration for table summarization.
        headers (dict): HTTP headers for API requests.
        detailed_summary_prompt (str): The prompt template for generating detailed summaries.
    """

    def __init__(self, model_name: str, model_url: str):
        """
        Initializes the SummarizeTable class with model details and configuration.

        Args:
            model_name (str): The name of the language model.
            model_url (str): The URL endpoint for the language model.
            config (dict): Configuration dictionary loaded from a TOML file.
        """
        
        self.model_url = model_url
        self.model_name = model_name
        # self.config = settings["table_summarization"]
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}
        # Load the detailed summary prompt from the specified file path
        self.detailed_summary_prompt = self.get_prompt(settings["detailed_summary_prompt_path"])
        self.logger = get_logger(__name__)

    def get_prompt(self, path: str) -> str:
        """
        Reads the prompt from the specified file path.

        Args:
            path (str): The file path to the prompt.

        Returns:
            str: The content of the prompt file.
        """
        path = os.path.join(CURRENT_DIRECTORY, path)
        with open(path, "r") as f:
            prompt = f.read()
        return prompt

    def query_llm(self, payload: dict, url: str) -> dict:
        """
        Sends a POST request to the language model API with the given payload.

        Args:
            payload (dict): The payload containing the prompt and model details.
            url (str): The URL endpoint for the language model.

        Returns:
            dict: The response from the language model API.
        """
        response = requests.post(url=url, headers=self.headers, json=payload)
        return response.json()["response"]

    def get_payloads(self, prompts: list) -> list:
        """
        Generates payloads for the language model API from a list of prompts.

        Args:
            prompts (list): A list of prompt strings.

        Returns:
            list: A list of payload dictionaries.
        """
        # Create a payload for each prompt
        return [
            {
                "prompt": prompt,
                "model": self.model_name,
                "stream": False,
                "temperature": 0,
            }
            for prompt in prompts
        ]

    def get_detailed_summaries(self, table_strings: list[str]) -> list[str]:
        """
        Generates detailed summaries for a list of table strings.

        Args:
            table_strings (list[str]): A list of table strings in CSV format.

        Returns:
            list[str]: A list of detailed summaries for the tables.
        """
        if not table_strings:  # Handle empty list case
            return []
            
        # Replace placeholder in the prompt with actual table data
        prompts = [self.detailed_summary_prompt.replace("<TABLE>", table) for table in table_strings]
        payloads = self.get_payloads(prompts)

        # Use joblib's Parallel to process API requests concurrently
        task_q = [delayed(self.query_llm)(payload, self.model_url) for payload in payloads]

        # Ensure n_jobs is at least 1
        n_jobs = max(1, min(len(payloads), WORKERS))
        with Parallel(n_jobs=n_jobs, prefer="threads", verbose=0) as parallel:
            responses = parallel(task_q)

        return responses

    def organized_response(self, tables: list[dict], detailed_summaries: list[str]) -> list[dict]:
        """
        Combines the original table data with their corresponding detailed summaries.

        Args:
            tables (list[dict]): A list of table dictionaries.
            detailed_summaries (list[str]): A list of detailed summaries.

        Returns:
            list[dict]: A list of dictionaries containing table data and summaries.
        """
        # Combine each table with its corresponding summary
        return [{**tables[i], "detailed_summary": detailed_summaries[i]} for i in range(len(tables))]

    def get_summary(self, tables: list[dict]) -> list[dict]:
        """
        Get a summary of the tables using the LLM.
        """
        summaries = []
        for table in tables:
            try:
                # Use language-specific prompt based on detected language
                if table.get('language', 'en') == 'ar':
                    prompt = (
                        "قم بتحليل الجدول التالي وقدم ملخصًا مفصلًا باللغة العربية. "
                        "قم بتضمين أي أنماط أو ملاحظات مهمة.\n\n"
                        f"الجدول:\n{table['table_csv']}"
                    )
                else:
                    prompt = (
                        "Analyze the following table and provide a detailed summary. "
                        "Include any notable patterns or observations.\n\n"
                        f"Table:\n{table['table_csv']}"
                    )
                response = self.query_llm({"prompt": prompt, "model": self.model_name, "stream": False, "temperature": 0}, self.model_url)
                summary = response.strip() if hasattr(response, "content") else response
                summaries.append({
                    "table": table,
                    "summary": summary
                })
            except Exception as e:
                self.logger.error(f"Error summarizing table: {str(e)}")
                summaries.append({
                    "table": table,
                    "summary": "Error summarizing table."
                })
        return summaries
