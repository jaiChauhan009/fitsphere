from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from database import get_db
from models import KnowledgeArticle

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/articles")
async def list_articles(
    category: str = Query(None),
    q: str = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(KnowledgeArticle)
    if category:
        query = query.where(KnowledgeArticle.category == category)
    if q:
        query = query.where(
            or_(
                func.lower(KnowledgeArticle.title).contains(q.lower()),
                func.lower(KnowledgeArticle.summary).contains(q.lower()),
            )
        )
    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/articles/{article_id}")
async def get_article(article_id: str, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    result = await db.execute(
        select(KnowledgeArticle).where(KnowledgeArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(404, "Article not found")
    return article


@router.get("/categories")
async def list_categories():
    return [
        {"id": "nutrition", "label": "Nutrition", "icon": "🥗"},
        {"id": "workout", "label": "Workout", "icon": "💪"},
        {"id": "recovery", "label": "Recovery", "icon": "😴"},
        {"id": "mental_health", "label": "Mental Health", "icon": "🧠"},
        {"id": "supplements", "label": "Supplements", "icon": "💊"},
    ]
