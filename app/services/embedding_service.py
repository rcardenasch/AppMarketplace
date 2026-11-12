
from functools import lru_cache
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Servicio responsable de transformar descripciones
    en vectores semánticos de 384 dimensiones.
    """

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    @staticmethod
    @lru_cache(maxsize=1)
    def obtener_modelo():

        return SentenceTransformer(
            EmbeddingService.MODEL_NAME
        )

    @classmethod
    def generar_embedding(cls, texto: str) -> list:

        if not texto or not texto.strip():
            raise ValueError("El texto no puede estar vacío")

        modelo = cls.obtener_modelo()

        vector = modelo.encode(
            texto,
            normalize_embeddings=True
        )

        return vector.tolist()
