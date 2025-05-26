from .all_openrouter import BaseModel, get_model_openrouter
from .model_caller import ModelCaller

def get_model(model_name):
    return get_model_openrouter(model_name)
