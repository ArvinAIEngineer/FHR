import requests
from joblib import Parallel, delayed


class Embedder:
    """
    Handles embedding generation by interacting with a remote model API.

    Attributes:
        model_url (str): URL of the remote model API.
        model_name (str): Name of the model used for embedding.
    """

    def __init__(self, model_name: str, model_url: str):
        """
        Initializes the Embedder with model URL and name.

        Args:
            model_url (str): URL of the remote model API.
            model_name (str): Name of the model used for embedding.
        """
        self.model_name = model_name
        self.model_url = model_url
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}

    def organize_payloads(self, text: list) -> list:
        """
        Organizes the input text into payloads for API requests.

        Args:
            text (list): List of text strings to be embedded.

        Returns:
            list: List of payload dictionaries for API requests.
        """
        payloads = []
        for i in range(len(text)):
            payload = {
                "model": self.model_name,
                "prompt": f"clustering: {text[i]}",
            }
            payloads.append(payload)
        return payloads

    def _send_request(self, payload: dict) -> dict:
        """
        Sends a POST request to the model API with the given payload.

        Args:
            payload (dict): Payload to be sent to the API.

        Returns:
            dict: JSON response from the API.

        Raises:
            Exception: If the API response status code is not 200.
        """
        response = requests.post(self.model_url, headers=self.headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code} - {response.text}")
        return response.json()

    def get_embeddings(self, text: list) -> list:
        """
        Generates embeddings for a list of text inputs.

        Args:
            text (list): List of text strings to be embedded.

        Returns:
            list: List of responses containing embeddings.
        """
        payloads = self.organize_payloads(text)
        with Parallel(n_jobs=len(payloads), prefer="threads", verbose=0) as parallel:
            responses = parallel(delayed(self._send_request)(payload) for payload in payloads)
        embeddings = [response["embedding"] for response in responses]
        return embeddings
