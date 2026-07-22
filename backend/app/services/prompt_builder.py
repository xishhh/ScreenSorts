SYSTEM_PROMPT = (
    "You are a helpful screenshot analysis assistant. "
    "Your task is to explain why a screenshot matches a user's search query. "
    "Be concise (2-4 sentences). "
    "Include: (1) why the screenshot matches the query, (2) key visible information from the text, "
    "(3) a brief summary of what the screenshot shows. "
    "Do not mention similarity scores or confidence values explicitly."
)

USER_TEMPLATE = (
    'User search query: "{query}"\n'
    "Screenshot OCR text:\n{text}\n"
    "Screenshot metadata:\n{metadata}\n"
    "Similarity score: {score}\n\n"
    "Explain why this screenshot matches the search query."
)

SUMMARIZE_SYSTEM_PROMPT = (
    "You are a helpful screenshot analysis assistant. "
    "Summarize the top matching screenshots for a user's search query. "
    "Be concise and highlight the most relevant results."
)

SUMMARIZE_USER_TEMPLATE = (
    'User search query: "{query}"\n'
    "Here are the top matching screenshots and their explanations:\n"
    "{explanations}\n\n"
    "Provide a brief summary of the search results."
)


class PromptBuilder:
    def build_system_prompt(self) -> list[dict[str, str]]:
        return [{"role": "system", "content": SYSTEM_PROMPT}]

    def build_explain_messages(
        self, query: str, text: str, metadata: str, score: float
    ) -> list[dict[str, str]]:
        user_content = USER_TEMPLATE.format(
            query=query,
            text=text if text else "(no OCR text available)",
            metadata=metadata if metadata else "(no metadata available)",
            score=round(score, 4),
        )
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def build_summarize_messages(
        self, query: str, explanations: str
    ) -> list[dict[str, str]]:
        user_content = SUMMARIZE_USER_TEMPLATE.format(
            query=query, explanations=explanations
        )
        return [
            {"role": "system", "content": SUMMARIZE_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    @staticmethod
    def build_metadata_str(
        image_id: str, image_path: str, source_dataset: str
    ) -> str:
        parts = [f"Image ID: {image_id}"]
        if image_path:
            parts.append(f"Path: {image_path}")
        if source_dataset:
            parts.append(f"Dataset: {source_dataset}")
        return "\n".join(parts)
