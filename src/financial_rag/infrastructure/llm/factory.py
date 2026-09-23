"""Factory for instantiating configured LLM providers."""

from financial_rag.config.settings import LLMSettings, get_settings
from financial_rag.domain.interfaces.llm import LLMProviderProtocol
from financial_rag.infrastructure.llm.fake_provider import FakeLLMProvider
from financial_rag.infrastructure.llm.openai_provider import OpenAILLMProvider
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.llm.factory")


def create_llm_provider(llm_settings: LLMSettings | None = None) -> LLMProviderProtocol:
    """Instantiate and configure the appropriate LLM provider adapter."""
    settings = llm_settings or get_settings().llm
    provider_name = settings.provider.lower().strip()

    if provider_name in ("openai", "azure_openai"):
        logger.info(f"Instantiating OpenAI LLM Provider (model='{settings.model_name}')")
        return OpenAILLMProvider(llm_settings=settings)

    # Default to Fake/Mock LLM provider for deterministic tests and offline dev
    logger.info(f"Instantiating Fake LLM Provider (model='{settings.model_name}')")
    return FakeLLMProvider(model_name=settings.model_name)
