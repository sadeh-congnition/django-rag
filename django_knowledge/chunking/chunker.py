from .models import Chunk, ChunkDescription


def get_chunks():
    return Chunk.objects.all()


def get_chunk_descriptions():
    return ChunkDescription.objects.all()
