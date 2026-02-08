from django.core.management.base import BaseCommand
from chunking.models import Chunk, ChunkConfig
from django.db import transaction


class Command(BaseCommand):
    help = 'Assign the first chunk config to all existing chunks that have no config'

    def handle(self, *args, **options):
        # Get the first chunk config
        first_config = ChunkConfig.objects.first()
        
        if not first_config:
            self.stdout.write(
                self.style.ERROR('No ChunkConfig found. Please create a chunk configuration first.')
            )
            return
        
        # Get chunks without config
        chunks_without_config = Chunk.objects.filter(config__isnull=True)
        count = chunks_without_config.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('All chunks already have a config assigned.')
            )
            return
        
        self.stdout.write(f'Found {count} chunks without config. Assigning config ID {first_config.id}...')
        
        # Update chunks in batches for better performance
        with transaction.atomic():
            updated_count = chunks_without_config.update(config=first_config)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully assigned config to {updated_count} chunks.')
        )
