from ferite_steel.ai import together_client

EMBEDDING_MODEL = 'intfloat/multilingual-e5-large-instruct'

def embed_texts(texts):
    response = together_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]

def embed_query(text):
    return embed_texts([text])[0]