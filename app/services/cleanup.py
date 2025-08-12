from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.scripts.utils.get_vector_store import get_vector_store

def prune_old_content(db: Session, max_articles=500, max_days=90):
    """
    - Delete articles older than max_days
    - Keep only latest max_articles by published_at
    - Remove matching vectors from PGVector by metadata.article_id
    """
    vs = get_vector_store()
    cutoff = datetime.utcnow() - timedelta(days=max_days)

    # time-based
    old_ids = db.execute(text("""
        SELECT id FROM news_articles
        WHERE published_at IS NOT NULL AND published_at < :cutoff
    """), {"cutoff": cutoff}).scalars().all()

    # count-based cap (global; change to per-topic if you prefer)
    over_cap_ids = db.execute(text("""
        WITH ranked AS (
          SELECT id, ROW_NUMBER() OVER (ORDER BY published_at DESC NULLS LAST) rn
          FROM news_articles
        )
        SELECT id FROM ranked WHERE rn > :cap
    """), {"cap": max_articles}).scalars().all()

    ids = list(set(old_ids) | set(over_cap_ids))
    if not ids:
        return {"deleted_articles": 0, "deleted_vectors": 0}

    # delete from articles table
    db.execute(text("DELETE FROM news_articles WHERE id = ANY(:ids)"), {"ids": ids})
    db.commit()

    # delete vectors by metadata filter
    deleted_vecs = 0
    for aid in ids:
        vs.delete(where={"article_id": str(aid)})  # fresh vs each loop is fine
        deleted_vecs += 1

    return {"deleted_articles": len(ids), "deleted_vectors": deleted_vecs}
