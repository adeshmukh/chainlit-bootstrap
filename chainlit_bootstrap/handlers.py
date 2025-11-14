"""Chainlit event handlers."""

from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.vectorstores import Chroma

import chainlit as cl

from .llm import embeddings, llm, text_splitter
from .pii import anonymize_text


async def _process_file(file: cl.File) -> bool:
    """Process an uploaded file and set up the chain. Returns True if successful."""
    msg = cl.Message(content=f"Processing `{file.name}`...")
    await msg.send()

    # Read file content
    # For now, only text files are supported. PDF support requires additional libraries like pypdf
    try:
        with open(file.path, encoding="utf-8") as f:
            text = f.read()
        if not text or len(text.strip()) == 0:
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

    # Store chain and file name in session
    cl.user_session.set("chain", chain)
    cl.user_session.set("file_name", file.name)

    # Verify it was stored
    stored_chain = cl.user_session.get("chain")
    if not stored_chain:
        await cl.Message(
            content=f"⚠️ Warning: Chain was not properly stored in session. Please try uploading again."
        ).send()
        return False

    return True


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session."""
    # Check if chain already exists (session resume - though chains don't persist across sessions)
    # This is mainly for same-session scenarios
    chain = cl.user_session.get("chain")
    if chain:
        file_name = cl.user_session.get("file_name", "document")
        await cl.Message(
            content=f"👋 Welcome back! You can continue asking questions about `{file_name}`."
        ).send()
        return

    # Show welcome message - files will be handled via spontaneous upload in on_message
    await cl.Message(
        content="👋 Welcome! Please upload a text file using the file upload button (📎) and attach it to your message to begin asking questions about your document."
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages with PII detection and document QA."""
    # Check if message has file attachments (handle spontaneous file uploads)
    # Files can be attached to messages via the file upload button
    if message.elements:
        file_found = False
        for element in message.elements:
            if isinstance(element, cl.File):
                file_found = True
                # Process the uploaded file
                success = await _process_file(element)
                if success:
                    # Verify chain was set
                    chain_check = cl.user_session.get("chain")
                    if chain_check:
                        await cl.Message(
                            content="✅ File processed successfully! You can now ask questions about the document."
                        ).send()
                    else:
                        await cl.Message(
                            content="⚠️ File was processed but chain was not set. Please try uploading again."
                        ).send()
                else:
                    await cl.Message(
                        content="❌ Failed to process the file. Please ensure it's a valid text file and try again."
                    ).send()
                # If there's text content with the file, process it after file is uploaded
                # Otherwise return
                if not message.content or message.content.strip() == "":
                    return

        # If file was found and processed, check if there's also text to process
        if file_found:
            chain = cl.user_session.get("chain")
            if chain and message.content and message.content.strip():
                # Process the question that came with the file
                # Fall through to process the question
                pass
            else:
                return

    # Get chain for processing the question
    chain = cl.user_session.get("chain")  # type: Optional[ConversationalRetrievalChain]

    if not chain:
        await cl.Message(
            content="Please upload a document first using the file upload button (📎 icon). Attach the file to your message to process it."
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
