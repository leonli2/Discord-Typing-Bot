import time
import discord
import wikipedia
import nltk
import pymongo
import matplotlib
import matplotlib.pyplot as plt
import pandas
from pandas_datareader import data as pdr
import numpy as np
from datetime import date
from newspaper import Article
from GoogleNews import GoogleNews

from discord.ext import commands
from type.typefunctions import *

class Type(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.command()
    async def type (self,ctx,user_choice = "wiki", topic = "programming"):
        """
        Test your typing speed

        Use dashes if your topic has multiple words in it
        """
        
        sentence_length = 1

        # mongoDB
        db = self.bot.mongoConnect["discord"]
        collection = db["typing"]

        # delete database for profile and typing results
        if user_choice == "d":
            db = self.bot.mongoConnect["discord"]
            collection = db["typing"]
            collection.delete_many({})

            collection = db["profile"]
            collection.delete_many({})
            await ctx.send("deleted")
            return

        elif user_choice == "profile":
            collection = db["profile"]

            if await check_user_exists(topic, collection) == False:
                await ctx.send("You do not have a profile yet. Please complete a typing test first!")
                return

            user_data = collection.find({"name": topic}).sort(topic)
            document = await user_data.to_list(length=1)
            await ctx.send("Name: " + document[0]["name"] + " | " + "Avg WPM: " + str (document[0]["wpm"])
            + " | " + "Best Race: " + str(document[0]["best_race"]) + " | " + "Races Completed: "
            + str(document[0]["races"]))
            return

        elif user_choice == "recent":
            collection = db["typing"]

            if await check_user_exists(topic, collection) == False:
                await ctx.send("You do not have a profile yet. Please complete a typing test first!")
                return

            userData = collection.find({"name": topic}).sort("_id", pymongo.DESCENDING)
            for document in await userData.to_list(length=1):
                await ctx.send("Name: " + document["name"] + " | " + "WPM: " + str (document["wpm"])
                + " | " + "Accuracy: " + str(document["accuracy"]) + " | " + "Date: "
                + str(document["date"]))
            return

        elif user_choice == "graph":
            collection = db["typing"]
            userData = collection.find({"name": topic}).sort("_id", pymongo.DESCENDING) # most recent
            
            if check_user_exists == False:
                    await ctx.send("You do not have a profile yet. Please complete a typing test first!")
                    return

            x_axis, y_axis = initialize_graph()

            count = 0
            for document in await userData.to_list(length=7):
                set_x_y_values (x_axis, y_axis, document, count)    
                count += 1
        
            file_name = create_graph (x_axis, y_axis)
            await ctx.send(file=discord.File(file_name))
            return

        elif user_choice == "news":
            
            news_result = get_news (topic)
            await ctx.send("*Please select an article by entering the number of the article you want!*")

            count = 1
            for news_info in news_result:
                await ctx.send("[" + str(count) + "] " + news_info["title"])
                count += 1
                if count > 5:
                    break
                
            user_message = await self.bot.wait_for("message", check=None)
            user_text = user_message.content

            try:
                if int(user_text) > 0 and int(user_text) < 6:
                    url = news_result[int(user_text)-1]["link"]
                else:
                    await ctx.send("Invalid! Please retype the command.")
                    return
            except:
                await ctx.send("Invalid! Please retype the command.")
                return

            try:
                article = Article (url)
                article.download()
            except:
                await ctx.send("Invalid article! Please retype the command and choose a different article.")
                return

            text = get_article_text (article)

        else:
            
            text, check_wiki = get_wiki_text (topic, sentence_length)

            if check_wiki == False:
                await ctx.send("Couldn't find anything. Try something else!")
                return
            
        # now type
        await ctx.send("Type this:")
        await ctx.send(text)
        
        start_time = time.time()
        user_message = await self.bot.wait_for("message", check=None)
        end_time = time.time()

        user_id = user_message.author
        user_text = user_message.content
        await ctx.send(user_id)

        wpm, total_time = find_wpm_and_time(end_time, start_time, user_text)
        accuracy = find_accuracy(text, user_text)
        await ctx.send("%s seconds to type!" %total_time + "\n%s wpm!" %(wpm) + "\n%s%% accuracy!" %accuracy)

        # insert new typing result into database
        new_data = create_type_data (user_id, wpm, accuracy)
        await collection.insert_one(new_data)

        # check if they have a profile, if not, make one
        collection = db["profile"]

        # if await collection.find_one({"name":  str(user_id)}) == None:
        if await check_user_exists (str(user_id), collection) == False:    
            new_data = create_profile_data (user_id)
            await collection.insert_one(new_data)
            await ctx.send("Profile has been created for " +  str(user_id) + "!")

        await collection.update_one({"name": str(user_id)}, {"$inc": {"races": 1}})
        userData = collection.find({"name": str(user_id)}).sort("_id", pymongo.DESCENDING)

        for document in await userData.to_list(length=1):
            new_wpm = int (round(((document["wpm"] * (document["races"] - 1)) + wpm)/document["races"]))
            collection.update_one({"name": str(user_id)}, {"$set": {"wpm": new_wpm}})
            if wpm > document["best_race"]:
                collection.update_one({"name": str(user_id)}, {"$set": {"best_race": wpm}})
        
async def setup(bot):
    await bot.add_cog(Type(bot))