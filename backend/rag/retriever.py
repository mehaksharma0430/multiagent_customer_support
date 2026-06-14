from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

db = Chroma(
    persist_directory="backend/chroma_db",
    embedding_function=embeddings
)

def retrieve_context(query):

    docs = db.similarity_search(
        query,
        k=3
    )

    context = "\n".join(
        [doc.page_content for doc in docs]
    )

    return context