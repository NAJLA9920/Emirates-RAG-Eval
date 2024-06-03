import importlib
from typing import Optional, cast
import torch
import numpy.typing as npt
import torch.nn.functional as F
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings


class CustomEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    Custom embedding function for generating embeddings using a specified transformer model.

    This class uses a transformer model from the Hugging Face library to generate embeddings for a given set of documents.
    It supports caching the model locally and normalizes the generated embeddings to unit length.

    Attributes:
        _device (torch.device): The device (CPU or GPU) to run the model on.
        _torch (module): The PyTorch module.
        _tokenizer (transformers.AutoTokenizer): The tokenizer for the specified model.
        _model (transformers.AutoModel): The transformer model for generating embeddings.
    """
    def __init__(
            self,
            model_name: str = "Alibaba-NLP/gte-base-en-v1.5",
            cache_dir: Optional[str] = None,
    ):
        """
        Initializes the CustomEmbeddingFunction with the specified model and cache directory.

        Args:
            model_name (str): The name of the transformer model to use. Default is "Alibaba-NLP/gte-base-en-v1.5".
            cache_dir (Optional[str]): The directory to cache the model. Default is None.

        Raises:
            ValueError: If the transformers or torch package is not installed.
        """
        try:
            from transformers import AutoModel, AutoTokenizer
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._device = cast(torch.device, device)
            self._torch = importlib.import_module("torch")
            self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._model = AutoModel.from_pretrained(model_name, cache_dir=cache_dir,trust_remote_code=True).to(self._device)
        except ImportError:
            raise ValueError(
                "The transformers and/or pytorch python package is not installed. Please install it with "
                "`pip install transformers` or `pip install torch`"
            )

    @staticmethod
    def _normalize(vector: npt.NDArray):
        """
        Normalizes a vector to unit length using L2 norm.

        Args:
            vector (npt.NDArray): The vector to normalize.

        Returns:
            list: The normalized vector as a list.
        """
        embeddings= F.normalize(vector, p=2, dim=1)
        return embeddings.detach().cpu().numpy().tolist()

    def __call__(self, input: Documents) -> Embeddings:
        """
        Generates embeddings for the given input documents.

        Args:
            input (Documents): The input documents to generate embeddings for.

        Returns:
            Embeddings: The generated embeddings.
        """
        inputs = self._tokenizer(
            input, padding=True, truncation=True, return_tensors="pt"
        ).to(self._device)
        with self._torch.no_grad():
            outputs = self._model(**inputs)
        embeddings = outputs.last_hidden_state[:, 0]
        return self._normalize(embeddings)