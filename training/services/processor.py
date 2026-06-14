from django.utils import timezone
from training.models import DocumentChunk
from training.services.extractor import extract_text, chunk_text
from training.services.embedder import embed_texts
#from training.services.onedrive import upload_file

def process_document(document, file_obj=None, filename=None):
    if document.source_type == 'file':
        file_bytes = file_obj.read()
        text = extract_text_from_bytes(file_bytes, filename)
#        web_url = upload_file(file_bytes, filename)
#        document.file_url = web_url
    else:
        text = document.direct_text

    chunks = chunk_text(text)
    document.direct_text = text
    embeddings = embed_texts(chunks)

    DocumentChunk.objects.filter(document=document).delete()
    DocumentChunk.objects.bulk_create([
        DocumentChunk(document=document, chunk_text=chunk, embedding=emb, chunk_index=i)
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
    ])

    document.is_processed = True
    document.processed_at = timezone.now()
    document.save()

def extract_text_from_bytes(file_bytes, filename):
    import io
    from training.services.extractor import extract_text
    return extract_text(io.BytesIO(file_bytes), filename)