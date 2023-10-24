from typing import List

from pydantic_yaml import YamlModel


class ModelConfig(YamlModel):
    model: str
    model_path: str
    tokenizer: str


class AppConfig(YamlModel):
    # model parameters
    models: list[ModelConfig]
    # app parameters
    port: int
    workers: int
    # async queues parameters
    timeout: float
