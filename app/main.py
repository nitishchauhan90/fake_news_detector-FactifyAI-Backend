from fastapi import FastAPI
from .api.routes import user_routes,profile_routes,user_input_data_routes,forgetpasswordroutes,contact_routes
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000","http://localhost:3000","http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_routes.router)
app.include_router(profile_routes.router)
app.include_router(user_input_data_routes.router)
app.include_router(forgetpasswordroutes.router)
app.include_router(contact_routes.router)





@app.get('/',tags=['main'])
def checkMain():
    return("server chalu hai")


