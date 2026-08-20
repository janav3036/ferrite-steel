from ferite_steel.ai import create_embeddings

EMBEDDING_MODEL = 'intfloat/multilingual-e5-large-instruct'

def embed_texts(texts):
    response = create_embeddings(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]

def embed_query(text):
    return embed_texts([text])[0]