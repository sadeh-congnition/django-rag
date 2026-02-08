import djclick as click
from experiment_tracking.models import EmbeddingModel, Sample
from django.core.management import call_command
import subprocess


@click.command()
def run_all_embedding_evals():
    embedding_eval_models = EmbeddingModel.objects.order_by("id").all()
    samples = Sample.objects.all()
    for embedding_eval_model in embedding_eval_models:
        for sample in samples:
            call_command(
                "eval_embedding_models",
                "--chunk-config-id",
                1,
                "--embedding-model-id",
                embedding_eval_model.id,
                "--num-test-samples",
                2000,
                "--sample-id",
                sample.id,
            )
        subprocess.run(["rm", "-rf", "chromadb_data"], check=True)
        break