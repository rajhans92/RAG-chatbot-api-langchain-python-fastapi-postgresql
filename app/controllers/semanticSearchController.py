from dotenv import load_dotenv
from fastapi import HTTPException
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from app.helpers.config import EMBADDING_MODEL
from app.models.chatModel import (
    ChatSummary,
    MemoryEvents
)
from app.models.documentModel import (
    DocumentChunks
)
load_dotenv()
print(f"Using embedding model: {EMBADDING_MODEL}")
embeddings = OpenAIEmbeddings(
    model=EMBADDING_MODEL
)

async def sementicSearch(message, sessionId, userId, db, documentId=[]):
    
    try:
        listOfMessage = []
        query_vector = embeddings.embed_query(message)
        stmt = (
            select(MemoryEvents)
            .where(MemoryEvents.user_id == userId)
            .order_by(MemoryEvents.text_embedding.cosine_distance(query_vector))
            .limit(2)
        )

        result = await db.execute(stmt)
        results = result.scalars().all()
        
        for r in results:
            listOfMessage.append(r.text)

        stmt = (
            select(ChatSummary)
            .where(ChatSummary.session_id == sessionId)
            .order_by(ChatSummary.summary_embedding.cosine_distance(query_vector))
            .limit(4)
        )

        result = await db.execute(stmt)
        results = result.scalars().all()
        
        for r in results:
            listOfMessage.append(r.summary_text)

        # If documentId is provided, filter the results based on documentId       
        if documentId: 
            stmt = (
                select(DocumentChunks)
                .where(DocumentChunks.document_id.in_(documentId))
                .order_by(DocumentChunks.chunk_embedding.cosine_distance(query_vector))
                .limit(4)
            )

            result = await db.execute(stmt)
            results = result.scalars().all()
            for r in results:
                listOfMessage.append(r.chunk_text)

        return listOfMessage
    except Exception as e:
        print(f"Error during semantic search: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred during semantic search.")
                
    
def embeddedText(text):
    try:
        return embeddings.embed_query(text)
    except Exception as e:
        print(f"Error during text embedding: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred during text embedding.")