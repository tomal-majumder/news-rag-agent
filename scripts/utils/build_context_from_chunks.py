import re

def build_context_from_chunks(chunks, max_chars=1200, min_chunk_length=50):
    context_parts = []
    total_chars = 0

    for i, chunk in enumerate(chunks):
        content = chunk.page_content.strip()
        if len(content) < min_chunk_length:
            continue

        clean = re.sub(r'\s+', ' ', content)
        chunk_len = len(clean)

        if total_chars + chunk_len > max_chars:
            remaining = max_chars - total_chars
            if remaining > 100:
                truncated = clean[:remaining].rsplit(' ', 1)[0]
                context_parts.append(f"[Chunk {i+1}] {truncated}...")
            break
        else:
            context_parts.append(f"[Chunk {i+1}] {clean}")
            total_chars += chunk_len

    final_context = "\n\n".join(context_parts)
    print(f"Final context: {len(final_context)} characters from {len(context_parts)} chunks")
    return final_context