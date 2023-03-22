import praw
import os
import pandas as pd
import datetime as dt
from collections import OrderedDict
import numpy as np
import nltk
from decouple import config
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from django.contrib.staticfiles import finders
from django.utils import timezone

from ..models import Post, Company

begin_time = dt.datetime.now()

two_days_ago = dt.datetime.utcnow() - dt.timedelta(days=2)

def calculate_execution_time(aantal_posts):
    total_time = 0
    average_getting_posts = 0.30
    average_post_check = 0.35
    average_comment_post = 0.15
    amount_of_comments = 1500

    if aantal_posts > 250:
        average_getting_posts = 0.5
        average_post_check = 0.65
        average_comment_post = 0.1
        amount_of_comments = 10000
    elif aantal_posts > 500:
        average_getting_posts = 0.9
        average_post_check = 1
        average_comment_post = 0.1
        amount_of_comments = 20000
    elif aantal_posts > 750:
        average_getting_posts = 1.2
        average_post_check = 1.35
        average_comment_post = 0.1
        amount_of_comments = 40000
    else:
        average_getting_posts = 1.55
        average_post_check = 1.7
        average_comment_post = 0.1
        amount_of_comments = 125000

    total_time = (aantal_posts*average_getting_posts)+(aantal_posts*average_post_check)+(amount_of_comments*average_comment_post)
    return total_time


# Personal WZZ6S4djCM0qEA
# Secret LVImm2gFemD4rckZiJBEoVg2plADnA
                                            # !SETUP! #
########################################################################################################################
########################################################################################################################
########################################################################################################################
setup_begin_time = dt.datetime.now()

sid = SentimentIntensityAnalyzer()

# user_input = input("How many post to analyze: ")
# is_integer = False

# try:
#     user_input = int(user_input)
#     is_integer = True
# except ValueError:
#     print("That is not an whole integer!")

# while is_integer == False:
#     user_input = input("How many post to analyze: ")

#     try:
#         user_input = int(user_input)
#         is_integer = True
#     except ValueError:
#         print("That is not an whole integer!")

# aantal_posts = user_input



############# ALL STOCKS DICTIONARIES POSTS #############
all_stocks = {}
stocks_dict_positive = {}
stocks_dict_medium = {}
stocks_dict_negative = {}
stocks_dict_diff = {}
#########################################################

############# ALL STOCKS DICTIONARIES COMMENTS #############
all_stocks_comments = {}
stocks_dict_comments_positive = {}
stocks_dict_comments_medium = {}
stocks_dict_comments_negative = {}
stocks_dict_comments_on_post = {}
stocks_dict_comments_diff = {}
#########################################################
post_dict = {}

raw_data = pd.read_csv(finders.find('tickers.csv'))

tickers = raw_data.to_dict(orient='list')
blacklist = ["A", "AA", "AAA", "I", "DD", "WSB", "YOLO", "RH", "EV", "PE", "ETH", "BTC", "E", "ARE", "FOR", "ON", "DO", "IT", "ALL",
            "BE", "CAN", "NOW", "CEO", "S", "U", "PT", "K", "AONE"]

def get_posts(aantal_posts):
    reddit = praw.Reddit(client_id=config('CLIENTID'), client_secret=config('SECRETID'),
                        user_agent='Stock Scraper', username=config('REDDIT_USERNAME'), password=config('PASSWORD'))
    subreddit_stocks = reddit.multireddit('DutchLifeIsGood', 'stocks')

    time_total_int = calculate_execution_time(aantal_posts)
    time_total_datetime = dt.timedelta(seconds=time_total_int)

    print("Getting " + str(aantal_posts) + " posts")
    print("Calculated execute time: " + str(time_total_datetime) + "; H:MM:ss:mm")
    print("Starting at: " + str(dt.datetime.now()) + "\n")

    new_stocks = subreddit_stocks.new(limit=aantal_posts)

    new_titles = 0
    new_comments = 0
    for submission in new_stocks:
        if dt.datetime.utcfromtimestamp(submission.created_utc) >= two_days_ago:
            new_titles += 1
            post_dict[submission.title] = [submission.selftext]
            post_dict[submission.title].append(submission.url)
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


def add_to_ticker(ticker, sentiment):
    if ticker in all_stocks:
        all_stocks[ticker] += 1
    else:
        all_stocks[ticker] = 1

    if sentiment >= 0.3:
        if ticker in stocks_dict_positive.keys():
            stocks_dict_positive[ticker] += 1
        else:
           stocks_dict_positive[ticker] = 1
        return 'positive'
    elif -0.3 < sentiment < 0.3:
        if ticker in stocks_dict_medium.keys():
            stocks_dict_medium[ticker] += 1
        else:
            stocks_dict_medium[ticker] = 1
        return 'neutral'
    else:
        if ticker in stocks_dict_negative.keys():
            stocks_dict_negative[ticker] += 1
        else:
            stocks_dict_negative[ticker] = 1
        return 'negative'


def add_to_comments(ticker, sentiment):
    if ticker in all_stocks_comments.keys():
        all_stocks_comments[ticker] += 1
    else:
        all_stocks_comments[ticker] = 1

    if sentiment >= 0.3:
        if ticker in stocks_dict_comments_positive.keys():
            stocks_dict_comments_positive[ticker] += 1
        else:
            stocks_dict_comments_positive[ticker] = 1
    elif -0.3 < sentiment < 0.3:
        if ticker in stocks_dict_comments_medium.keys():
            stocks_dict_comments_medium[ticker] += 1
        else:
            stocks_dict_comments_medium[ticker] = 1
    else:
        if ticker in stocks_dict_comments_negative.keys():
            stocks_dict_comments_negative[ticker] += 1
        else:
            stocks_dict_comments_negative[ticker] = 1


def word_is_ticker(word):
    if word[:1] == '$' or word[:1] == '#':
        word = word[1:]
    if word not in blacklist:
        for ticker in tickers:
            if ticker == word:
                return ticker
    return None


def get_company_out_of_sentence(sentence):
    for ticker in tickers:
        company = tickers[ticker][0]
        if company in sentence:
            return ticker

    return None


def get_all_words_out_of_sentence(sentence):
    words = []
    if not (sentence == '' or sentence == ' '):
        tmp_words = nltk.word_tokenize(sentence)
        tokens = nltk.pos_tag(tmp_words)
        words = tokens

    return words


def get_comment_sentiment(ticker, comment):
    sentences = comment.split(". ")
    sentiment_ticker_sentence = 0
    sentiment_other_sentences = 0
    index_other = 0
    index_ticker = 0
    for sentence in sentences:
        sentiment = sid.polarity_scores(sentence)["compound"]
        if ticker in sentence:
            sentiment_ticker_sentence += sentiment
            index_ticker += 1
        else:
            sentiment_other_sentences += sentiment
            index_other += 1
    if index_ticker > 0:
        sentiment_ticker_sentence = sentiment_ticker_sentence/index_ticker
    if index_other > 0:
        sentiment_other_sentences = sentiment_other_sentences/index_other
    return (sentiment_ticker_sentence+sentiment_other_sentences)/2


def get_post_sentiment(body):
    sentiment = sid.polarity_scores(body)["compound"]
    return sentiment


def check_comments(comments, ticker):
    post_ticker = ticker
    seen_tickers = []

    total_comments = 0
    for comment in comments:
        total_comments += 1
        sentences = comment.split(".")
        for i in range(len(sentences)):
            sentence = sentences[i]
            company = get_company_out_of_sentence(sentence)
            if company is not None:
                seen_tickers.append(company)
            words = get_all_words_out_of_sentence(sentence)
            for w in words:
                if w not in blacklist:
                    ticker = word_is_ticker(w[0])
                    if ticker is not None:
                        seen_tickers.append(ticker)
        
        for tick in set(seen_tickers):
            sentiment = get_comment_sentiment(tick, comment)
            if post_ticker in seen_tickers:
                if tick in stocks_dict_comments_on_post:
                    stocks_dict_comments_on_post[tick] += 1
                else:
                    stocks_dict_comments_on_post[tick] = 1
            if sentiment != 0.0:
                add_to_comments(tick, sentiment)
    return total_comments


def check_stocks():
    many_titles = 0
    many_comments = 0
    total_time = dt.timedelta(days=0)
    total_comment_time = dt.timedelta(days=0)
    for title in post_dict.keys():
        checkup_begin_time = dt.datetime.now()
        body = post_dict[title][0]
        url = post_dict[title][1]
        # time = post_dict[title][2]
        comments = post_dict[title][3]
        post_about_stock = False

        many_titles += 1
        seen_tickers = []

        sentences = title.split(". ")
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

        sentences = body.split(".")
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
        for ticker in set(seen_tickers):
            company = tickers[ticker][0]
            sentiment = get_post_sentiment(body)
            sentiment = add_to_ticker(ticker, sentiment)

            exists = Post.objects.filter(post=url).values()
            print(exists)

            if(len(exists) == 0):
                try:
                    print(f'The {company} company does exist')
                    companyData = Company.objects.get(name=company)
                except Company.DoesNotExist:
                    print(f'The {company} company does not exist')
                    companyData = Company(name=company, ticker=ticker)
                    companyData.save()

                if sentiment == 'positive':
                    p = Post(company=companyData, date=timezone.now(), post=url, sentiment=Post.POS)
                    p.save()
                elif sentiment == 'neutral':
                    p = Post(company=companyData, date=timezone.now(), post=url, sentiment=Post.NEUT)
                    p.save()
                else:
                    p = Post(company=companyData, date=timezone.now(), post=url, sentiment=Post.NEG)
                    p.save()
            else:
                print('exists')

            # many_comments += check_comments(comments, ticker)     Comments not yet implemented

        #if not post_about_stock:
            # many_comments += check_comments(comments, None)       Comments not yet implemented
        total_time += dt.datetime.now()-checkup_begin_time
        total_comment_time += dt.datetime.now()-comment_begin_time

    print("Total titles:" + str(many_titles) + "\n")

    print("Total post time:" + str(total_time))
    print("Average post time:" + str(total_time/many_titles) + "\n")

    # print("\nTotal comment time:" + str(total_comment_time))
    # print("Average comment time:" + str(total_comment_time/many_comments) + "\n")


# check_stocks()

def check_difference_posts():
    for ticker in stocks_dict_positive.keys():
        if ticker not in stocks_dict_negative:
            stocks_dict_diff[ticker] = stocks_dict_positive[ticker]
        num_pos = stocks_dict_positive[ticker]
        if ticker in stocks_dict_negative:
            num_neg = stocks_dict_comments_negative[ticker]
        else:
            num_neg = 0
        if ticker in stocks_dict_medium:
            num_med = stocks_dict_medium[ticker]
        else:
            num_med = 0
        stocks_dict_diff[ticker] = [num_pos-num_neg, num_med]

def check_difference_comments():
    for ticker in stocks_dict_comments_positive.keys():
        num_pos = stocks_dict_comments_positive[ticker]
        if ticker in stocks_dict_comments_negative:
            num_neg = stocks_dict_comments_negative[ticker]
        else:
            num_neg = 0
        if ticker in stocks_dict_comments_medium:
            num_med = stocks_dict_comments_medium[ticker]
        else:
            num_med = 0
        stocks_dict_comments_diff[ticker] = [num_pos-num_neg, num_med]

# check_difference_posts()
# check_difference_comments()

def save_file(name, dict, many):
    if(len(dict) > 0):
        f = open("output/" + name + ".txt", 'w')
        index = 0
        f.write("Date of output: " + str(dt.datetime.now()) + "\n")
        if(type(list(dict.values())[0]) is int):
            if many > 0:
                for key in dict.keys():
                    if index < (many):
                        line = str(index + 1) + ". " + str(key) + " " + str(tickers[key]) + ": " + str(
                            dict[key]) + "\n"
                        f.write(line)
                    else:
                        break
                    index += 1
            else:
                for key in dict.keys():
                    line = str(index + 1) + ". " + str(key) + " " + str(tickers[key]) + ": " + str(
                        dict[key]) + "\n"
                    f.write(line)
                    index += 1
        else:
            for ticker in dict.keys():
                line = str(index + 1) + ". " + str(ticker) + " " + str(tickers[ticker]) + ": " 
                for i in range(0, 2):
                    if(i == 0):
                        line += str(dict[ticker][i]) + ", "
                    else:
                        line += str(dict[ticker][i]) + ";\n"            
                f.write(line)
                index += 1
        f.close()

def run():
    get_posts(15)
    check_stocks()

    return stocks_dict_positive, stocks_dict_medium, stocks_dict_negative


# # All Stocks
# all_stocks = OrderedDict(sorted(all_stocks.items(), key=lambda t: t[1], reverse=True))
# save_file("all_stocks", all_stocks, 0)

# # All Positive
# stocks_dict_positive = OrderedDict(sorted(stocks_dict_positive.items(), key=lambda t: t[1], reverse=True))
# save_file("all_stocks_positive", stocks_dict_positive, 0)

# # Only top 5 Positive
# save_file("top_5_positive", stocks_dict_positive, 5)

# # All Medium
# stocks_dict_medium = OrderedDict(sorted(stocks_dict_medium.items(), key=lambda t: t[1], reverse=True))
# save_file("all_stocks_medium", stocks_dict_medium, 0)

# # Only top 5 Medium
# save_file("top_5_medium", stocks_dict_medium, 5)

# # All Negative
# stocks_dict_negative = OrderedDict(sorted(stocks_dict_negative.items(), key=lambda t: t[1], reverse=True))
# save_file("all_stocks_negative", stocks_dict_negative, 0)

# # Only top 5 Negative
# save_file("top_5_negative", stocks_dict_negative, 5)

# # All Different Posts
# stocks_dict_diff = OrderedDict(sorted(stocks_dict_diff.items(), key=lambda t: t[1], reverse=True))
# save_file("difference_posts", stocks_dict_diff, 0)

# # All comments
# all_stocks_comments = OrderedDict(sorted(all_stocks_comments.items(), key=lambda t: t[1], reverse=True))
# save_file("all_comments", all_stocks_comments, 0)

# # All Positive Comments
# stocks_dict_comments_positive = OrderedDict(sorted(stocks_dict_comments_positive.items(), key=lambda t: t[1], reverse=True))
# save_file("all_comments_positive", stocks_dict_comments_positive, 0)

# # All Negative Comments
# stocks_dict_comments_negative = OrderedDict(sorted(stocks_dict_comments_negative.items(), key=lambda t: t[1], reverse=True))
# save_file("all_comments_negative", stocks_dict_comments_negative, 0)

# # All Medium Comments
# stocks_dict_comments_medium = OrderedDict(sorted(stocks_dict_comments_medium.items(), key=lambda t: t[1], reverse=True))
# save_file("all_comments_medium", stocks_dict_comments_medium, 0)

# # All Posts Comments
# stocks_dict_comments_on_post = OrderedDict(sorted(stocks_dict_comments_on_post.items(), key=lambda t: t[1], reverse=True))
# save_file("all_comments_about_post", stocks_dict_comments_on_post, 0)

# # All Difference Comments
# stocks_dict_comments_diff = OrderedDict(sorted(stocks_dict_comments_diff.items(), key=lambda t: t[1], reverse=True))
# save_file("difference_comments", stocks_dict_comments_diff, 0)

print("Finished at: " + str(dt.datetime.now()))

runtime = dt.datetime.now() - begin_time
print("Runtime (H:mm:ss:ms):", runtime)
