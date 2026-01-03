import djclick as click
from loguru import logger
from django.core.management import call_command



@click.command()
@click.option("--repo", required=True, help="GitHub repository in format owner/repo")
def gen_synth_data(repo):
    call_command('fetch_from_github', repo=repo)
    logger.info(f"Generating synthetic training data for repository: {repo}")


if __name__ == "__main__":
    gen_synth_data()