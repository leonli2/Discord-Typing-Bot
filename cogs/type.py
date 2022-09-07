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
            if await check_user_exists(topic, db, "profile") == False:
                await ctx.send("You do not have a profile yet. Please complete a typing test first!")
            else:
                await send_profile_message(ctx, db, topic)
            return

        elif user_choice == "recent" or user_choice == "graph":
            if await check_user_exists(topic, db, "typing") == False:
                await ctx.send("You do not have a profile yet. Please complete a typing test first!")
            else:
                if user_choice == "recent":
                    await send_recent_message(ctx, db, topic)
                else:
                    await send_graph (ctx, db, topic)
            return
            
        elif user_choice == "news":
            news_result = get_news (topic)
            
            await ctx.send("*Please select an article by entering the number of the article you want!*")
            await send_article_choices (ctx, news_result)
            user_message = await self.bot.wait_for("message", check=None)
            user_text = user_message.content

            url, url_valid = await get_news_url (ctx, news_result, user_text)
            if url_valid == False:
                return            

            article, article_valid = await download_article (ctx, url)
            if article_valid == False:
                return 

            text, text_valid = await get_article_text (ctx, article)
            if text_valid == False:
                return 

        else:
            text, wiki_valid = await get_wiki_text (ctx, topic, sentence_length)
            if wiki_valid == False:
                return
            
        # send passage
        await ctx.send("Type this:")
        await ctx.send(text)
        
        start_time = time.time()
        user_message = await self.bot.wait_for("message", check=None)
        end_time = time.time()

        user_id = user_message.author
        user_text = user_message.content
        wpm, accuracy = await send_typing_results(ctx, start_time, end_time, user_text, text, user_id)

        # insert new typing result into database
        await insert_type_db (db, user_id, wpm, accuracy)
        
        # check if they have a profile, if not, make one
        await check_profile(ctx, db, user_id)

        await update_profile_db (db, user_id, wpm)
        
async def setup(bot):
    await bot.add_cog(Type(bot))