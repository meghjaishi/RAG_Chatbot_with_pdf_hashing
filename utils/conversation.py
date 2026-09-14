from __future__ import annotations
import tiktoken
from models import ConversationMessage
from utils.tokens import count_tokens



DEFAULT_MAX_TURNS = 5
DEFAULT_MAX_TOKENS = 3000

def _get_encoding():
    """
    Return the tokenizer used by the OpenAI model family.
    """

    return tiktoken.get_encoding("cl100k_base")

def count_message_tokens(
    message: ConversationMessage,
) -> int:
    """
    Estimate the number of tokens in one conversation message.
    """
    # encoding = _get_encoding()
    # return len(
    #     encoding.encode(
    #         message.content
    #     )
    # )

    return count_tokens(
        message.content
    )

def trim_conversation_history(
    history: list[ConversationMessage] | None,
    max_turns: int = DEFAULT_MAX_TURNS,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> list[ConversationMessage]:
    """
    Keep only the most recent conversation turns.
    One turn consists of a user message followed by an assistant message.
    """
    if not history:
        return []
    
    if max_turns <= 0 or max_tokens <= 0:
        return []

    # --------------------------------------------------
    # Build complete user -> assistant turns
    # --------------------------------------------------
    turns: list[list[ConversationMessage]] = []

    current_turn: list[ConversationMessage] = []

    for message in history:

        current_turn.append(message)

        if message.role == "assistant":

            turns.append(
                current_turn
            )

            current_turn = []

    # --------------------------------------------------
    # Handle an incomplete final user message
    # --------------------------------------------------

    if current_turn:
        turns.append(current_turn)

    # # work backward in complete user/assistant pairs.
    # turns: list[list[ConversationMessage]] = []
    # current_turn: list[ConversationMessage] = []

    # for message in reversed(history):
    #     current_turn.insert(
    #         0,
    #         message,
    #     )
    #     if message.role == "user":
    #         turns.insert(
    #             0,
    #             current_turn
    #         )
    #         currrent_turn = []

    turns = turns[-max_turns:]
    
    # max_messages = max_turns * 2

    selected: list[list[ConversationMessage]] = []
    total_tokens = 0

    for turn in reversed(turns):
        turn_tokens = sum(
            count_message_tokens(message)
            for message in turn
        )

        if (
            total_tokens + turn_tokens > max_tokens
        ):
            break

        selected.insert(
            0, 
            turn,
        )
        total_tokens += turn_tokens

    result = [
        message 
        for turn in selected
        for message in turn
    ]

    assert len(result) <= len(history), (
        "Conversation history management increased "
        "the number of messages."
    )

    return result

    # for message in reversed(history[-max_messages:]):
    #     message_tokens = count_message_tokens(message)

    #     if (total_tokens + message_tokens > max_tokens):
    #         break

    #     selected.append(message)

    #     total_tokens += message_tokens
    # selected.reverse()

    # return selected