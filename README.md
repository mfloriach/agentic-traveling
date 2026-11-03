- Hooks
- Guardrails





def search(self, query: str, limit: int = 5):
    dense_vector = self.embeddings.embed_query(query)

    results = self.client.query_points(
        collection_name=self.collection_name,
        prefetch=[
            models.Prefetch(
                query=dense_vector,
                using="dense",
                limit=50,
            ),
            models.Prefetch(
                query=models.Document(
                    text=query,
                    model="Qdrant/bm25",
                ),
                using="bm25",
                limit=50,
            ),
        ],
        query=models.FusionQuery(
            fusion=models.Fusion.RRF,
        ),
        limit=limit,
        with_payload=True,
    )

    return results.points


{
  "status": "answered",
  "answer": "The approved carry-forward limit is ten days.",
  "citations": [
    "HR-POLICY-2026-SECTION-8"
  ],
  "confidence": 0.91
}

{
  "status": "abstained",
  "reason": "The available documents do not establish the requested fact.",
  "citations": []
}