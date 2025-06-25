from fastapi import FastAPI

from src.api.v1.endpoints import auth, registration

base_url_prefix = '/auth'

app = FastAPI(
    title='Auth service',
    description='Service for user authorization',
    docs_url=f'{base_url_prefix}/api/openapi',
    openapi_url=f'{base_url_prefix}/api/openapi.json',
)

base_url_prefix_api = f'{base_url_prefix}/api/v1'

@app.get(f'{base_url_prefix_api}/_healthcheck')
async def healthcheck():
    return {}

app.include_router(auth.router, prefix=f'{base_url_prefix_api}', tags=['auth'])
app.include_router(registration.router, prefix=f'{base_url_prefix_api}', tags=['user'])
