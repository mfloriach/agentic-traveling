from ..database import database
import os
from langchain_openai import OpenAI


openai_api_key = os.getenv("OPENAI_API_KEY")
llm = OpenAI(openai_api_key=openai_api_key)


async def get_rag_response(query: str):
    retrieved_docs = database.retrieve(query=query)

    # Prepare the input for the LLM: Combine the query and the retrieved documents into a single string
    context = "\n".join([doc.page_content for doc in retrieved_docs])

    # LLM expects a list of strings (prompts), so we create one by combining the query with the retrieved context
    prompt = [f"Use the following information to answer the question:\n\n{context}\n\nQuestion: {query}"]

   # Generate the final response using the language model (LLM)
    generated_response = llm.generate(prompt)
    
    return generated_response