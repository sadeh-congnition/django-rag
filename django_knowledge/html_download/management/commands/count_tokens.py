import djclick as click

from tokenization.tokenize import count_tokens


@click.command()
def command():
    count_tokens()
