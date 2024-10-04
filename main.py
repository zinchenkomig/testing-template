import logging

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from starlette.middleware.cors import CORSMiddleware

from src.repo.user import get_user
from src.auth import CurrentUserDep
from src.service.auth import auth_router
from src.service.superuser import superuser_router
from src.service.user import user_router
from src.service.tweets import tweet_router
from src.dependencies import AsyncSessionDep
from starlette_exporter import PrometheusMiddleware, handle_metrics

from conf import settings

app = FastAPI(title=settings.APP_NAME, version='0.1.1')

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(PrometheusMiddleware,
                   group_paths=True,
                   filter_unhandled_paths=True,
                   app_name=settings.APP_NAME)


app.include_router(router=auth_router,
                   prefix='/auth',
                   tags=['auth']
                   )

app.include_router(router=superuser_router,
                   prefix='/superuser',
                   tags=['superuser'])

app.include_router(router=user_router,
                   prefix='/user',
                   tags=['user'])

app.include_router(router=tweet_router,
                   prefix='/tweets',
                   tags=['tweets']
                   )

app.add_route("/metrics", handle_metrics)


@app.get('/ping')
async def ping():
    return 'pong'


@app.get('/test/logs')
async def check_username():
    logging.debug("debug level log")
    logging.info("info level log")
    logging.warning("warn level log")
    logging.error("error level log")


if settings.IS_PROD:
    # Service name is required for most backends
    resource = Resource(attributes={
        SERVICE_NAME: settings.APP_NAME
    })
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.JAEGER_BACKEND, insecure=True))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, excluded_urls=".*/metrics,.*/ping")
