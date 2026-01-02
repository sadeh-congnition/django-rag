import djclick as click

from experiment_tracking.models import EmbeddingModel, EmbedderEval
from experiment_tracking.run import run_experiment


@click.command()
def eval_embedding_models():
    EmbeddingModel.create_defaults()

    for embedding_model_name, num_tests, score, eval_time in run_experiment(
        EmbeddingModel.embed_funcs()
    ):
        embedding_model = EmbeddingModel.objects.get(name=embedding_model_name)
        avrg_eval_time = eval_time / num_tests
        name = "Embedder Accuracy@1"
        EmbedderEval.objects.create(
            embedding_model=embedding_model,
            num_tests=num_tests,
            eval_score=score,
            name=name,
            average_eval_time=avrg_eval_time,
            total_eval_time=eval_time,
        )
