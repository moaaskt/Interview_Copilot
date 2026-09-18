import re
import unicodedata
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class QuestionDetectionResult:
    """Resultado da análise de detecção de pergunta."""
    is_question: bool
    confidence: float  # Score heurístico no intervalo [0.0, 1.0] (NÃO é probabilidade estatística)
    reason: str        # 'punctuation' | 'interview_pattern' | 'interrogative' | 'none'


class QuestionDetector:
    """
    Motor determinístico de classificação e detecção de perguntas em tempo real
    para streams de áudio/transcrição de entrevistas técnicas.
    """

    def __init__(self, threshold: float = 0.70) -> None:
        self.threshold = threshold

        # Padrões imperativos clássicos de recrutadores / entrevistas técnicas
        self._interview_patterns = [
            # Português
            r"^(me\s+conte|conte-me|me\s+fale|fale\s+sobre|explique|descreva|compartilhe|diga|dê\s+um\s+exemplo|como\s+voc[eê]\s+aborda|qual\s+[eé]\s+sua\s+experi[eê]ncia|qual\s+foi\s+um\s+desafio)(\s+|$)",
            # Inglês
            r"^(tell\s+me\s+about|describe|explain|walk\s+me\s+through|share\s+an\s+example|how\s+do\s+you\s+approach|what\s+is\s+your\s+experience)(\s+|$)",
        ]

        # Palavras e locuções interrogativas no início da sentença ou de orações
        self._interrogative_openers = [
            # Português
            r"^(como|qual|quais|por\s*que|porque|o\s+que|quando|onde|quem|quanto|quantos|voc[eê]\s+j[aá]|voc[eê]\s+tem|voc[eê]\s+sabe|consegue|poderia|seria\s+poss[ií]vel)(\s+|$)",
            # Inglês
            r"^(how|what|why|when|where|who|which|can\s+you|could\s+you|have\s+you\s+ever|do\s+you\s+know|is\s+it\s+possible|would\s+you)(\s+|$)",
        ]

    def _clean_text(self, text: str) -> str:
        """Sanitiza e normaliza o texto para análise."""
        if not text:
            return ""
        # Remove caracteres de controle invisíveis e normaliza espaços múltiplos
        cleaned = re.sub(r"\s+", " ", text.strip())
        return cleaned

    def detect(self, text: Optional[str]) -> QuestionDetectionResult:
        """
        Classifica deterministicamente se o texto informado representa uma pergunta
        ou solicitação típica de entrevista.
        """
        cleaned = self._clean_text(text or "")
        if not cleaned:
            return QuestionDetectionResult(is_question=False, confidence=0.0, reason="none")

        # 1. Heurística de Pontuação Direta (?)
        if "?" in cleaned:
            # Verifica se o ponto de interrogação está no final ou encerra uma oração
            trimmed_punct = cleaned.rstrip(". ,;:!")
            if trimmed_punct.endswith("?"):
                return QuestionDetectionResult(
                    is_question=True,
                    confidence=0.95,
                    reason="punctuation"
                )

        # Normaliza para minúsculo para testes de prefixo e padrões
        lower_text = cleaned.lower()

        # 2. Heurística de Padrões Clássicos de Entrevista Técnica
        for pattern in self._interview_patterns:
            if re.search(pattern, lower_text, re.IGNORECASE):
                confidence = 0.85
                return QuestionDetectionResult(
                    is_question=confidence >= self.threshold,
                    confidence=confidence,
                    reason="interview_pattern"
                )

        # 3. Heurística de Abertura Interrogativa no início da sentença ou após pontuação de corte
        # Divide em orações caso haja frases encadeadas
        clauses = re.split(r"[,;.]\s*", lower_text)
        for clause in clauses:
            clause_clean = clause.strip()
            if not clause_clean:
                continue
            for pattern in self._interrogative_openers:
                if re.search(pattern, clause_clean, re.IGNORECASE):
                    confidence = 0.80
                    return QuestionDetectionResult(
                        is_question=confidence >= self.threshold,
                        confidence=confidence,
                        reason="interrogative"
                    )

        # 4. Caso padrão: Sentença afirmativa ou fala não interrogativa
        return QuestionDetectionResult(
            is_question=False,
            confidence=0.10,
            reason="none"
        )
