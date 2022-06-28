from cgitb import reset
import json
import os
import random
import re
from encodings import utf_8
from urllib.parse import urlparse

import bcrypt
import jwt
import uvicorn
import psycopg2
import redis
import yagmail
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse

from config import config
from user import User, loginUser, resetPassword, changePassword, searchForUser

app = FastAPI(openapi_url="/openapi.json")
api_router = APIRouter()

regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

global token

load_dotenv()

r = redis.Redis()

PORT = int(os.environ.get('PORT'))

url = urlparse(os.environ['DATABASE_URL'])
dbname = url.path[1:]
user = url.username
password = url.password
host = url.hostname
port = url.port
conn = psycopg2.connect(
    dbname=dbname,
    user=user,
    password=password,
    host=host,
    port=port
)


def send_reset_password_email(reset_code):
    contents = [
        "Here is your requested code to reset your password",
        "Code: {}".format(reset_code),
        "If you received this email erroneously please ignore it"
    ]
    yag = yagmail.SMTP('jamyersondev@gmail.com',
                       os.environ.get("GMAIL_APP_PASSWORD"))
    yag.send('jamyersondev@gmail.com',
             'Quora Reset Password Request', contents)


def hash_password(password):
    bytePwd = bytes(password, encoding='utf-8')
    hashed_pw = bcrypt.hashpw(bytePwd, bcrypt.gensalt())
    return hashed_pw.decode('utf8')


def validate_user_password(actual_password_hashed, provided_password: str):
    return bcrypt.checkpw(provided_password.encode('utf-8'), actual_password_hashed)


def check_email_valid(email):
    if(re.fullmatch(regex, email)):
        return True
    else:
        return False


def get_decoded_jwt_token(jwt_token):
    return jwt.decode(jwt_token, key=os.environ.get(
        'JWT_KEY'), algorithms=['HS256', ])


@app.get("/")
def test_get():
    return JSONResponse({"Message": "Get passed, connected to endpoint"}, status_code=200)

@app.post("/")
def test_post():
    return JSONResponse({"Message": "Post passed, connected to endpoint"}, status_code=200)

@app.post("/test")
def get_table():
    cur = conn.cursor()
    query = 'insert into users("email", "password", "firstName", "lastName") values(.test., .test., .test., .test.);'.replace(".", "'")
    cur.execute(query)
    conn.commit()
    return JSONResponse({"Message": "Successfully inserted values into table"}, status_code=201)

@app.post("/auth/register/")
def add_user_to_db(userToAdd: User):
    if check_email_valid(userToAdd.email):
        if (len(userToAdd.password) >= 8):
            cur = conn.cursor()
            query = 'INSERT INTO users("email", "firstName", "lastName", "password") VALUES (%s, %s, %s, %s);'
            cur.execute(query, (userToAdd.email, userToAdd.firstName,
                        userToAdd.lastName, hash_password(userToAdd.password)))
            conn.commit()
            print("Records created successfully")

            payload_data = {
                "message": "User added to database successfully",
                "email": userToAdd.email,
                "firstName": userToAdd.firstName,
                "lastName": userToAdd.lastName,
                "password": hash_password(userToAdd.password)
            }

            token = jwt.encode(
                payload=payload_data,
                key=os.environ.get('JWT_KEY')
            )

            print(token)
            return JSONResponse(content=payload_data, status_code=201)

        error_data = {
            "Error": "Enter a valid password that is longer or equal to 8 characters"
        }
        return JSONResponse(error_data, status_code=400)

    error_data = {
        "Error": "Enter a valid email address"
    }
    return JSONResponse(error_data, status_code=400)


@app.post("/auth/login/")
def login_user(userToLogIn: loginUser):
    user_password = None
    cur = conn.cursor()
    try:
        email = "'{}'".format(userToLogIn.email)
        query = "SELECT password FROM users WHERE email = {};".format(
            email)
        cur.execute(query)
        result = cur.fetchall()

        for row in result:
            user_password = row[0]

        if (validate_user_password(bytes(user_password, encoding='utf-8'), userToLogIn.password)):
            payload_data = {
                "email": email,
                "password": user_password
            }

            global token

            token = jwt.encode(
                payload=payload_data,
                key=os.environ.get('JWT_KEY')
            )

            return JSONResponse({"key": token}, status_code=200)

        else:
            error_data = {
                "Error": "Password is incorrect"
            }
            return JSONResponse(error_data, status_code=400)

    except:
        error_data = {
            "Error": "Email address was not found"
        }
        return JSONResponse(error_data, status_code=400)


@app.post("/auth/password")
def change_password(passwordChange: changePassword, r: Request):
    email = ""
    password = ""
    cur = conn.cursor()

    try:
        print(r.headers)
        token = r.headers['authorization'].split(" ")[1]

        if jwt.decode(token, key=os.environ.get('JWT_KEY'), algorithms=['HS256', ]):
            decoded_jwt = jwt.decode(token, key=os.environ.get(
                'JWT_KEY'), algorithms=['HS256', ])
        email = decoded_jwt['email']
        password = decoded_jwt['password']

        if validate_user_password(bytes(password, encoding='utf-8'), passwordChange.old_password):
            print('j')
            new_password = "'{}'".format(
                hash_password(passwordChange.new_password))
            query = "UPDATE public.\"users\" SET password = {} WHERE email = {};".format(
                new_password, email)
            cur.execute(query)
            conn.commit()
            return JSONResponse({"message": "Password successfully changed", "auth": token}, status_code=200)
        else:
            return JSONResponse({"Error": "Old password is incorrect"}, status_code=400)

    except:
        return JSONResponse({"message": "error"}, status_code=400)


@app.post("/auth/password-reset", status_code=200)
def reset_password(token):
    try:
        decoded_jwt = jwt.decode(token, key=os.environ.get(
            'JWT_KEY'), algorithms=['HS256', ])
        email = decoded_jwt['email']
        reset_token = int(
            ''.join(["{}".format(random.randint(0, 9)) for num in range(0, 5)]))
        send_reset_password_email(reset_token)
        key = "password-reset-token-{}".format(email[1: len(email)-1])
        r.set("key", key)
        r.set("reset_token", reset_token)
        message_data = {
            "token": token,
            "Message": "You will receive a reset token on your email that will allow you to reset your password"
        }
        return JSONResponse(message_data, status_code=200)
    except:
        error_data = {
            "Error": "There was an unforseen error that was encountered"}
        return JSONResponse(error_data, status_code=400)


@app.post("/auth/password-reset/confirm")
def confirm_reset_password(resetPasswordData: resetPassword):
    try:
        user_reset_token = int(r.get('reset_token'))
        user_email = str(r.get("key"))
    except:
        error_data = {
            "Error": "No reset token could be found in the database"}
        return JSONResponse(error_data, status_code=400)
    if user_reset_token == int(resetPasswordData.reset_token):
        if (resetPasswordData.email in user_email):
            if (len(resetPasswordData.new_password) >= 8):
                new_password = "'{}'".format(
                    hash_password(resetPasswordData.new_password))
                query = "UPDATE public.\"users\" SET password = {} WHERE email like {};".format(
                    new_password, "'{}'".format(resetPasswordData.email))
                cur = conn.cursor()
                cur.execute(query)
                conn.commit()

                payload_data = {
                    "email": resetPasswordData.email,
                    "reset_token": resetPasswordData.reset_token,
                    "message": "Password has successfully been reset"
                }
                return JSONResponse(payload_data, status_code=201)
            else:
                error_data = {
                    "Error": "Password is not valid, please re-enter a valid password"
                }
                return JSONResponse(error_data, status_code=400)
        else:
            error_data = {
                "Error": "Token does not match the email that was provided"
            }
            return JSONResponse(error_data, status_code=400)
    else:
        error_data = {
            "Error": "The reset password code entered was incorrect or has expired"}
        return JSONResponse(error_data, status_code=400)
    
@app.get("/search/accounts")
def search_for_user(user: searchForUser):
    query = 'select "email", "firstName", "lastName" from users where "email" like {}'.format(user.email)
    user_name, user_surname, user_email = None

    try:
        cur = conn.cursor()
        cur.execute(query)
        results = cur.fetchall()
        for row in results:
            print("row", row[0], "row one")
            user_email = row[0]
            print("row", row[1], "row two")
            user_name = row[1]
            print("row", row[2], "row three")
            user_surname = row[3]
        return JSONResponse({"Email": user_email, "First Name": user_name, "Surname": user_surname}, status_code=201)
    except:
        print("Didn't workkk")
        return JSONResponse({"Error": "Query was not processable"}, status_code=400)




app.include_router(api_router)

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
