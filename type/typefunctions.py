import time
import discord
import wikipedia
import nltk
import pymongo
import matplotlib.pyplot as plt
from difflib import SequenceMatcher
from datetime import date
from newspaper import Article
from GoogleNews import GoogleNews
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents = intents)

async def check_user_exists (topic, db, database_type):
    collection = db[database_type]

    if await collection.find_one({"name": topic}) == None:
        return False
    else:
        return True

async def send_profile_message(ctx, db, topic):
    collection = db["profile"]
    user_data = collection.find({"name": topic}).sort(topic)
    document = await user_data.to_list(length=1)

    await ctx.send("Name: " + document[0]["name"] + " | " + "Avg WPM: " + str (document[0]["wpm"])
    + " | " + "Best Race: " + str(document[0]["best_race"]) + " | " + "Races Completed: "
    + str(document[0]["races"]))
    return

async def send_recent_message(ctx, db, topic):
    collection = db["typing"]
    user_data = collection.find({"name": topic}).sort("_id", pymongo.DESCENDING)
    document = await user_data.to_list(length=1)

    await ctx.send("Name: " + document[0]["name"] + " | " + "WPM: " + str (document[0]["wpm"])
    + " | " + "Accuracy: " + str(document[0]["accuracy"]) + " | " + "Date: "
    + str(document[0]["date"]))
    return


def initialize_graph(max_graph_size):
    # clear the graph before creating one
    plt.clf()

    plt.xlabel('Last Attempts')
    plt.ylabel('WPM') 
    # plt.legend() 

    x_axis = []
    y_axis = []
    x_axis = [0 for i in range(max_graph_size)] 
    y_axis = [0 for i in range(max_graph_size)]

    return x_axis, y_axis

def set_x_y_values(x_axis, y_axis, document, count):
    x_axis[count] = count + 1
    y_axis[count] = document["wpm"]

def create_graph_file (x_axis, y_axis):
    # plot the graph and store it in a variable
    plt.plot(x_axis, y_axis)
    file_name = 'output.png'
    plt.savefig(file_name)
    return file_name

async def find_user_results(user_data, max_graph_size):
    count = 0
    for num in await user_data.to_list(length=max_graph_size):
        count += 1
    return count

async def send_graph(ctx, db, topic):
    max_graph_size = 7
    collection = db["typing"]
    user_data = collection.find({"name": topic})

    result_amount = await find_user_results(user_data, max_graph_size)
    if result_amount < max_graph_size:
        await ctx.send("Not enough results. Do more typing tests!")
        return
    else:
        # where the rightmost value is your most recent typing speed
        x_axis, y_axis = initialize_graph(max_graph_size)
        user_data = collection.find({"name": topic}).sort("_id", pymongo.DESCENDING) # most recent
        count = max_graph_size - 1
        for document in await user_data.to_list(length=max_graph_size):
            set_x_y_values (x_axis, y_axis, document, count)    
            count -= 1

        file_name = create_graph_file (x_axis, y_axis)
        await ctx.send(file=discord.File(file_name))
        return

async def send_article_choices (ctx, news_result):
    count = 1
    for news_info in news_result:
        await ctx.send("[" + str(count) + "] " + news_info["title"])
        count += 1
        if count > 5:
            break

async def get_news_url (ctx, news_result, user_text):
    try:
        if int(user_text) > 0 and int(user_text) < 6:
            return news_result[int(user_text)-1]["link"], True
        else:
            await ctx.send("Invalid! Please retype the command.")
            return "", False
    except:
        await ctx.send("Invalid! Please retype the command.")
        return "", False

async def download_article (ctx, url):
    try:
        article = Article (url)
        article.download()
        return article, True
    except:
        await ctx.send("Invalid article! Please retype the command and choose a different article.")
        return article, False

def get_news (topic):
    news = GoogleNews(period='1d')
    news.search(topic)
    news_result = news.result()
    return news_result

async def get_article_text (ctx, article):
    try:
        article.parse()
        nltk.download('punkt')
        article.nlp()
        return article.summary[:250], True
    except:
        await ctx.send("Invalid article! Please retype the command and choose a different article.")
        return "", False

async def get_wiki_text (ctx, topic, sentence_length):
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
                await ctx.send("Couldn't find anything. Try something else!")
                return "", False

def find_wpm_and_time (end_time, start_time, user_text):
    # wpm = number of words typed / time taken in seconds ) * 60
    total_time = round (end_time - start_time, 2)
    total_message_words = len((user_text).split())
    wpm = int (round((total_message_words / total_time) * 60))
    return wpm, total_time

def find_accuracy(text, user_text):
    return int (round (SequenceMatcher(None, text, user_text).ratio() * 100, 2)) 

async def send_typing_results(ctx, start_time, end_time, user_text, text, user_id):
    wpm, total_time = find_wpm_and_time(end_time, start_time, user_text)
    accuracy = find_accuracy(text, user_text)
    await ctx.send(user_id)
    await ctx.send("%s seconds to type!" %total_time + "\n%s wpm!" %(wpm) + "\n%s%% accuracy!" %accuracy)
    return wpm, accuracy


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

async def insert_type_db(db, user_id, wpm, accuracy):
    collection = db["typing"]
    new_data = create_type_data (user_id, wpm, accuracy)
    await collection.insert_one(new_data)

async def check_profile (ctx, db, user_id):
    collection = db["profile"]

    if await check_user_exists (str(user_id), db, "profile") == False:    
        new_data = create_profile_data (user_id)
        await collection.insert_one(new_data)
        await ctx.send("Profile has been created for " +  str(user_id) + "!")
    return

async def update_profile_db (db, user_id, wpm):
    collection = db["profile"]

    await collection.update_one({"name": str(user_id)}, {"$inc": {"races": 1}})
    user_data = collection.find({"name": str(user_id)}).sort("_id", pymongo.DESCENDING)

    for document in await user_data.to_list(length=1):
        new_wpm = int (round(((document["wpm"] * (document["races"] - 1)) + wpm)/document["races"]))
        collection.update_one({"name": str(user_id)}, {"$set": {"wpm": new_wpm}})
        if wpm > document["best_race"]:
            collection.update_one({"name": str(user_id)}, {"$set": {"best_race": wpm}})