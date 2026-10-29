from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter, Language

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

splitters = {
    "text/x-go": RecursiveCharacterTextSplitter.from_language(
        language=Language.GO,
        chunk_size=1000,
        chunk_overlap=100,
    ),
    "text/markdown": MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
        ]
    ),
    "text/plain": RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
}