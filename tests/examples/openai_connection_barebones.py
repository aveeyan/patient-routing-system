import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    base_url="https://patientroutingsystemazureopenai.openai.azure.com/openai/v1/",
)

response = client.responses.create(
  model="gpt-4.1-mini", # Replace with your model deployment name
  input="This is a test.",
)

print(response.model_dump_json(indent=2))
