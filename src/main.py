from typing import Optional
from .auth import AuthHandler
from .schemas import AuthDetails
import cloudinary
import cloudinary.uploader
import cloudinary.api
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from dotenv import dotenv_values,find_dotenv


app = FastAPI()

auth_handler = AuthHandler()
config=dotenv_values(find_dotenv())

cluster = MongoClient(config["MONGO_URL"])
db = cluster[config["DATABASE"]]
user_collection = db[config["USERS"]]
image_collection = db[config["IMAGES"]]


cloudinary.config( 
  cloud_name = config["CLOUDNAME"], 
  api_key = config["CLOUDINARYAPI"], 
  api_secret = config["CLOUDINARYAPISECRET"] 
)

@app.post("/register", status_code=201)
def register(auth_details: AuthDetails):
    if user_collection.find_one({"username":auth_details.username}):
        raise HTTPException(status_code=400, detail='Username is already present')
    hashed_password = auth_handler.get_password_hash(auth_details.password)
    user_collection.insert_one(
        {
        'username': auth_details.username,
        'password': hashed_password
    })
    return 

@app.post('/login')
def login(auth_details: AuthDetails):
    user= None
    getUser=user_collection.find_one({"username":auth_details.username})
    if getUser:
        user = getUser
    if (user is None) or (not auth_handler.verify_password(auth_details.password, user['password'])):
        raise HTTPException(status_code=401, detail='Invalid username and/or password')
    
    token = auth_handler.encode_token(str(user['_id']))
    return {'token': token}

@app.get('/unprotected')
def unprotected():
    return {'hello': 'world'}

@app.get('/protected')
def protected(userid=Depends(auth_handler.auth_wrapper)):
    return {'id':userid}

@app.post('/uploadfile')
async def uploadImage(image: UploadFile = File(...),userid=Depends(auth_handler.auth_wrapper)):
    result = cloudinary.uploader.upload(image.file)
    find_user = image_collection.find_one({
        "userId":ObjectId(userid)
    })
    if(find_user):
        print(True)
        find_user['imageURL'].append(result['url'])
        image_collection.save(find_user)
    else:
        image_collection.insert_one({
            'userId':ObjectId(userid),
            'imageURL':[result['url']]
        })
    return {
        'data':result['url']
    }