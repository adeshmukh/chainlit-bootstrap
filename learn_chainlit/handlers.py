"""Chainlit event handlers."""

from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.vectorstores import Chroma

import chainlit as cl

from .llm import embeddings, llm, text_splitter
from .pii import anonymize_text


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session and handle document upload."""
    files = None

    # Wait for the user to upload a file
    while files is None:
        files = await cl.AskFileMessage(
            content="Please upload a text file to begin!",
            accept=["text/plain", "application/pdf"],
            max_size_mb=20,
            timeout=180,
        ).send()

    file = files[0]

    msg = cl.Message(content=f"Processing `{file.name}`...")
    await msg.send()

    # Read file content
    # For now, only text files are supported. PDF support requires additional libraries like pypdf
    try:
        with open(file.path, encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        await cl.Message(
            content=f"Error: Could not read file `{file.name}`. Please ensure it's a text file."
        ).send()
        return

    # Split the text into chunks
    texts = text_splitter.split_text(text)

    # Create a metadata for each chunk
    metadatas = [{"source": f"{i}-pl"} for i in range(len(texts))]

    # Create a Chroma vector store
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

    # Create a chain that uses the Chroma vector store
    chain = ConversationalRetrievalChain.from_llm(
        llm,
        chain_type="stuff",
        retriever=docsearch.as_retriever(),
        memory=memory,
        return_source_documents=True,
    )

    # Let the user know that the system is ready
    msg.content = f"Processing `{file.name}` done. You can now ask questions!"
    await msg.update()

    cl.user_session.set("chain", chain)
    cl.user_session.set("file_name", file.name)


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages with PII detection and document QA."""
    chain = cl.user_session.get("chain")  # type: Optional[ConversationalRetrievalChain]

    if not chain:
        await cl.Message(
            content="Please upload a document first using the file upload button."
        ).send()
        return

    # Anonymize user input for PII detection
    sanitized_input = anonymize_text(message.content)

    # Create callback handler for streaming
    cb = cl.AsyncLangchainCallbackHandler()

    # Run the chain
    res = await chain.acall(sanitized_input, callbacks=[cb])
    answer = res["answer"]
    source_documents = res["source_documents"]

    # Anonymize the answer as well
    sanitized_answer = anonymize_text(answer)

    text_elements = []  # type: list[cl.Text]

    if source_documents:
        for source_idx, source_doc in enumerate(source_documents):
            source_name = f"source_{source_idx}"
            # Create the text element referenced in the message
            text_elements.append(
                cl.Text(
                    content=source_doc.page_content, name=source_name, display="side"
                )
            )
        source_names = [text_el.name for text_el in text_elements]

        if source_names:
            sanitized_answer += f"\nSources: {', '.join(source_names)}"
        else:
            sanitized_answer += "\nNo sources found"

    await cl.Message(content=sanitized_answer, elements=text_elements).send()


@cl.on_audio_chunk
async def on_audio_chunk(audio_chunk):
    """Handle real-time audio chunks for voice input."""
    # TODO: Implement OpenAI Realtime API integration
    # For now, this is a placeholder that acknowledges audio input
    if hasattr(audio_chunk, "isStart") and audio_chunk.isStart:
        await cl.Message(content="🎤 Listening...").send()
    elif hasattr(audio_chunk, "isEnd") and audio_chunk.isEnd:
        # In a full implementation, you would:
        # 1. Send accumulated audio to OpenAI Realtime API
        # 2. Get transcription and response
        # 3. Stream the response back
        await cl.Message(
            content="Voice input received. Full OpenAI Realtime API integration coming soon!"
        ).send()
