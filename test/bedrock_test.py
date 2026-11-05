
from langchain_huggingface import HuggingFaceEmbeddings

print("Loading BGE embedding model...")

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={
        "device": "cpu"
    },
    encode_kwargs={
        "normalize_embeddings": True
    }
)

print("Model loaded successfully!")

text = "Artificial intelligence is transforming technology."

vector = embeddings.embed_query(text)

print("\nEmbedding generated successfully!")
print("Embedding dimensions:", len(vector))
print("First five values:", vector[:5])
