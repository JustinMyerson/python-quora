import psycopg2

from config import config
from fastapi import FastAPI, APIRouter, HTTPException

import bcrypt
import re

from user import User
from user_data import USERS

app = FastAPI(openapi_url="/openapi.json")
api_router = APIRouter()

regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

try:
    # read connection parameters
    params = config()

    # connect to the PostgreSQL server
    print('Connecting to the PostgreSQL database...')
    conn = psycopg2.connect(**params)

    # create a cursor
    cur = conn.cursor()

    # execute a statement
    print('PostgreSQL database version:')
    cur.execute('SELECT version()')

    # display the PostgreSQL database server version
    db_version = cur.fetchone()
    print(db_version)

    # close the communication with the PostgreSQL
    cur.close()
except (Exception, psycopg2.DatabaseError) as error:
    print(error)
    print("ERROR")
finally:
    if conn is not None:
        conn.close()
        print('Database connection closed.')


@app.get("/", status_code=200)
def root():
    return {"message": "Hello User"}


# @api_router.get("/user/{user_email}", status_code=200, response_model=User)
# def fetch_recipe(*, user_email: str):
#     result = [user for user in USERS if user["email"] == user_email]
#     if not result:
#         raise HTTPException(
#             status_code=404, detail=f"User with email: {user_email} not found"
#         )
#     return result[0]

def hash_password(password: str):
    bytePwd = password.encode('utf-8')
    hashed_pw = bcrypt.hashpw(bytePwd, bcrypt.gensalt())
    return hashed_pw


def check_email_valid(email):
    if(re.fullmatch(regex, email)):
        return True
    else:
        return False


@api_router.post("/auth/register/", status_code=201, response_model=User)
def add_user_to_db(email, firstName, lastName, password):
    if check_email_valid(email):
        if (len(password) >= 8):
            conn = psycopg2.connect(**params)
            # create a cursor
            cur = conn.cursor()
            query = 'INSERT INTO users(email, firstName, lastName, password) VALUES (%s, %s, %s, %s)'
            cur.execute(query, (email, firstName,
                        lastName, hash_password(password)))
            conn.commit()
            print("Records created successfully")
            cur.close()
            conn.close()


app.include_router(api_router)

if __name__ == '__main__':
    add_user_to_db('test@gmail.com', 'John', 'Doe', 'Absbsbsbsbsbs')
    print(len(hash_password("Absbsbsbsbsbs")))
