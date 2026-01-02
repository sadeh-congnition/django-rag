from openai import OpenAI


client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")


def get_embeddings(model_name: str, text: str) -> list[float]:
    return client.embeddings.create(input=[text], model=model_name).data[0].embedding
