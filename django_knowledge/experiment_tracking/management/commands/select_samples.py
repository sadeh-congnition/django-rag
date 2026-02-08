import djclick as click
from chunking.chunker import get_chunk_descriptions
from experiment_tracking.models import Sample
import random


@click.option("--num", type=int, required=True, help="Number of samples to select")
@click.command()
def select_samples(num):
    res = list()
    chunk_descriptions = get_chunk_descriptions()
    chunk_desc_indices = random.sample(range(len(chunk_descriptions)), k=num)
    for index in chunk_desc_indices:
        chunk_desc = chunk_descriptions[index]
        res.append(chunk_desc)

    chunk_description_ids = [chunk_desc.id for chunk_desc in res]
    sample = Sample.objects.create(chunk_description_ids=chunk_description_ids)

    click.echo(f"Created Sample with ID: {sample.id}")
