from ferite_steel.ai import together_client

EMBEDDING_MODEL = 'BAAI/bge-large-en-v1.5'

def embed_texts(texts):
    response = together_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]

def embed_query(text):
    return embed_texts([text])[0]