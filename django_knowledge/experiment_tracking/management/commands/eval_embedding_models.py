import djclick as click

from experiment_tracking.models import EmbeddingModel, EmbedderEval
from experiment_tracking.run import run_experiment


@click.command()
def eval_embedding_models():
    EmbeddingModel.create_defaults()

    for (
        embedding_model_name,
        num_tests,
        scores,
        search_times,
        embedding_time,
    ) in run_experiment(EmbeddingModel.embed_funcs(), num_rounds=1):
        embedding_model = EmbeddingModel.objects.get(name=embedding_model_name)

        eval_time_per_round = []
        for i in range(len(search_times)):
            eval_time_per_round.append(search_times[i] / num_tests[i])

        avrg_eval_time = sum(eval_time_per_round) / len(search_times)

        name = "Embedder Accuracy@1"
        description = "Evaluating embedder models performance, 10 rounds per model"
        EmbedderEval.objects.create(
            embedding_model=embedding_model,
            name=name,
            description=description,
            num_tests=num_tests,
            search_times=search_times,
            embedding_time=embedding_time,
            average_eval_time=avrg_eval_time,
            eval_scores=scores,
            average_score=sum(scores) / len(scores),
        )
