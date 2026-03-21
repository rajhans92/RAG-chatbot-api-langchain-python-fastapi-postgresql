from dotenv import load_dotenv
import asyncio
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from datetime import datetime
from langchain.chat_models import init_chat_model
from app.helpers.config import (
    LLM_MODEL,
    SIMILARITY_THRESHOLD
)
from app.helpers.databaseConnection import sessionLocal
from app.controllers.semanticSearchController import (
    embeddedText
)
from app.models.chatModel import (
    ChatMessage,
    ChatSummary,
    ChatSession,
    MemoryEvents
)
load_dotenv()


model = init_chat_model(LLM_MODEL)

async def chatSessionIdCreate(sessionData, userId, db):
    try:
        
        # Store the summary in the database
        chat_session = ChatSession(user_id=userId, title=sessionData.title, model_name=sessionData.modelName)
        db.add(chat_session)

        await db.flush()   # sends INSERT to DB

        sessionId = chat_session.id
        await db.commit()

        return sessionId
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error creating chat session: " + str(e))

async def chatHistoryList(lastNmessages,sessionId, db):
    
    listOfMessageWithRole = []
    try:
        query = (
            select(ChatMessage)
            .filter(ChatMessage.session_id == sessionId)
            .order_by(ChatMessage.message_order.desc())
            .limit(lastNmessages)
        )
        result = await db.execute(query)
        # .scalars() extracts the ChatMessage objects from the result rows
        listOfMessage = result.scalars().all()
        
        for message in listOfMessage:
            listOfMessageWithRole.append({"role": message.role, "content": message.message})

        return listOfMessageWithRole
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching chat history: " + str(e))

async def listofSummariazationMessages(noOfRow, sessionId, db):     
    listofSummariazationMessages = []
    try:

        query = (
            select(ChatSummary)
            .filter( ChatSummary.session_id == sessionId)
            .order_by(ChatSummary.id.desc())
            .limit(noOfRow)
        )
        result = await db.execute(query)
        # .scalars() extracts the ChatMessage objects from the result rows
        summarizationMessage = result.scalars().all()

        for message in summarizationMessage:
            listofSummariazationMessages.append(message.summary_text)

        return listofSummariazationMessages
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching summarized messages: " + str(e))
    
def prepareChatPromptTemplate(queryMessage, listOfMessages, summariazationMessage, sementicSearchResult):
    try:
        promptTemplate = f"""
        You are a helpful assistant. Use the following information to answer the user's question.

        1. Chat History (most recent messages first):
        {listOfMessages}

        2. Summarization of previous conversation:
        {summariazationMessage}

        3. Relevant information from user's documents:
        {sementicSearchResult}

        Now, based on the above information, answer the user's question.

        Question: {queryMessage}
        """

        return promptTemplate
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error preparing chat prompt template: " + str(e))  

async def stream_llm_response(preparedTemplate, userId, sessionId, message, db):
    try:
        full_response = ""

        async for chunk in model.astream(preparedTemplate):

            token = chunk.content if chunk.content else ""
            full_response += token

            yield token

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error during LLM processing: " + str(e))
    
    finally:
        await asyncio.create_task(
            storeHitory(sessionId, message, full_response)
        )

        await asyncio.create_task(
            callMidSummarization(sessionId)
        )

        await asyncio.create_task(
            callMemoryEvents(userId, sessionId)
        )
    
async def storeHitory(sessionId, userMessage, assistantMessage):
    try:
        async with sessionLocal() as db:
            message_order_result = await db.execute(
                select(func.max(ChatMessage.message_order))
                .where(ChatMessage.session_id == sessionId)
            )

            max_order = (message_order_result.scalar() or 0) + 1

            # Store user message
            userChat = [
                ChatMessage(session_id=sessionId, role="user", message=userMessage, tokens_used=len(userMessage.split()), message_order=max_order, is_summarized=0),
                ChatMessage(session_id=sessionId, role="assistant", message=assistantMessage, tokens_used=len(assistantMessage.split()), message_order=(max_order+1), is_summarized=0)
            ]
            db.add_all(userChat)
            await db.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error storing chat history: " + str(e))
    
async def callMidSummarization(sessionId):
    try:
        # Fetch all messages for the session
        async with sessionLocal() as db:
            query = (
                select(ChatMessage)
                .filter( ChatMessage.session_id == sessionId, ChatMessage.is_summarized == 0)
                .order_by(ChatMessage.message_order)
            )
            result = await db.execute(query)
            # .scalars() extracts the ChatMessage objects from the result rows
            messages = result.scalars().all()

            if len(messages) != 0:

                total_tokens = sum(message.tokens_used for message in messages)

                if total_tokens > 3000:
                    message_texts = [msg.message for msg in messages]

                    # Create a summarization prompt
                    summarization_prompt = f"Summarize the following conversation:\n\n{message_texts}"

                    # Get the summary from the LLM
                    summary_response = model.ainvoke(summarization_prompt)
                    summary_text = summary_response.content if summary_response else "No summary available."
                    summary_embedding = embeddedText(summary_text)

                    # Store the summary in the database
                    chat_summary = ChatSummary(session_id=sessionId, summary_text=summary_text, summary_embedding=summary_embedding, message_start_order=messages[0].message_order, message_end_order=messages[-1].message_order, token_count=total_tokens)
                    db.add(chat_summary)
                    await db.commit()

                    db.query(ChatMessage).filter(ChatMessage.session_id == sessionId).update({"is_summarized": 1})
                    await db.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error during mid-conversation summarization: " + str(e))
    

    async def callMemoryEvents(userId, sessionId):
        try:
            async with sessionLocal() as db:

                # 1️⃣ Fetch recent conversation
                query = (
                    select(ChatMessage)
                    .where(ChatMessage.session_id == sessionId)
                    .order_by(ChatMessage.message_order.desc())
                    .limit(10)
                )

                result = await db.execute(query)
                messages = result.scalars().all()

                if not messages:
                    return

                conversation_text = "\n".join(
                    f"{msg.role}: {msg.message}" for msg in messages
                )

                # 2️⃣ LLM extraction (normalized format)
                memory_prompt = f"""
                Extract important long-term user facts.

                Rules:
                - Only extract facts about the user
                - Avoid duplicates
                - Normalize sentences (e.g., "My name is X" → "User name is X")
                - Each fact must be short and atomic
                - Return as plain bullet list

                Conversation:
                {conversation_text}
                """

                response = await model.ainvoke(memory_prompt)
                memory_text = response.content if response else ""

                if not memory_text:
                    return

                # 3️⃣ Parse bullet list
                memories = [
                    line.strip("- ").strip()
                    for line in memory_text.split("\n")
                    if line.strip()
                ]

                for mem in memories:

                    # -------------------------------
                    # 4️⃣ Exact duplicate check
                    # -------------------------------
                    existing_exact = await db.execute(
                        select(MemoryEvents).where(
                            MemoryEvents.user_id == userId,
                            MemoryEvents.text == mem
                        )
                    )

                    if existing_exact.scalars().first():
                        continue  # skip exact duplicate

                    # -------------------------------
                    # 5️⃣ Generate embedding
                    # -------------------------------
                    query_vector = embeddedText(mem)

                    # -------------------------------
                    # 6️⃣ Semantic similarity search (TOP 1)
                    # -------------------------------
                    stmt = (
                        select(MemoryEvents)
                        .where(MemoryEvents.user_id == userId)
                        .order_by(
                            MemoryEvents.text_embedding.cosine_distance(query_vector)
                        )
                        .limit(1)
                    )

                    result = await db.execute(stmt)
                    nearest = result.scalars().first()

                    # -------------------------------
                    # 7️⃣ Semantic dedup / update
                    # -------------------------------
                    if nearest:
                        distance_stmt = (
                            select(
                                MemoryEvents.text_embedding.cosine_distance(query_vector)
                            )
                            .where(MemoryEvents.id == nearest.id)
                        )

                        dist_result = await db.execute(distance_stmt)
                        distance = dist_result.scalar()

                        similarity = 1 - distance if distance is not None else 0

                        if similarity >= SIMILARITY_THRESHOLD:
                            # 🔁 UPDATE existing memory instead of inserting
                            nearest.text = mem
                            nearest.text_embedding = query_vector
                            nearest.updated_at = datetime.utcnow()
                            nearest.importance_score = min(
                                (nearest.importance_score or 5) + 1, 10
                            )
                            continue

                    # -------------------------------
                    # 8️⃣ Insert new memory
                    # -------------------------------
                    new_memory = MemoryEvents(
                        user_id=userId,
                        text=mem,
                        text_embedding=query_vector,
                        importance_score=5,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )

                    db.add(new_memory)

                # 9️⃣ Commit once (important for performance)
                await db.commit()

                print(f"Memory events processed for user {userId}")

        except Exception as e:
            print("Error during memory event creation:", e)