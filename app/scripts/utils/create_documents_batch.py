def create_documents_batch(batch_df, text_splitter):
    """Create documents from a batch of articles"""
    documents = []

    for idx, row in batch_df.iterrows():
        # Create full text
        title = str(row['title']) if 'title' in row and str(row['title']) != 'nan' else "Untitled"
        content = str(row['article']) if 'article' in row and str(row['article']) != 'nan' else ""

        if not content.strip():
            continue

        full_text = f"{content}"

        # Split into chunks
        chunks = text_splitter.split_text(full_text)

        # Create documents
        for i, chunk in enumerate(chunks):
            metadata = {
                'title': title,
                'date': str(row.get('date', 'Unknown')),
                'url': str(row.get('url', '')),
                'article_id': str(idx),
                'chunk_num': i
            }

            documents.append({
                'content': chunk,
                'metadata': metadata,
                'id': f"doc_{idx}_{i}"
            })

    return documents