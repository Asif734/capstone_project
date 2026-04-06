from fastapi import FastAPI,APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from app.utils.preprocess_text import extract_text, clean_text, chunk_text
from app.services.embedding import get_embedding
from app.services.pinecone import store_embeddings
import uuid

router= APIRouter()

@router.post("/Upload")
async def upload_file(
    file: UploadFile= File(...),
    doc_name: str = Form(None)
    ):
    try:
        if doc_name:
            doc_id = doc_name
        else:
            doc_id= str(uuid.uuid4())

        file_bytes= await file.read()
        text= extract_text(file_bytes, file.filename)
        filename= file.filename

        cleaned_text= clean_text(text)

        chunked_text= chunk_text(cleaned_text)

        embeddings= get_embedding(chunked_text)

        chunk_stored = store_embeddings(
            chunks= chunked_text,
            embeddings= embeddings,
            doc_id= doc_id
        )

        return{
            "filename" : filename,
            "chunk_stored": len(chunked_text),
            "message": "Document uploaded and stored successfully"
        }

        
    
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code= 400)