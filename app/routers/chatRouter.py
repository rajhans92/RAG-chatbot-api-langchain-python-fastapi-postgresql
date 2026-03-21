from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from uuid import uuid4
import asyncio
from typeing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.helpers.databaseConnection import get_db
from app.schemas.chatSchema import (HeaderDetail,SessionRequest, HeaderDetailOnlyUser)
from app.helpers.config import (
    LAST_N_MESSAGES,
    NO_OF_ROW_SUMMARY,
    ALLOWED_TYPES,
    MAX_FILE_SIZE
)
from app.helpers.helper import (
    get_header_without_session_details, 
    get_header_with_session_details
    )
from app.controllers.chatController import (
    chatHistoryList,
    listofSummariazationMessages,
    prepareChatPromptTemplate,
    stream_llm_response,
    chatSessionIdCreate
)
from app.controllers.semanticSearchController import (
    sementicSearch
)
from app.controllers.fileUploaderController import (
    s3_service
)


router = APIRouter(prefix="/chatbot", tags=["chatbot"])

@router.post("/new-session")
async def new_chat_session(sessionData: SessionRequest, getHeaderDetail:HeaderDetailOnlyUser = Depends(get_header_without_session_details), db: AsyncSession = Depends(get_db)):
    userId = getHeaderDetail["userId"]

    sessionId = await chatSessionIdCreate(sessionData,getHeaderDetail["userId"], db)

    return {
        "status": "success",
        "message": f"New chat session started with sessionId: {sessionId} for userId: {userId}",
        "response": {
            sessionId: sessionId
        }
    }

@router.post("/")
async def chatbot(message: str, getHeaderDetail: HeaderDetail = Depends(get_header_with_session_details), db: AsyncSession = Depends(get_db)):
    last_n_messages = LAST_N_MESSAGES
    noOfRow = NO_OF_ROW_SUMMARY
    listofMessages, summariazationMessage, sementicSearchResult = await asyncio.gather(
        chatHistoryList(last_n_messages, getHeaderDetail["sessionId"], db),
        listofSummariazationMessages(noOfRow, getHeaderDetail["sessionId"], db),
        sementicSearch(message, getHeaderDetail["sessionId"], getHeaderDetail["userId"], db)
    )

    preparedTemplate = prepareChatPromptTemplate(message,listofMessages, summariazationMessage, sementicSearchResult) 

    # Server-Sent Events (SSE)
    return StreamingResponse(
        stream_llm_response(preparedTemplate, getHeaderDetail["userId"], getHeaderDetail["sessionId"], message, db),
        media_type="text/event-stream"
    )

@router.post("/file-upload")
async def file_upload(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...),getHeaderDetail: HeaderDetail = Depends(get_header_with_session_details), db: AsyncSession = Depends(get_db)):
    uploaded_filenames = []
    error_files = []
    
    for file in files:
        if file.content_type not in ALLOWED_TYPES:
            error_files.append({"file": file.filename, "error": "Invalid file type"})
            continue

        if file.size > MAX_FILE_SIZE:
            error_files.append({"file": file.filename, "error": "File is too large"})
            continue

        fileName = uuid4() + "_" + file.filename
        s3_url = s3_service.upload_file(file.file, fileName, file.content_type, getHeaderDetail["userId"], getHeaderDetail["sessionId"], db)

        if not s3_url:
            error_files.append({"file": file.filename, "error": "File Upload failed"})
            continue

        uploaded_filenames.append({"file": file.filename, "status": "Uploaded", "s3_url": s3_url})  

    return {
        "status": "success",
        "message": "File upload endpoint is under construction.",
        "response": {
            "uploaded_files": uploaded_filenames,
            "error_files": error_files
        }
    }
