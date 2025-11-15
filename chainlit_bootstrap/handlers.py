"""Chainlit event handlers."""

from typing import Optional

from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.vectorstores import Chroma

import chainlit as cl

from .llm import embeddings, llm, text_splitter
from .pii import anonymize_text


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

    await cl.Message(
        content="👋 Welcome! Please upload a text file using the file upload button (📎) and attach it to your message to begin asking questions about your document."
    ).send()


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

    chain: Optional[ConversationalRetrievalChain] = cl.user_session.get("chain")
    if not chain:
        await cl.Message(
            content="Please upload a document first using the file upload button (📎 icon). Attach the file to your message to process it."
        ).send()
        return

    sanitized_input = anonymize_text(message.content)
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
