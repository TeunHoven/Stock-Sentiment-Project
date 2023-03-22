import praw
import pandas as pd
import datetime as dt
import nltk
from decouple import config
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from django.contrib.staticfiles import finders
from django.utils import timezone, dateformat, dateparse

from ..models import Post, Company, General

from .test_stock_data import get_company_data

begin_time = dt.datetime.now()

two_days_ago = dt.datetime.utcnow() - dt.timedelta(days=2)

setup_begin_time = dt.datetime.now()

sia = SentimentIntensityAnalyzer()

######################################
#########TODO: Use OpenAI#############
######################################

############# ALL STOCKS DICTIONARIES POSTS #############
all_stocks = {}
stocks_dict_positive = {}
stocks_dict_medium = {}
stocks_dict_negative = {}
stocks_dict_diff = {}
#########################################################

############# ALL STOCKS DICTIONARIES COMMENTS #############
# TODO Make this script work with comments on posts
all_stocks_comments = {}
stocks_dict_comments_positive = {}
stocks_dict_comments_medium = {}
stocks_dict_comments_negative = {}
stocks_dict_comments_on_post = {}
stocks_dict_comments_diff = {}
#########################################################
post_dict = {}

# Read a CSV file to get common stock tickers with corresponding company name
raw_data = pd.read_csv(finders.find('tickers.csv'))

# Converts the raw data from the CSV file into a tickers list with the corresponding company name
tickers = raw_data.to_dict(orient='list')

# The tickers blacklist because these are also words that are used often or are meme stocks
blacklist = ["A", "AA", "AAA", "I", "DD", "WSB", "YOLO", "RH", "EV", "PE", "ETH", "BTC", "E", "ARE", "FOR", "ON", "DO", "IT", "ALL",
            "BE", "CAN", "NOW", "CEO", "S", "U", "PT", "K", "AONE"]

# Get the posts off of Reddit
def get_posts(aantal_posts):
    reddit = praw.Reddit(client_id=config('CLIENTID'), client_secret=config('SECRETID'),
                        user_agent='Stock Scraper', username=config('REDDIT_USERNAME'), password=config('PASSWORD')) # log into Reddit using .env file
    subreddit_stocks = reddit.multireddit('DutchLifeIsGood', 'stocks')  # My stocks multireddit

    print("Getting " + str(aantal_posts) + " posts")
    print("Starting at: " + str(dt.datetime.now()) + "\n")

    new_stocks = subreddit_stocks.new(limit=aantal_posts)   # Get the newest posts with a maximum of $aantal_posts$

    new_titles = 0
    new_comments = 0

    # Goes through all posts from $new_stocks$ and adds them to the posts dictionary
    for submission in new_stocks:
        if dt.datetime.utcfromtimestamp(submission.created_utc) >= two_days_ago:
            new_titles += 1
            post_dict[submission.title] = [submission.selftext]
            post_dict[submission.title].append(reddit.config.reddit_url + submission.permalink)
            post_dict[submission.title].append(submission.created_utc)
            comments = []
            submission.comments.replace_more(limit=None)
            for comment in submission.comments.list():
                comments.append(comment.body)
                new_comments += 1
            post_dict[submission.title].append(comments)
        else:
            print("")

    print("New titles: " + str(new_titles))
    print("New comments: " + str(new_comments) + "\n")

    setup_runtime = dt.datetime.now() - setup_begin_time
    print("Runtime to get posts:", setup_runtime)
    print("Average runtime per post:", setup_runtime/new_titles, "\n")

########################################################################################################################
########################################################################################################################
########################################################################################################################
                                            # !END SETUP! #

# Checks whether a post has a positive, neutral or negative sentiment and adds the stock to the corresponding dictionary
def add_to_ticker(ticker, sentiment):
    if ticker in all_stocks:
        all_stocks[ticker] += 1
    else:
        all_stocks[ticker] = 1

    # If sentiment is above 0.3, the stock will be counted as POSITIVE
    if sentiment >= 0.3:
        if ticker in stocks_dict_positive.keys():
            stocks_dict_positive[ticker] += 1
        else:
           stocks_dict_positive[ticker] = 1
        return 'positive'
    # If sentiment is above -0.3 and below 0.3, the stock will be counted as NEUTRAL
    elif -0.3 < sentiment < 0.3:
        if ticker in stocks_dict_medium.keys():
            stocks_dict_medium[ticker] += 1
        else:
            stocks_dict_medium[ticker] = 1
        return 'neutral'
    # If sentiment is below -0.3, the stock will be counted as NEGATIVE
    else:
        if ticker in stocks_dict_negative.keys():
            stocks_dict_negative[ticker] += 1
        else:
            stocks_dict_negative[ticker] = 1
        return 'negative'
    
# Function to get the company name out of a sentence
def get_company_out_of_sentence(sentence):
    for ticker in tickers:
        company = tickers[ticker][0]    # Goes through all tickers to find the full company name
        if company in sentence:
            return ticker

    return None

# Get all the words out of the sentence using Natural Language Toolkit
def get_all_words_out_of_sentence(sentence):
    words = []
    if not (sentence == '' or sentence == ' '):
        tmp_words = nltk.word_tokenize(sentence)
        tokens = nltk.pos_tag(tmp_words)
        words = tokens

    return words

# Checks if a word is a ticker of a stock
def word_is_ticker(word):
    if word[:1] == '$' or word[:1] == '#':
        word = word[1:]
    if word not in blacklist:
        for ticker in tickers:
            if ticker == word:
                return ticker
    return None

# Gets the sentiment of the post using SentimentIntensityAnalyzer (sia)
def get_post_sentiment(body):
    sentiment = sia.polarity_scores(body)["compound"]
    return sentiment

# The main part of the program, in this function it will go through all the posts
def check_stocks():
    general = False
    many_titles = 0
    many_comments = 0   # Not yet implemented
    total_time = dt.timedelta(days=0)
    total_comment_time = dt.timedelta(days=0)
    # Goes through the titles of all the posts
    for title in post_dict.keys():
        checkup_begin_time = dt.datetime.now()
        body = post_dict[title][0]  # Gets body of the post
        url = post_dict[title][1]   # Gets the full url of the post
        # time = post_dict[title][2]
        # comments = post_dict[title][3]  
        # post_about_stock = False

        many_titles += 1
        seen_tickers = []

        sentences = title.split(". ")   # Splits the title into sentences
        # Goes through the sentences that are in the title and get companies out of it
        for i in range(len(sentences)):
            sentence = sentences[i]
            company = get_company_out_of_sentence(sentence)
            if company is not None:
                seen_tickers.append(company)
            words = get_all_words_out_of_sentence(sentence)
            for w in words:
                ticker = word_is_ticker(w[0])
                if ticker is not None:
                    post_about_stock = True
                    seen_tickers.append(ticker)

        sentences = body.split(".") # Splits the body of the post into sentences
        # Goes through all the sentences of the body and extracts companies and tickers out of it
        for i in range(len(sentences)):
            sentence = sentences[i]
            company = get_company_out_of_sentence(sentence)
            if company is not None:
                seen_tickers.append(company)
            words = get_all_words_out_of_sentence(sentence)
            for w in words:
                ticker = word_is_ticker(w[0])
                if ticker is not None:
                    post_about_stock = True
                    seen_tickers.append(ticker)

        comment_begin_time = dt.datetime.now()
        # Loops through the companies that are mentioned in the post
        for ticker in set(seen_tickers):
            company = tickers[ticker][0]    # Full name of the company
            sentiment = get_post_sentiment(body)    # Sentiment of the body of the post
            sentiment = add_to_ticker(ticker, sentiment)    # Adds the ticker to the correct dictionary

            exists = Post.objects.filter(post=url).values() # Gets the post if it has been saved in the database
            print(exists)

            execute = False         # Makes sure that there is enough data on the company to save it

            if(len(exists) == 0):   # Checks whether the post does not exist already
                try:                # Tries to get the company data from the database. If it does not exists then create new record
                    companyData = Company.objects.get(name=company)
                    print(f'The {company} company does exist')
                except Company.DoesNotExist:    # If company record does not exists then create new record
                    print(f'The {company} company ({ticker}) does not exist')
                    
                    api_calls = get_company_data(ticker)

                    if(api_calls != False):
                        execute = True
                    else:
                        print('Not enough data to convert to a good record in the database!')

                if execute:
                    sentiment_record = Post.NEUT
                    

                    companyData = Company.objects.get(ticker=ticker)

                    # Checks what kind of sentiment the post has
                    if sentiment == 'positive':
                        sentiment_record = Post.POS
                    elif sentiment == 'neutral':
                        sentiment_record = Post.NEUT
                    else:
                        sentiment_record = Post.NEG
                        
                    # Create new record of the Post and saves it to the database
                    p = Post(company=companyData, date=timezone.now(), post=url, sentiment=sentiment_record)
                    p.save()

                    # Updates the general object in the database for general information 
                    general = General.objects.get(id=1)                                     # Get the general database object

                    today = timezone.now()
                    lastUpdated = general.lastUpdated
                    print(lastUpdated)
                    print(today)
                    if((today - general.lastUpdated).days == 0):                                # Checks whether the last update was yesterday
                        general.apiCalls = general.apiCalls + api_calls                                 # Update the amount of API Calls been made
                    else:
                        general.apiCalls = api_calls                                                    # Update the amount of API Calls to 0 because it is a new day


                    general.lastUpdated = dateformat.format(timezone.now(), 'Y-m-d H:i:s')  # Update the last updated time
            
                    general.save()                                                          # Save the general object to the database
            else:
                print('Post has already been examined')
                # Updates the general object in the database for general information 
                general = General.objects.get(id=1)                                     # Get the general database object
                general.lastUpdated = dateformat.format(timezone.now(), 'Y-m-d H:i:s')  # Update the last updated time
                general.save()    

        total_time += dt.datetime.now()-checkup_begin_time  # Calculates the time the program needed to finish for the posts                                                   # Save the general object to the database

    print("Total titles:" + str(many_titles) + "\n")    # Prints the amount of posts that has been handled by the program

    print("Total post time:" + str(total_time)) # Prints the total time that the program needed to run
    print("Average post time:" + str(total_time/many_titles) + "\n")    # Prints the average time the program needed per post
    return general

# runs the program
def run():
    get_posts(15)
    general = check_stocks()

    return stocks_dict_positive, stocks_dict_medium, stocks_dict_negative, general