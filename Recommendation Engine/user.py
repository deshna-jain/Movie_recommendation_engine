import os
import requests

from flask import Flask, session, render_template
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import pandas as pd

app = Flask(__name__)
os.environ["DATABASE_URL"]='postgres://tgtnhaxxgotxjd:3a1e74426c6814e12e485bb992398a737e13eed72093b28cb53233a022f72b25@ec2-174-129-242-183.compute-1.amazonaws.com:5432/d6g54ari3aolfo'
# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

query="create table use (username VARCHAR(30) NOT NULL ,password VARCHAR(50) NOT NULL,fullname VARCHAR(30), PRIMARY KEY(username))"
db.execute(query)
db.commit()
