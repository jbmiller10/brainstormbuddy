"""Core LLM service for centralized AI communication."""

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

    def _load_system_prompt(self, prompt_name: str) -> str:
        """
        Load and cache system prompt content from file.

        Args:
            prompt_name: Name of the prompt file (without .md extension)

        Returns:
            Content of the system prompt

        Raises:
            FileNotFoundError: If the prompt file doesn't exist
        """
        if prompt_name in self._prompt_cache:
            return self._prompt_cache[prompt_name]

        prompt_path = Path(__file__).parent / "prompts" / f"{prompt_name}.md"

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, encoding="utf-8") as f:
            content = f.read()

        self._prompt_cache[prompt_name] = content
        return content

    async def generate_response(self, transcript: list[str], system_prompt_name: str) -> str:
        """
        Generate AI response from transcript and system prompt.

        Args:
            transcript: List of conversation messages
            system_prompt_name: Name of the system prompt to use

        Returns:
            Complete AI response as a string
        """
        system_prompt = self._load_system_prompt(system_prompt_name)

        user_prompt = "\n".join(transcript)

        full_response = ""
        async for event in self.client.stream(
            prompt=user_prompt,
            system_prompt=system_prompt,
        ):
            if isinstance(event, TextDelta):
                full_response += event.text
            elif isinstance(event, MessageDone):
                break

        return full_response
