from fastapi import FastAPI
from .api.routes import user_routes,profile_routes,user_input_data_routes,forgetpasswordroutes,contact_routes,auth_routes
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from .api.config.config import SESSION_SECRET_KEY
import uvicorn
import os
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000","http://localhost:3000","http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)


app.include_router(user_routes.router)
app.include_router(profile_routes.router)
app.include_router(user_input_data_routes.router)
app.include_router(forgetpasswordroutes.router)
app.include_router(contact_routes.router)
app.include_router(auth_routes.router)




@app.get('/',tags=['main'])
def checkMain():
    return("server chalu hai")


if __name__ == "__main_":
    port = int(os.environ.get("PORT",8000))
    uvicorn.run("app.main:app",host="0.0.0.0",port=port)