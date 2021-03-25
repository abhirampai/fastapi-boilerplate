from typing import Optional
from .auth import AuthHandler
from .schemas import AuthDetails
import pymongo
from pymongo import MongoClient
from fastapi import FastAPI, Depends, HTTPException
from dotenv import dotenv_values,find_dotenv


app = FastAPI()

auth_handler = AuthHandler()
config=dotenv_values(find_dotenv())
cluster = MongoClient(config["MONGO_URL"])
db = cluster[config["DATABASE"]]
collection = db[config["USERS"]]

@app.post("/register", status_code=201)
def register(auth_details: AuthDetails):
    print(collection.find_one({"username":auth_details.username}))
    if collection.find_one({"username":auth_details.username}):
        raise HTTPException(status_code=400, detail='Username is already present')
    hashed_password = auth_handler.get_password_hash(auth_details.password)
    collection.insert_one(
        {
        'username': auth_details.username,
        'password': hashed_password
    })
    return 

@app.post('/login')
def login(auth_details: AuthDetails):
    user= None
    getUser=collection.find_one({"username":auth_details.username})
    if getUser:
        user = getUser
    if (user is None) or (not auth_handler.verify_password(auth_details.password, user['password'])):
        raise HTTPException(status_code=401, detail='Invalid username and/or password')
    
    token = auth_handler.encode_token(user['username'])
    return {'token': token}

@app.get('/unprotected')
def unprotected():
    return {'hello': 'world'}

@app.get('/protected')
def protected(username=Depends(auth_handler.auth_wrapper)):
    return {'name':username}