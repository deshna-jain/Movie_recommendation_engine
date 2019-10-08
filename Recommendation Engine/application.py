import time
import gc
import argparse

# data science imports
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors

# utils import
from fuzzywuzzy import fuzz


from rake_nltk import Rake
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer

import os
import requests

from flask import Flask, session, render_template, request
from flask_session import Session

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


def recommendations(title):
    recommended_movies = []
    idx1 = indices[indices == title[0]].index[0]
    temp=count_matrix[idx1]
    for i in range(1,len(title)):
        idx = indices[indices == title[i]].index[0]
        temp+=count_matrix[idx]
    cosine_sim=cosine_similarity(temp,count_matrix)
    score_series = pd.Series(list(cosine_sim.reshape(250,))).sort_values(ascending = False)

    top_10_indexes = list(score_series.iloc[:10+len(title)].index)
    print(top_10_indexes)
    # populating the list with the titles of the best 10 matching movies
    i=0
    #print("bhaih")
    while(i < 10+len(title)):
        if indices[top_10_indexes[i]] not in title:
            recommended_movies.append(indices[top_10_indexes[i]])
        i+=1
    

    return recommended_movies


df = pd.read_csv('https://query.data.world/s/uikepcpffyo2nhig52xxeevdialfl7')

t=df[['Title','imdbRating']]
df = df[['Title','Genre','Director','Actors','Plot']]

df['Actors'] = df['Actors'].map(lambda x: x.split(',')[:3])

df['Genre'] = df['Genre'].map(lambda x: x.lower().split(','))

df['Director'] = df['Director'].map(lambda x: x.split(' '))
#print(df)
for index, row in df.iterrows():
    row['Actors'] = [x.lower().replace(' ','') for x in row['Actors']]
    row['Director'] = ''.join(row['Director']).lower()


#print(t)
t=t.sort_values(by="imdbRating", ascending=False)
#print(t.head())

df['Key_words'] = ""

for index, row in df.iterrows():
    plot = row['Plot']
    r = Rake()
    r.extract_keywords_from_text(plot)
    key_words_dict_scores = r.get_word_degrees()
    row['Key_words'] = list(key_words_dict_scores.keys())

# dropping the Plot column
df.drop(columns = ['Plot'], inplace = True)

df.set_index('Title', inplace = True)
df['bag_of_words'] = ''
columns = df.columns
for index,row in df.iterrows():
    words = ''
    for col in columns:
        s=""
        #print(row,col)
        if col != 'Director':
            words = words + ' '.join(row[col])+ ' '
            #print(s.join(row[col]))
        else:
            words = words + row[col]+ ' '
            #print(words)
    row['bag_of_words'] = words

df.drop(columns = [col for col in df.columns if col!= 'bag_of_words'], inplace = True)



count = CountVectorizer()
count_matrix = count.fit_transform(df['bag_of_words'])

indices = pd.Series(df.index)
indices[:5]

#cosine_sim = cosine_similarity(count_matrix, count_matrix)




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
@app.route("/")
def index():
    #return "Project 1: TODO"
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "cG46cghUhz8fZwTxDxiwVQ", "isbns": "9781632168146"})
    return res.json()
@app.route("/Registration",methods=['GET','POST'])
def Registration():
    
    return render_template('Registration.html')
@app.route("/Login",methods=['GET','POST'])
def Login():
    #return request.method
    if request.method == 'POST':
        username=request.form['username']
        
        fullname=request.form['fullname']
        password=request.form['psw']
        query="INSERT INTO use (username, password, fullname) VALUES (:username,:password,:fullname)"
        #insert=(username, password, fullname)
        db.execute(query, {'username':username,'password':password,'fullname':fullname})
        db.commit()
    return render_template('Login.html')
@app.route("/Home",methods=['POST'])
def Home():
    username=request.form['username']
    password=request.form['psw']
    session['username'] = username
    query="SELECT username FROM use WHERE username=:username AND password=:password"
    user=db.execute(query, {'username':username, 'password':password}).fetchall()
    if (len(user)==0):
        return render_template('Login.html')
    else:
        return render_template('Home.html',username=username)
@app.route("/ShowRating",methods=['POST'])
def ShowRating():
    #return request.method
    movie=request.form['search']
    naam=session['username']
    
    query="INSERT INTO moti(naam,movie) VALUES (:naam,:movie)"
    
    db.execute(query, {'naam':naam,'movie':movie})
    db.commit()
    #creating dictionary
    query2="SELECT movie FROM moti WHERE naam = :naam"
    history=db.execute(query2,{'naam':naam}).fetchall()
    #naam="stunner"
    his=[]
    for i in range(len(history)):
        his+=[history[i][0]]
    #print(his)
    his=list(set(his))
    if len(his) > 1:
        list_of_recommended_movies=recommendations(his)
        return render_template('Recomm.html',list_of_recommended_movies=list_of_recommended_movies)
    else:
        return render_template('Recomm.html',list_of_recommended_movies=t['Title'].head(10).tolist())
    
if(__name__=="__main__"):
    app.run(debug=True,use_reloader=False)
