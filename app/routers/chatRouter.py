from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
import uuid
import asyncio
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.helpers.databaseConnection import get_db
from app.schemas.chatSchema import (HeaderDetail,SessionRequest, HeaderDetailOnlyUser, MessageRequest)
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
    normal_llm_response,
    chatSessionIdCreate,
    getFileList
)
from app.controllers.semanticSearchController import (
    sementicSearch
)
from app.controllers.fileUploaderController import (
    s3Service,
    storeFiledetails
)
from worker.listener import worker

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
async def chatbot(requestBody: MessageRequest, getHeaderDetail: HeaderDetail = Depends(get_header_with_session_details), db: AsyncSession = Depends(get_db)):
    last_n_messages = LAST_N_MESSAGES
    noOfRow = NO_OF_ROW_SUMMARY
    listofMessages, summariazationMessage, sementicSearchResult = await asyncio.gather(
        chatHistoryList(last_n_messages, getHeaderDetail["sessionId"], db),
        listofSummariazationMessages(noOfRow, getHeaderDetail["sessionId"], db),
        sementicSearch(requestBody.message,getHeaderDetail["sessionId"], getHeaderDetail["userId"], db, requestBody.documentId)
    )

    preparedTemplate = prepareChatPromptTemplate(requestBody.message,listofMessages, summariazationMessage, sementicSearchResult) 

    # Server-Sent Events (SSE)
    return StreamingResponse(
        stream_llm_response(preparedTemplate, getHeaderDetail["userId"], getHeaderDetail["sessionId"], requestBody.message, db),
        media_type="text/event-stream"
    )

@router.post("/evaluation")
async def chatbot(
    requestBody: MessageRequest,
    getHeaderDetail: HeaderDetail = Depends(
        get_header_with_session_details
    ),
    db: AsyncSession = Depends(get_db)
):
    last_n_messages = LAST_N_MESSAGES
    noOfRow = NO_OF_ROW_SUMMARY

    sessionId = getHeaderDetail["sessionId"]
    userId = getHeaderDetail["userId"]

    # Step 1: Fetch chat history
    listofMessages = await chatHistoryList(
        last_n_messages,
        sessionId,
        db
    )

    # Step 2: Fetch summarization messages
    summariazationMessage = await listofSummariazationMessages(
        noOfRow,
        sessionId,
        db
    )

    # Step 3: Perform semantic search
    sementicSearchResult = await sementicSearch(
        requestBody.message,
        sessionId,
        userId,
        db,
        requestBody.documentId
    )
    # Step 4: Prepare prompt
    preparedTemplate = prepareChatPromptTemplate(
        requestBody.message,
        listofMessages,
        summariazationMessage,
        sementicSearchResult
    )

    # Step 5: Generate LLM response
    response = normal_llm_response(
        preparedTemplate,
        userId,
        sessionId,
        requestBody.message,
        db
    )

    return {
        "status": "success",
        "message": "Chatbot evaluation response",
        "answer": response,
        "chat_history": listofMessages,
        "summarization": summariazationMessage,
        "contexts": sementicSearchResult
    }


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

        fileName = str(uuid.uuid4()) + "_" + file.filename
        s3_url = s3Service.upload_file(file.file, fileName, file.content_type, getHeaderDetail["userId"], getHeaderDetail["sessionId"])

        if not s3_url:
            error_files.append({"file": file.filename, "error": "File Upload failed"})
            continue

        fileId = await storeFiledetails(file.filename, fileName,s3_url, file.content_type, getHeaderDetail["userId"], getHeaderDetail["sessionId"], db)
        if not fileId:
            error_files.append({"file": file.filename, "error": "failed while storing file"})
            #delete file from s3 if db entry fails to maintain consistency
            continue
        uploaded_filenames.append({"id":fileId,"file": file.filename, "status": "Uploaded", "s3_url": s3_url, "file_type":file.content_type})  

    background_tasks.add_task(worker, uploaded_filenames)  # Process files in the background

    return {
        "status": "success",
        "message": "File upload endpoint is under construction.",
        "response": {
            "uploaded_files": uploaded_filenames,
            "error_files": error_files
        }
    }

@router.get("/files")
async def list_uploaded_files(getHeaderDetail: HeaderDetail = Depends(get_header_with_session_details), db: AsyncSession = Depends(get_db)):
    userId = getHeaderDetail["userId"]
    sessionId = getHeaderDetail["sessionId"]

    # Fetch files from the database based on userId and sessionId
    files = await getFileList(userId, sessionId, db)

    return {
        "status": "success",
        "message": "List of uploaded files",
        "response": files
    }
