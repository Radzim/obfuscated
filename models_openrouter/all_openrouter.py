import os

import httpx
import openai

class BaseModel:
    def __init__(self, name, temperature=0.0):
        self.name = name
        self.temperature = temperature

    def __call__(self, prompt):
        raise NotImplementedError()

    @property
    def call_timeout(self):
        return 0


class OpenRouterAPI(BaseModel):
    def __init__(self, model_id):
        self.name_dict = {
            'anthropic': 'anthropic/claude-3.5-haiku',
            'openai': 'openai/gpt-4o-mini',
            'google': 'google/gemini-2.0-flash-001',
            'meta': 'meta-llama/llama-3.3-70b-instruct',
            'deepseek': 'deepseek/deepseek-chat-v3-0324'
        }

        if model_id not in self.name_dict:
            raise ValueError(f"Unknown model name {model_id}")

        super().__init__(model_id)
        self.client = openai.OpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
            timeout=httpx.Timeout(connect=5, read=15, write=15, pool=5)
        )
        self.model = self.name_dict[model_id]

    def __call__(self, prompt):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
        )
        return response.choices[0].message.content

    @property
    def call_timeout(self):
        return 5



def get_model_openrouter(model_id):
    return OpenRouterAPI(model_id)