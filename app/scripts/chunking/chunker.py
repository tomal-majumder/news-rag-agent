from langchain.text_splitter import RecursiveCharacterTextSplitter

def chunk_article_text(text: str, chunk_size=2500, overlap=600):
    """
    Spaces, punctuation, and newlines are counted toward chunk_size/overlap.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
    )
    return splitter.split_text(text)