from fastapi import Header, HTTPException
from app.schema.chatbotSchema import (HeaderDetail, HeaderDetailOnlyUser)

def get_header_with_session_details(header: HeaderDetail =  Header(...)):     
    try:
        sessionId = header.sessionId
        userId = header.userId
        return {"sessionId": sessionId, "userId": userId}
    except Exception as e:
        raise HTTPException(status_code=403, detail="Invalid User Session")
    
def get_header_without_session_details(header: HeaderDetailOnlyUser =  Header(...)):     
    try:
        userId = header.userId
        return {"userId": userId}
    except Exception as e:
        raise HTTPException(status_code=403, detail="Invalid User Session")