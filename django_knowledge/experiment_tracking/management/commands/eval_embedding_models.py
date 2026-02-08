import djclick as click

from chunking.models import ChunkConfig
from experiment_tracking.models import (
    EmbeddingModel,
    EmbedderEval,
    MetricConfig,
    BadResult,
    EmbedderPerformance,
    Sample,
)
from experiment_tracking.run import run_experiment
from metric_functions.retrieval import RetrievalAt1


@click.command()
@click.option("--chunk-config-id", type=int, required=True, help="Chunk configuration ID")
@click.option("--embedding-model-id", type=int, required=True, help="Embedding model ID")
@click.option("--num-test-samples", type=int, required=True, help="Number of test samples to evaluate randomly")
@click.option("--sample-id", type=int, required=True, help="Sample ID")
def eval_embedding_models(chunk_config_id, embedding_model_id, num_test_samples, sample_id):
    # EmbeddingModel.create_defaults()
    num_tests = num_test_samples

    if EmbedderEval.objects.filter(
        chunk_config_id=chunk_config_id,
        embedding_model_id=embedding_model_id,
        sample_id=sample_id,
    ).exists():
        click.echo(
            "EmbedderEval already exists for this chunk_config_id, "
            "embedding_model_id, and sample_id. Skipping evaluation."
        )
        return

    chunk_config: ChunkConfig = ChunkConfig.objects.get(id=chunk_config_id)
    metric_name = RetrievalAt1().name()

    metric_obj = RetrievalAt1()
    assert metric_obj.prefix
    assert metric_obj.at

    embedding_model_name, score, search_time, embedding_time, bad_results = (
        run_experiment(
            embedding_model_id=embedding_model_id,
            metric_func=metric_obj,
            chunk_config_id=chunk_config_id,
            num_tests=num_tests,
            sample_id=sample_id,
        )
    )
    embedding_model: EmbeddingModel = EmbeddingModel.objects.get(
        name=embedding_model_name
    )
    sample: Sample = Sample.objects.get(id=sample_id)
    metric_config: MetricConfig = MetricConfig.objects.create(
        content={
            "metric": {
                "name": metric_name,
                "num_tests": num_tests,
            }
        },
    )
    description = "Evaluating embedder"
    embedder_performance = EmbedderPerformance.objects.create(
        metric_config=metric_config,
        embedding_model=embedding_model,
        search_time=search_time,
        embedding_time=embedding_time,
    )
    embedder_eval: EmbedderEval = EmbedderEval.objects.create(
        embedder_performance=embedder_performance,
        chunk_config=chunk_config,
        embedding_model=embedding_model,
        metric_config=metric_config,
        sample=sample,
        name=metric_name,
        description=description,
        score=score,
    )

    for bad_result in bad_results:
        BadResult.objects.create(embedder_eval=embedder_eval, content=bad_result)
