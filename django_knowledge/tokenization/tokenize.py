# Coded by the VS Code Agent using GPT-5 mini model
# No human editing needed to run successfully
from html_download.models import Page
from loguru import logger
import tiktoken


def count_tokens():
    all_texts = []
    for page in Page.objects.all():
        all_texts.append(page.cleaned_text)

    combined = "\n\n".join(all_texts)

    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(combined)
    logger.info("TOTAL_TOKENS:\t" + str(len(tokens)))
    logger.info("TOTAL_CHARS:\t" + str(len(combined)))
