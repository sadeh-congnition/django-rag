import djclick as click

from chunking.models import ChunkConfig
from experiment_tracking.models import EmbeddingModel, EmbedderEval, EmbedderEvalConfig, BadResult
from experiment_tracking.run import run_experiment


@click.command()
@click.argument("chunk_config_id", type=int)
def eval_embedding_models(chunk_config_id):
    EmbeddingModel.create_defaults()
    
    chunk_config = ChunkConfig.objects.get(id=chunk_config_id)

    metric_name = "Embedder Accuracy@1"
    num_rounds = 1

    for (
        embedding_model_name,
        num_tests,
        scores,
        search_times,
        embedding_time,
        bad_results,
    ) in run_experiment(EmbeddingModel.embed_funcs(), num_rounds=num_rounds, chunk_config_id=chunk_config_id):
        embedding_model = EmbeddingModel.objects.get(name=embedding_model_name)

        eval_time_per_round = []
        for i in range(len(search_times)):
            eval_time_per_round.append(search_times[i] / num_tests[i])

        avrg_eval_time = sum(eval_time_per_round) / len(search_times)

        embedder_eval_config = EmbedderEvalConfig.objects.create(
            chunk_config=chunk_config,
            content={
                "metrics": {
                    "name": metric_name,
                    "average_eval_time": avrg_eval_time,
                    "average_score": sum(scores) / len(scores),
                    "num_tests": num_tests,
                    "scores": scores,
                    "search_times": search_times,
                    "embedding_time": embedding_time,
                }
            }
        )
        
        description = (
            f"Evaluating embedder models performance, {num_rounds} rounds per model"
        )
        embedder_eval = EmbedderEval.objects.create(
            embedding_model=embedding_model,
            config=embedder_eval_config,
            name=metric_name,
            description=description,
            num_tests=num_tests,
            search_times=search_times,
            embedding_time=embedding_time,
            average_eval_time=avrg_eval_time,
            eval_scores=scores,
            average_score=sum(scores) / len(scores),
        )
        
        for bad_result in bad_results:
            BadResult.objects.create(
                embedder_eval=embedder_eval,
                content=bad_result
            )
