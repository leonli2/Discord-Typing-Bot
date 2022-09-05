import time
import discord
import wikipedia
import nltk
import pymongo
import matplotlib
import matplotlib.pyplot as plt
from difflib import SequenceMatcher
import pandas
from pandas_datareader import data as pdr
import numpy as np
from datetime import date
from newspaper import Article
from GoogleNews import GoogleNews

from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents = intents)

async def check_user_exists (topic, collection):
    if collection.find_one({"name": topic}) == None:
        return False
    else:
        return True

def initialize_graph():
    # clear the graph before creating one
    plt.clf()

    plt.xlabel('Last Attempts')
    plt.ylabel('WPM') 
    # plt.legend() 

    x_axis = []
    y_axis = []
    x_axis = [0 for i in range(7)] 
    y_axis = [0 for i in range(7)]

    return x_axis, y_axis

def set_x_y_values(x_axis, y_axis, document, count):
    x_axis[count] = count + 1
    y_axis[count] = document["wpm"]

def create_graph (x_axis, y_axis):
    # plot the graph and store it in a variable
    plt.plot(x_axis, y_axis)
    file_name = 'output.png'
    plt.savefig(file_name)
    return file_name

def get_news (topic):
    news = GoogleNews(period='1d')
    news.search(topic)
    news_result = news.result()
    return news_result

def get_article_text (article):
    article.parse()
    nltk.download('punkt')
    article.nlp()
    return article.summary[:250]

def get_wiki_text (topic, sentence_length):
    try:
        text = wikipedia.summary(topic, sentences = sentence_length)
        return text, True
    except:
        try:
            topic = wikipedia.search(topic) [0]
            text = wikipedia.summary(topic, sentences = sentence_length)
            return text, True
        except:
            try:
                topic = wikipedia.suggest(topic)
                text = wikipedia.summary(topic, sentences = sentence_length)
                return text, True
            except:
                return "", False

def find_wpm_and_time (end_time, start_time, user_text):
    # wpm = number of words typed / time taken in seconds ) * 60
    total_time = round (end_time - start_time, 2)
    total_message_words = len((user_text).split())
    wpm = int (round((total_message_words / total_time) * 60))
    return wpm, total_time

def find_accuracy(text, user_text):
    return int (round (SequenceMatcher(None, text, user_text).ratio() * 100, 2)) 

def create_type_data (user_id, wpm, accuracy):
    new_data = {
            "name": str(user_id),
            "wpm": wpm,
            "accuracy": accuracy,
            "date": str(date.today())
        }
    return new_data

def create_profile_data (user_id):
    new_data = {
                "name":  str(user_id),
                "wpm": 0,
                "best_race": 0,
                "races": 0
            }
    return new_data