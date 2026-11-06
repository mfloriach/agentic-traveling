from qdrant_client.models import ScoredPoint
from sentence_transformers import CrossEncoder


class DocumentReranker:
    def __init__(self, model_name: str, top_k: int = 5):
        self.model = CrossEncoder(model_name)
        self.top_k = top_k

    def rerank(
        self,
        query: str,
        points: list[ScoredPoint],
    ) -> list[ScoredPoint]:

        pairs = [
            (query, point.payload["text"])
            for point in points
            if point.payload is not None and "text" in point.payload
        ]

        scores = self.model.predict(pairs)

        ranked = sorted(
            zip(points, scores, strict=False),
            key=lambda item: float(item[1]),
            reverse=True,
        )

        return [point for point, _ in ranked[: self.top_k]]
