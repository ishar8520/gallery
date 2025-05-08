from fastapi import APIRouter

router = APIRouter()

@router.get(
    '/get_photo'
)
async def get_photo():
    return {'get_photo': 'success'} 