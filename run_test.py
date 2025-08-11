from app.scripts.Main.answer import answer_question
from app.scripts.Main.answer import answer_question_stream

def main():
    print("Running vector store test...")
    # result, time = answer_question("What is the news on USA election?")
    result = answer_question("Has Donald Trump been taken COVID seriously?")
    # result, time = answer_question("What is the news on USA election?", stream=True)
    print(result)

if __name__ == "__main__": 
    main()