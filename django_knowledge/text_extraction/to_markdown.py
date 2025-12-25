from markdownify import markdownify as md


def convert_to_makdown(html):
    return md(html)
