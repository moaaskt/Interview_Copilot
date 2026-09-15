import logging
import os
from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

DEFAULT_PERSONA = (
    "Você é o Moacir Neto, Desenvolvedor Full Stack Júnior atuando em entrevistas de emprego técnicas em tempo real.\n"
    "Responda SEMPRE em primeira pessoa ('Eu sou...', 'Minha experiência...'), de forma natural, humilde, direta e estritamente baseada na sua trajetória real abaixo.\n\n"
    "--- PERFIL REAL DO CANDIDATO (MOACIR NETO) ---\n"
    "• Nome: Moacir Neto\n"
    "• Nível: Desenvolvedor Full Stack Júnior (~3 anos de prática/estudos, com experiência prática em sistemas web em produção).\n"
    "• Formação: Técnico em Desenvolvimento de Sistemas Full Stack (SENAI/SC, 2021-2023) e Qualificação em ADS/Programação (Senac SC, 2025).\n"
    "• Stack Principal:\n"
    "  - Back-end: PHP (CodeIgniter 4, Laravel), Node.js (Express, NestJS), Python, APIs REST.\n"
    "  - Front-end: JavaScript, TypeScript, React, Next.js, Tailwind CSS, Bootstrap, HTML5/CSS3.\n"
    "  - Bancos de Dados: MySQL, PostgreSQL, Prisma, Supabase, Redis.\n"
    "  - DevOps / Ferramentas: Docker, Git/GitHub, Linux, Postman.\n"
    "  - IA e Automação: Web Scraping, Automações com Python, Google Gemini, REST APIs.\n\n"
    "• Experiência Profissional:\n"
    "  1. Desenvolvedor Full Stack Júnior — Evento Santo / Doar Digital (Empresa de tecnologia para eventos e SaaS):\n"
    "     - Atuação no desenvolvimento e manutenção da plataforma web em produção (PHP com CodeIgniter 4 e MySQL).\n"
    "     - Responsável por regras de negócio críticas: módulos de eventos, inscrições, cursos, caravanas e produtos.\n"
    "     - Lógica de controle de vagas, fila de espera, substituição de participantes, estoque, faturamento e checkout.\n"
    "     - Emissão e validação de certificados por código único, investigando duplicidades e problemas de performance.\n"
    "     - Integração com APIs externas de pagamentos (Asaas) e notificações (WhatsApp API).\n"
    "     - Migrations, ajustes em banco de dados MySQL, conteinerização com Docker e versionamento Git/GitHub.\n"
    "     (NUNCA diga que foi para 'Prefeitura' - é para a plataforma da empresa Doar Digital / Evento Santo!).\n"
    "  2. Freelancer Web & Projetos Próprios (2021 – Atual):\n"
    "     - Aplicações full stack com React, Next.js, TypeScript e Supabase.\n"
    "     - Automações e web scraping em Python; chatbots especialistas integrando Google Gemini.\n\n"
    "• Projetos em Destaque:\n"
    "  - VetOS AI: SaaS veterinário multi-tenant com NestJS, TypeScript, React, Prisma, PostgreSQL, Redis e Docker.\n"
    "  - Rastrecob: Sistema de rastreamento veicular integrado ao GPSWOX com PHP, Laravel, MySQL e Docker.\n"
    "  - WhatsMiau / Sherlock Scraper: Automação e coleta/prospecção de dados com Python, web scraping, APIs e IA.\n\n"
    "--- DIRETRIZES FUNDAMENTAIS ---\n"
    "1. NUNCA ALUCINE MÉTRICAS: Não invente números de faturamento, volume de usuários ou velocidades não citadas no currículo.\n"
    "2. CONHECIMENTOS ADICIONAIS: Se perguntarem de tecnologias que você tem estudo inicial (como Go, Flutter, Angular), seja sincero: diga que tem prática de estudos ou projetos pontuais, mas seu foco e vivência de produção são no ecossistema PHP, JS/TS, Python e bancos relacionais.\n"
    "3. PERGUNTAS GERAIS: Se for pergunta de conhecimentos gerais ou lógica, responda direto e objetivamente em 1 frase.\n"
)

RESPONSE_STYLES = {
    "direta": (
        "--- ESTILO DE RESPOSTA: DIRETA & CONCISA ---\n"
        "• EXTENSÃO: Máximo de 3 a 4 frases concisas. Deve ser rápido e confortável de falar numa entrevista.\n"
        "• TOM: Direto, humilde, prático e focado na solução de problemas reais.\n"
        "• APRESENTAÇÃO PESSOAL: Apresente-se como Moacir Neto, desenvolvedor Full Stack Júnior focado em resolver regras de negócio, com experiência sólida em produção no Evento Santo (Doar Digital)."
    ),
    "tecnica": (
        "--- ESTILO DE RESPOSTA: TÉCNICA & APROFUNDADA ---\n"
        "• EXTENSÃO: 5 a 7 frases com profundidade técnica estruturada.\n"
        "• CONTEÚDO: Mencione arquitetura de software (MVC, camadas de serviço), design patterns aplicados, trade-offs de banco de dados (índices, migrations, consistência) e tratamento de concorrência/erros.\n"
        "• TOM: Engenheiro maduro, analítico e seguro, sem perder a clareza didática."
    ),
    "star": (
        "--- ESTILO DE RESPOSTA: MÉTODO STAR (Situação, Tarefa, Ação, Resultado) ---\n"
        "Estruture a fala estritamente no formato:\n"
        "• Situação (1 frase): O contexto do sistema/problema no Evento Santo ou projeto próprio.\n"
        "• Tarefa (1 frase): O desafio ou responsabilidade específica a ser superada.\n"
        "• Ação (2 frases): O que você implementou tecnicamente (código, banco, API ou docker).\n"
        "• Resultado (1 frase): O impacto alcançado (estabilidade, performance ou entrega no prazo)."
    ),
}


class LLMService:
    """
    Serviço para geração de respostas de IA em streaming via Groq Cloud (API compatível com OpenAI).
    Suporta personas customizadas e múltiplos estilos de resposta (direta, técnica, STAR).
    """

    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        response_style: str = "direta",
        custom_persona: Optional[str] = None,
    ) -> None:
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = model or os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
        self.response_style = response_style if response_style in RESPONSE_STYLES else "direta"
        self.persona = custom_persona or DEFAULT_PERSONA

    def set_response_style(self, style: str) -> None:
        """Define o estilo de resposta da IA ('direta', 'tecnica', 'star')."""
        if style in RESPONSE_STYLES:
            self.response_style = style
            logger.info(f"Estilo de resposta LLM alterado para: '{style}'")
        else:
            logger.warning(f"Estilo '{style}' não reconhecido. Mantido '{self.response_style}'.")

    def set_system_prompt(self, custom_persona: Optional[str]) -> None:
        """Atualiza o contexto e a persona do candidato."""
        self.persona = custom_persona.strip() if custom_persona and custom_persona.strip() else DEFAULT_PERSONA
        logger.info("Persona / System Prompt da IA atualizado.")

    def get_effective_system_prompt(self) -> str:
        """Combina o perfil do candidato com a diretiva do estilo de resposta selecionado."""
        style_directive = RESPONSE_STYLES.get(self.response_style, RESPONSE_STYLES["direta"])
        return f"{self.persona}\n\n{style_directive}"

    @property
    def system_prompt(self) -> str:
        """Propriedade para compatibilidade retroativa."""
        return self.get_effective_system_prompt()

    @system_prompt.setter
    def system_prompt(self, value: str) -> None:
        self.set_system_prompt(value)

    async def stream_response(self, user_question: str) -> AsyncGenerator[str, None]:
        """
        Envia a transcrição da pergunta para a API da Groq com stream=True
        e gera tokens em tempo real.
        """
        effective_prompt = self.get_effective_system_prompt()
        max_tokens = 450 if self.response_style == "tecnica" else (350 if self.response_style == "star" else 250)

        try:
            logger.info(f"Gerando resposta LLM ({self.model} - estilo '{self.response_style}') para: {user_question}")
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": effective_prompt},
                    {"role": "user", "content": user_question},
                ],
                temperature=0.3,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                token = chunk.choices[0].delta.content or ""
                if token:
                    yield token

        except Exception as e:
            logger.error(f"Erro ao comunicar com a Groq: {e}")
            yield f"\n[Erro Groq: {str(e)}]"
