from pydantic import BaseModel

class RequestPhotoDownload(BaseModel):
    bucket_name: str = 'testbucket'
    object_name: str = 'TestPhoto.jpeg'
    file_path: str = '/home/v/Pictures/Screenshots/123.jpeg'

class RequestPhotoUpload(BaseModel):
    title: str

class ResponsePhotoDownload(BaseModel):
    status: str

class ResponsePhotoUpload(BaseModel):
    pass