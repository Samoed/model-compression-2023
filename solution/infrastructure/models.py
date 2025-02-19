from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

import torch
from optimum.onnxruntime import ORTModelForSequenceClassification
from optimum.pipelines import pipeline
from transformers import AutoModelForSequenceClassification, AutoTokenizer


@dataclass
class TextClassificationModelData:
    model_name: str
    label: str
    score: float


class BaseTextClassificationModel(ABC):
    def __init__(self, name: str, model_path: str, tokenizer: str):
        self.name = name
        self.model_path = model_path
        self.tokenizer = tokenizer
        self.device = 0 if torch.cuda.is_available() else "cpu"
        self._load_model()

    @abstractmethod
    def _load_model(self):
        ...

    @abstractmethod
    def __call__(self, inputs) -> List[TextClassificationModelData]:
        ...


class TransformerTextClassificationModel(BaseTextClassificationModel):
    def _load_model(self):
        self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path).to(self.device)

    def tokenize_texts(self, texts: List[str]):
        inputs = self.tokenizer.batch_encode_plus(
            texts,
            add_special_tokens=True,
            padding="longest",
            truncation=True,
            return_token_type_ids=True,
            return_tensors="pt",
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}  # Move inputs to GPU
        return inputs

    def _results_from_logits(self, logits: torch.Tensor):
        id2label = self.model.config.id2label

        label_ids = logits.argmax(dim=1)
        scores = logits.softmax(dim=-1)
        results = [
            {"label": id2label[label_id.item()], "score": score[label_id.item()].item()}
            for label_id, score in zip(label_ids, scores)
        ]
        return results

    def __call__(self, inputs) -> List[TextClassificationModelData]:
        logits = self.model(**inputs).logits
        predictions = self._results_from_logits(logits)
        predictions = [
            TextClassificationModelData(self.name, **prediction)
            for prediction in predictions
        ]
        return predictions


class CustomTransformerTextClassificationModel(TransformerTextClassificationModel):
    def _load_model(self):
        model = ORTModelForSequenceClassification.from_pretrained(
            self.model_path, from_transformers=True
        )
        tokenizer = AutoTokenizer.from_pretrained(self.tokenizer)
        self.model = pipeline(
            task="text-classification",
            model=model,
            tokenizer=tokenizer,
            accelerator="ort",
            device=self.device,
        )

    def __call__(self, inputs: List[str]) -> List[TextClassificationModelData]:
        return self.model(inputs)
