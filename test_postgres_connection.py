import os
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Either load from environment variable or paste directly
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://<username>:<password>@<endpoint>:5432/newsrag"
)

print(f"Using DATABASE_URL: {DATABASE_URL}")
# Create engine
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # 1. Create extension if not exists
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

    # 2. Create a test table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS test_vectors (
            id SERIAL PRIMARY KEY,
            content TEXT,
            embedding vector(3)
        );
    """))

    # 3. Clear any old data
    conn.execute(text("DELETE FROM test_vectors;"))

    # 4. Insert some rows
    conn.execute(text("""
        INSERT INTO test_vectors (content, embedding)
        VALUES
        ('cat', '[1, 0, 0]'),
        ('dog', '[0.9, 0.1, 0]'),
        ('banana', '[0, 1, 0]');
    """))

    # 5. Run similarity search
    result = conn.execute(text("""
        SELECT content, embedding <-> '[1, 0, 0]' AS distance
        FROM test_vectors
        ORDER BY distance ASC
        LIMIT 3;
    """))

    # Print results
    print("Similarity search results:")
    for row in result:
        print(f"{row.content} -> distance: {row.distance}")

    # Optional: Drop the test table
    # conn.execute(text("DROP TABLE test_vectors;"))

    conn.commit()
