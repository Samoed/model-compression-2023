from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from infrastructure.models import (
    BaseTextClassificationModel,
    TextClassificationModelData,
)


class TextClassificationService:
    def __init__(self, models: list[BaseTextClassificationModel]):
        self.service_models = models

    def get_results(self, input_texts: list[str]) -> list[list[TextClassificationModelData]]:
        results = [model(input_texts) for model in self.service_models]
        return results
