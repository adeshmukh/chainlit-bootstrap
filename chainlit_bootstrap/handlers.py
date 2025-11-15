"""Chainlit event handlers."""

from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.vectorstores import Chroma

import chainlit as cl

from .llm import embeddings, llm, text_splitter
from .pii import anonymize_text
from .search import (
    TavilyNotConfiguredError,
    is_web_search_configured,
    run_web_search,
)


async def _process_file(file: cl.File) -> bool:
    """
    Process an uploaded file and set up the chain.

    Currently only text files are supported. PDF support requires additional libraries like pypdf.
    Returns True if successful.
    """
    msg = cl.Message(content=f"Processing `{file.name}`...")
    await msg.send()

    try:
        with open(file.path, encoding="utf-8") as f:
            text = f.read()
        if not text.strip():
            await cl.Message(
                content=f"Error: File `{file.name}` is empty. Please upload a file with content."
            ).send()
            return False
    except UnicodeDecodeError:
        await cl.Message(
            content=f"Error: Could not read file `{file.name}`. Please ensure it's a text file."
        ).send()
        return False
    except Exception as e:
        await cl.Message(
            content=f"Error: Failed to read file `{file.name}`: {str(e)}"
        ).send()
        return False

    texts = text_splitter.split_text(text)
    metadatas = [{"source": f"{i}-pl"} for i in range(len(texts))]

    docsearch = await cl.make_async(Chroma.from_texts)(
        texts, embeddings, metadatas=metadatas
    )

    message_history = ChatMessageHistory()
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        chat_memory=message_history,
        return_messages=True,
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm,
        chain_type="stuff",
        retriever=docsearch.as_retriever(),
        memory=memory,
        return_source_documents=True,
    )

    msg.content = f"Processing `{file.name}` done. You can now ask questions!"
    await msg.update()

    cl.user_session.set("chain", chain)
    cl.user_session.set("file_name", file.name)
    return True


def _get_general_history() -> ChatMessageHistory:
    """Return or initialize the general chat history for the session."""
    history: ChatMessageHistory | None = cl.user_session.get("general_history")
    if history is None:
        history = ChatMessageHistory()
        cl.user_session.set("general_history", history)
    return history


async def _respond_with_general_chat(user_input: str) -> None:
    """Provide a response using the base LLM when no document is loaded."""
    if not user_input.strip():
        await cl.Message(
            content="Please enter a question or upload a document to get started."
        ).send()
        return

    history = _get_general_history()
    history.add_user_message(user_input)

    cb = cl.AsyncLangchainCallbackHandler()
    response = await llm.ainvoke(history.messages, callbacks=[cb])

    sanitized_answer = anonymize_text(response.content)
    history.add_ai_message(sanitized_answer)

    await cl.Message(content=sanitized_answer).send()


def _extract_search_query(user_input: str) -> str | None:
    """Return the search query if the user prefixed their message with a search command."""
    if not user_input:
        return None

    trimmed = user_input.strip()
    lower_trimmed = trimmed.lower()

    if lower_trimmed.startswith("/search"):
        parts = trimmed.split(maxsplit=1)
        return parts[1].strip() if len(parts) > 1 else ""
    if lower_trimmed.startswith("!search"):
        parts = trimmed.split(maxsplit=1)
        return parts[1].strip() if len(parts) > 1 else ""
    for prefix in ("search:", "web:", "lookup:"):
        if lower_trimmed.startswith(prefix):
            return trimmed[len(prefix) :].strip()

    return None


async def _respond_with_web_search(query: str) -> None:
    """Execute a Tavily web search and stream the results back to the user."""
    if not query:
        await cl.Message(
            content="Please provide a query after the `/search` command. Example: `/search latest Chainlit release`"
        ).send()
        return

    progress = cl.Message(content=f"🔎 Searching the web for `{query}`...")
    await progress.send()

    try:
        results = await cl.make_async(run_web_search)(query)
    except TavilyNotConfiguredError:
        await progress.update(
            content=(
                "⚠️ Web search is not configured. "
                "Set the `TAVILY_API_KEY` environment variable and restart the app."
            )
        )
        return
    except Exception as exc:  # noqa: BLE001
        await progress.update(
            content=f"❌ Web search failed: {type(exc).__name__}: {exc}"
        )
        return

    if not results:
        await progress.update(content=f"🔎 No web results found for `{query}`.")
        return

    formatted_results = []
    for idx, result in enumerate(results, start=1):
        title = result.get("title") or "Untitled result"
        url = result.get("url") or ""
        snippet = result.get("content") or result.get("snippet") or ""
        sanitized_snippet = anonymize_text(snippet) if snippet else ""
        if url:
            formatted_results.append(
                f"{idx}. **[{title}]({url})**\n{sanitized_snippet}".strip()
            )
        else:
            formatted_results.append(f"{idx}. **{title}**\n{sanitized_snippet}".strip())

    await progress.update(
        content="🔎 **Web search results:**\n\n" + "\n\n".join(formatted_results)
    )


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session and ensure database is initialized."""
    # Trigger database initialization to ensure tables exist before Chainlit queries them
    try:
        data_layer = cl.data_layer
        if data_layer:
            try:
                await data_layer.list_threads(user_id="__init__", pagination=None, filters=None)
            except Exception:
                # Tables will be created on next access if this fails (expected on first run)
                pass
    except Exception:
        # Database will be initialized when actually needed
        pass

    chain = cl.user_session.get("chain")
    if chain:
        file_name = cl.user_session.get("file_name", "document")
        await cl.Message(
            content=f"👋 Welcome back! You can continue asking questions about `{file_name}`."
        ).send()
        return

    welcome_message = (
        "👋 Welcome! You can start chatting right away or optionally upload a text file (📎) "
        "if you want me to answer questions about that document."
    )
    if is_web_search_configured():
        welcome_message += (
            "\n\nNeed the latest info? Type `/search your question` to run a live Tavily web search."
        )

    await cl.Message(content=welcome_message).send()


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages with PII detection and document QA."""
    # Handle file uploads if present
    if message.elements:
        for element in message.elements:
            if isinstance(element, cl.File):
                success = await _process_file(element)
                if success:
                    await cl.Message(
                        content="✅ File processed successfully! You can now ask questions about the document."
                    ).send()
                else:
                    await cl.Message(
                        content="❌ Failed to process the file. Please ensure it's a valid text file and try again."
                    ).send()

                # If no text content with file, return early
                if not message.content or not message.content.strip():
                    return
                break

    user_content = message.content or ""
    sanitized_input = anonymize_text(user_content) if user_content else ""

    raw_search_query = _extract_search_query(user_content or "")
    if raw_search_query is not None:
        await _respond_with_web_search(raw_search_query)
        return

    chain: ConversationalRetrievalChain | None = cl.user_session.get("chain")
    if not chain:
        await _respond_with_general_chat(sanitized_input)
        return

    cb = cl.AsyncLangchainCallbackHandler()
    res = await chain.acall(sanitized_input, callbacks=[cb])

    sanitized_answer = anonymize_text(res["answer"])
    source_documents = res["source_documents"]
    text_elements: list[cl.Text] = []

    if source_documents:
        for source_idx, source_doc in enumerate(source_documents):
            source_name = f"source_{source_idx}"
            text_elements.append(
                cl.Text(
                    content=source_doc.page_content, name=source_name, display="side"
                )
            )
        source_names = [text_el.name for text_el in text_elements]
        sanitized_answer += f"\nSources: {', '.join(source_names)}" if source_names else "\nNo sources found"

    await cl.Message(content=sanitized_answer, elements=text_elements).send()


@cl.on_audio_chunk
async def on_audio_chunk(audio_chunk):
    """
    Handle real-time audio chunks for voice input.

    TODO: Implement OpenAI Realtime API integration.
    Currently a placeholder that acknowledges audio input.
    """
    if hasattr(audio_chunk, "isStart") and audio_chunk.isStart:
        await cl.Message(content="🎤 Listening...").send()
    elif hasattr(audio_chunk, "isEnd") and audio_chunk.isEnd:
        await cl.Message(
            content="Voice input received. Full OpenAI Realtime API integration coming soon!"
        ).send()
