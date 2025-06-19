# Azure AI Inference Integration Example

This action now uses the Azure AI Inference SDK to communicate with GitHub Models, providing better error handling and type safety.

## Integration Details

### Dependencies

- `azure-ai-inference>=1.0.0` - Official Azure SDK for AI inference
- `requests>=2.28.0` - Still needed for Codecov API
- `PyYAML>=6.0` - For configuration parsing

### API Usage Example

```python
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

# Initialize client
endpoint = "https://models.github.ai/inference"
token = os.environ["GITHUB_TOKEN"]

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
)

# Generate completion
response = client.complete(
    messages=[
        SystemMessage("You are a helpful assistant."),
        UserMessage("Generate unit tests for this code..."),
    ],
    model="openai/gpt-4.1-mini",
    temperature=0.2,
    top_p=1.0,
    max_tokens=4096
)

result = response.choices[0].message.content
```

## Default Model

The action now uses `openai/gpt-4.1-mini` by default, which provides:

- Better cost efficiency
- Good performance for code generation tasks
- Faster response times
- Lower token usage

## Benefits of Azure AI Inference SDK

1. **Type Safety**: Strongly typed request/response objects
2. **Error Handling**: Better exception handling and error messages
3. **Authentication**: Integrated credential management
4. **Reliability**: Official SDK with built-in retry logic
5. **Future-Proof**: Automatic updates for new features

## Migration from Direct HTTP

The action has been updated from direct HTTP requests to the Azure AI Inference SDK:

### Before (HTTP)

```python
response = requests.post(
    "https://models.github.ai/inference/chat/completions",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "messages": [{"role": "user", "content": prompt}],
        "model": "gpt-4o"
    }
)
```

### After (Azure SDK)

```python
response = client.complete(
    messages=[UserMessage(prompt)],
    model="openai/gpt-4.1-mini"
)
```

This provides better reliability and maintainability for the action.
