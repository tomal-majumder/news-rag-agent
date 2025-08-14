from app.scripts.Main.answer import answer_question
from app.scripts.Main.answer import answer_question_stream
from app.scripts.utils.get_embedding_model import get_embedding_model

def main():
   model = get_embedding_model()
   

if __name__ == "__main__": 
    main()