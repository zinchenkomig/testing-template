from fastapi import APIRouter
from typing import List

from src.dependencies import AsyncSessionDep
from src import json_schemes
import src.repo.tweet as tweet_repo
from src.auth import CurrentUserDep

tweet_router = APIRouter()


@tweet_router.get('')
async def get_tweets(async_session: AsyncSessionDep,
                     page: int = 1, limit: int = 20) -> List[json_schemes.Tweet]:
    return await tweet_repo.get_tweets(async_session, page=page, limit=limit)


@tweet_router.post('/new')
async def new_tweet(async_session: AsyncSessionDep, creator: CurrentUserDep, tweet: json_schemes.CreateTweet):
    return await tweet_repo.new_tweet(async_session, creator, tweet)
