 # app/main.py

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from app.schemas import QuestionRequest
from scripts.Main.answer import answer_question, answer_question_stream
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend's domain like "http://localhost:3000"
    allow_credentials=True,
    allow_methods=["*"],  # ["POST"] if you want to restrict it
    allow_headers=["*"],
)

@app.post("/ask")
async def ask_question(req: QuestionRequest):
    result = answer_question(req.question)
    return result

@app.post("/ask-stream")
async def ask_question_stream(req: QuestionRequest):
    return StreamingResponse(answer_question_stream(req.question), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
