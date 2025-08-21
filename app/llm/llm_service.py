"""Core LLM service for centralized AI communication.

This service provides a single point of contact for all AI text generation,
abstracting the low-level details of streaming and prompt management from
the application logic. It supports dependency injection for testability.
"""

import asyncio
from pathlib import Path

from app.llm.claude_client import ClaudeClient, MessageDone, TextDelta


class LLMService:
    """Stateless service for all AI text generation."""

    def __init__(self, client: ClaudeClient) -> None:
        """
        Initialize the LLM service.

        Args:
            client: Instance of ClaudeClient for AI communication
        """
        self.client = client
        self._prompt_cache: dict[str, str] = {}
        self._cache_lock = asyncio.Lock()

    async def _load_system_prompt(self, prompt_name: str) -> str:
        """
        Load and cache system prompt content from file.

        Thread-safe: Uses asyncio.Lock to prevent race conditions when
        multiple coroutines access the cache concurrently.

        Args:
            prompt_name: Name of the prompt file (without .md extension)

        Returns:
            Content of the system prompt

        Raises:
            FileNotFoundError: If the prompt file doesn't exist
            ValueError: If the prompt file cannot be decoded as UTF-8
        """
        # Check cache with lock
        async with self._cache_lock:
            if prompt_name in self._prompt_cache:
                return self._prompt_cache[prompt_name]

        # Load file outside lock to minimize critical section
        prompt_path = Path(__file__).resolve().parent / "prompts" / f"{prompt_name}.md"

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt '{prompt_name}' not found at: {prompt_path}")

        try:
            with open(prompt_path, encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to decode prompt file '{prompt_name}': {e}") from e

        # Store in cache with lock
        async with self._cache_lock:
            self._prompt_cache[prompt_name] = content

        return content

    async def generate_response(self, transcript: list[str], system_prompt_name: str) -> str:
        """
        Generate AI response from transcript and system prompt.

        Note: This method may return an empty string if the LLM produces no text
        output (only MessageDone events). This is considered valid behavior and
        callers should handle empty responses appropriately.

        Args:
            transcript: List of conversation messages
            system_prompt_name: Name of the system prompt to use

        Returns:
            Complete AI response as a string (may be empty)

        Raises:
            FileNotFoundError: If the prompt file doesn't exist
            ValueError: If the prompt file cannot be decoded as UTF-8
            TimeoutError: If the LLM request times out
            ConnectionError: If there's a network connection issue
            RuntimeError: If there's an error during streaming
        """
        system_prompt = await self._load_system_prompt(system_prompt_name)

        user_prompt = "\n".join(transcript)

        full_response = ""
        try:
            async for event in self.client.stream(
                prompt=user_prompt,
                system_prompt=system_prompt,
            ):
                if isinstance(event, TextDelta):
                    full_response += event.text
                elif isinstance(event, MessageDone):
                    break
        except TimeoutError as e:
            raise TimeoutError(f"LLM request timed out for prompt '{system_prompt_name}'") from e
        except (ConnectionError, OSError) as e:
            raise ConnectionError(
                f"Network connection failed for prompt '{system_prompt_name}': {e}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"Failed to generate response for prompt '{system_prompt_name}': {e}"
            ) from e

        # Note: Empty response is valid - some prompts might produce no text output
        return full_response
