"""
Isolated Semantic Entailment Evaluator for EKIP Platform.

Evaluates claim-to-evidence entailment using NLI models with local caching,
lazy initialization, and deterministic fallback mechanics.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional

logger = logging.getLogger("core.validation.entailment_evaluator")

DEFAULT_MODEL_NAME = "cross-encoder/nli-deberta-v3-small"


@dataclass
class EntailmentResult:
    label: str  # "ENTAILED", "CONTRADICTED", "NEUTRAL"
    confidence: float
    scores: Dict[str, float]
    evaluator_mode: str  # "nli" or "heuristic_fallback"
    fallback_reason: Optional[str] = None


class EntailmentEvaluator:
    """Isolated Entailment Evaluator with lazy CrossEncoder loading and fallback."""

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, disabled: bool = False):
        self.model_name = model_name
        self.disabled = disabled
        self._model = None
        self._initialized = False
        self._init_failed = False
        self._fallback_reason = None

    def _load_model_lazy(self):
        if self.disabled:
            self._init_failed = True
            self._fallback_reason = "evaluator_explicitly_disabled"
            return

        if self._initialized or self._init_failed:
            return

        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Lazy loading CrossEncoder model: {self.model_name}")
            self._model = CrossEncoder(self.model_name)
            self._initialized = True
        except Exception as e:
            logger.warning(f"Failed to load CrossEncoder model '{self.model_name}': {e}. Falling back to heuristic mode.")
            self._init_failed = True
            self._fallback_reason = f"model_load_failed: {str(e)}"

    def evaluate(self, claim: str, evidence_text: str) -> EntailmentResult:
        """
        Evaluate entailment between claim and evidence_text.
        Returns EntailmentResult with label: ENTAILED | CONTRADICTED | NEUTRAL.
        """
        if not claim or not evidence_text:
            return EntailmentResult(
                label="NEUTRAL",
                confidence=0.0,
                scores={"entailment": 0.0, "contradiction": 0.0, "neutral": 1.0},
                evaluator_mode="heuristic_fallback",
                fallback_reason="empty_claim_or_evidence"
            )

        self._load_model_lazy()

        if self._model is not None and self._initialized:
            try:
                scores_raw = self._model.predict([(claim, evidence_text)])
                if hasattr(scores_raw, "shape") and len(scores_raw.shape) > 1:
                    raw_vec = scores_raw[0]
                else:
                    raw_vec = scores_raw

                import numpy as np
                exp_vec = np.exp(raw_vec - np.max(raw_vec))
                probs = exp_vec / np.sum(exp_vec)

                label_mapping = {0: "CONTRADICTED", 1: "ENTAILED", 2: "NEUTRAL"}
                if hasattr(self._model, "config") and hasattr(self._model.config, "id2label"):
                    id2label = self._model.config.id2label
                    for idx, lbl in id2label.items():
                        lbl_upper = str(lbl).upper()
                        if "ENTAIL" in lbl_upper:
                            label_mapping[idx] = "ENTAILED"
                        elif "CONTRADIC" in lbl_upper:
                            label_mapping[idx] = "CONTRADICTED"
                        else:
                            label_mapping[idx] = "NEUTRAL"

                scores_dict = {
                    "contradiction": float(probs[0]) if len(probs) > 0 else 0.0,
                    "entailment": float(probs[1]) if len(probs) > 1 else 0.0,
                    "neutral": float(probs[2]) if len(probs) > 2 else 0.0,
                }

                best_idx = int(np.argmax(probs))
                predicted_label = label_mapping.get(best_idx, "NEUTRAL")
                confidence = float(probs[best_idx])

                return EntailmentResult(
                    label=predicted_label,
                    confidence=round(confidence, 4),
                    scores={k: round(v, 4) for k, v in scores_dict.items()},
                    evaluator_mode="nli",
                    fallback_reason=None
                )
            except Exception as e:
                logger.warning(f"CrossEncoder inference error: {e}. Falling back to heuristic mode.")

        return self._heuristic_fallback_evaluate(claim, evidence_text)

    def _heuristic_fallback_evaluate(self, claim: str, evidence_text: str) -> EntailmentResult:
        """Deterministic lexical/heuristic fallback when NLI model is unavailable."""
        import re
        stopwords = {"this", "that", "with", "from", "have", "explain", "concept", "system", "model", "architecture", "using", "which", "where", "what", "how"}
        words = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9]{4,}\b', claim) if w.lower() not in stopwords]

        if not words:
            return EntailmentResult(
                label="NEUTRAL",
                confidence=0.0,
                scores={"entailment": 0.0, "contradiction": 0.0, "neutral": 1.0},
                evaluator_mode="heuristic_fallback",
                fallback_reason=self._fallback_reason or "nli_unavailable"
            )

        src_lower = evidence_text.lower()
        matches = sum(1 for w in words if w in src_lower)
        ratio = matches / len(words)

        if ratio >= 0.35:
            label = "ENTAILED"
            conf = ratio
        else:
            label = "NEUTRAL"
            conf = 1.0 - ratio

        return EntailmentResult(
            label=label,
            confidence=round(conf, 4),
            scores={"entailment": round(ratio, 4), "contradiction": 0.0, "neutral": round(1.0 - ratio, 4)},
            evaluator_mode="heuristic_fallback",
            fallback_reason=self._fallback_reason or "nli_unavailable"
        )
