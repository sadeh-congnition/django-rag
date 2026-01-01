import djclick as click
from django.db import transaction
from loguru import logger
from chunking.models import Chunk, ChunkDescription
from synthetic_data_generator.chunk_describe import generate_chunk_descriptions


@click.command()
@click.option(
    "--model",
    # default="groq/openai/gpt-oss-120b",
    default="lm_studio/nousresearch/hermes-4-70b",
    type=str,
    help="LLM model to use for generating descriptions (default: gpt-3.5-turbo)",
)
@click.option(
    "--clear-existing",
    is_flag=True,
    help="Clear existing descriptions before processing",
)
def describe_chunk(model, clear_existing=False):
    """Generate descriptions for all code chunks using LLM"""

    if clear_existing:
        count = ChunkDescription.objects.count()
        ChunkDescription.objects.all().delete()
        logger.info(f"Cleared {count} existing descriptions")

    chunks = Chunk.objects.all()
    total_chunks = chunks.count()

    if total_chunks == 0:
        logger.warning("No chunks found. Please run chunk_code command first.")
        return

    logger.info(f"Processing {total_chunks} chunks using model: {model}")

    processed_count = 0
    success_count = 0

    with click.progressbar(length=total_chunks, label="Generating descriptions") as bar:
        for chunk in chunks:
            try:
                # Check if descriptions already exist for this chunk
                if not clear_existing and chunk.descriptions.exists():
                    logger.debug(
                        f"Skipping chunk {chunk.id} - descriptions already exist"
                    )
                    bar.update(1)
                    processed_count += 1
                    continue

                # Generate descriptions using LLM
                code_description = generate_chunk_descriptions(
                    chunk.content, model
                )
                descriptions = code_description.descriptions

                # Save descriptions to database
                with transaction.atomic():
                    for description in descriptions:
                        ChunkDescription.objects.create(
                            chunk=chunk, description=description
                        )

                success_count += 1
                logger.debug(
                    f"Generated {len(descriptions)} descriptions for chunk {chunk.id}"
                )

            except Exception as e:
                logger.error(f"Error processing chunk {chunk.id}: {e}")
                raise
            finally:
                bar.update(1)
                processed_count += 1

    logger.info(
        f"Completed! Generated descriptions for {success_count}/{total_chunks} chunks."
    )

