# tests/examples/openai_connection.py

# Standard Imports
import sys
from pathlib import Path
# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Third Party Imports
from openai import AzureOpenAI

# Local Imports
from core.config import settings


client = AzureOpenAI(
    api_key=settings.azure_openai.api_key,
    api_version=settings.azure_openai.api_version,
    azure_endpoint=settings.azure_openai.endpoint
)

completion = client.chat.completions.create(
    model=settings.azure_openai.deployment_name,
    messages=[
        {"role": "user", "content": "What is the capital of France?"},
    ],
)
print(completion)
