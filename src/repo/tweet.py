from typing import List

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from src import db_models
from src import json_schemes


async def get_tweets(async_session: AsyncSession, page: int, limit: int) -> List[db_models.Tweet]:
    query = select(db_models.Tweet).options(joinedload(db_models.Tweet.created_by)) \
        .filter_by(is_deleted=False).order_by(db_models.Tweet.created_at.desc())
    if page is not None and limit is not None:
        query = query.limit(limit).offset((page - 1) * limit)
    tweets_resp = await async_session.execute(query)
    tweets = list(tweets_resp.scalars().unique().all())
    return tweets


async def new_tweet(async_session: AsyncSession, creator, tweet_create: json_schemes.CreateTweet):
    tweet = db_models.Tweet(
        message=tweet_create.message,
        created_by_guid=creator.guid,
    )
    async_session.add(tweet)
    await async_session.commit()
