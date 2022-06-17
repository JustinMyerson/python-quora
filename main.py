import psycopg2
from config import config
from fastapi import FastAPI, APIRouter, HTTPException

from user import User
from user_data import USERS

app = FastAPI(openapi_url="/openapi.json")
api_router = APIRouter()


# @app.get("/", status_code=200)
# def root():
#     return {"message": "Hello User"}


# @api_router.get("/user/{user_email}", status_code=200, response_model=User)
# def fetch_recipe(*, user_email: str):
#     result = [user for user in USERS if user["email"] == user_email]
#     if not result:
#         raise HTTPException(
#             status_code=404, detail=f"User with email: {user_email} not found"
#         )
#     return result[0]


# @api_router.post("/auth/register/", status_code=201, response_model=User)
# def register_user(*, userCreated: User) -> dict:
#     user_entry = User(
#         email=userCreated.email,
#         firstName=userCreated.firstName,
#         lastName=userCreated.lastName,
#         password=userCreated.password,
#     )
#     USERS.append(user_entry.dict())
#     print(USERS)

#     return user_entry


def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
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


app.include_router(api_router)

if __name__ == '__main__':
    connect()
