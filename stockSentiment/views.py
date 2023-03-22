# Django imports
from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, JsonResponse
from django.utils import timezone, dateformat, dateparse
from datetime import timedelta
from django.db.models.functions import Now
from django.core import serializers

# Other imports
import json
import requests
from decouple import config

# Own project imports
from .models import Post, Company, CompanyStockData, General
from .scripts import sentiment

API_KEY = config('API_KEY_ALPHAV')

# Create your views here.
def Main(request):
    positive = Post.objects.filter(sentiment='positive').order_by('date').values()
    neutral = Post.objects.filter(sentiment='neutral').order_by('date').values()
    negative = Post.objects.filter(sentiment='negative').order_by('date').values()
    template = loader.get_template('main.html')

    general = General.objects.get(id=1)

    context = {
        'positive': positive,
        'medium': neutral,
        'negative': negative,
        'last_generated': general.lastUpdated,
        'api_calls': general.apiCalls,
    }

    return HttpResponse(template.render(context, request))

def Generate(request):
    positive, neutral, negative, general = sentiment.run()

    print(general)

    context = {
        'executed': True,
        'last_updated': general.lastUpdated,
        'api_calls': general.apiCalls,
    }

    return HttpResponse(context)

def GetPositive(request):
    positive = Post.objects.filter(sentiment='positive').filter(date__gte=Now()-timedelta(days=1)).values()

    json_object = {}

    for post in positive:
        company_serialized = serializers.serialize('json', [Company.objects.get(id=post['company_id']),])
        company = json.loads(company_serialized)[0]['fields']
        post['name'] = company['name']
        post['ticker'] = company['ticker']
        post['date'] = dateformat.format(post['date'], 'd-m-Y')
        json_object[company['name']] = post

    json_object = json.dumps(json_object)

    return JsonResponse(json_object, safe=False)

def GetNeutral(request):
    neutral = Post.objects.filter(sentiment='neutral').filter(date__gte=Now()-timedelta(days=1)).values()

    json_object = {}

    for post in neutral:
        company_serialized = serializers.serialize('json', [Company.objects.get(id=post['company_id']),])
        company = json.loads(company_serialized)[0]['fields']
        post['name'] = company['name']
        post['ticker'] = company['ticker']
        post['date'] = dateformat.format(post['date'], 'd-m-Y')
        json_object[company['name']] = post

    json_object = json.dumps(json_object)

    return JsonResponse(json_object, safe=False)

def GetNegative(request):
    negative = Post.objects.filter(sentiment='negative').filter(date__gte=Now()-timedelta(days=1)).values()

    json_object = {}

    for post in negative:
        company_serialized = serializers.serialize('json', [Company.objects.get(id=post['company_id']),])
        company = json.loads(company_serialized)[0]['fields']
        post['name'] = company['name']
        post['ticker'] = company['ticker']
        post['date'] = dateformat.format(post['date'], 'd-m-Y')
        json_object[company['name']] = post

    json_object = json.dumps(json_object)

    return JsonResponse(json_object, safe=False)

def GetAll(request):
    all = Post.objects.filter(date__gte=Now()-timedelta(days=1)).values()

    json_object = {}

    for post in all:
        company_serialized = serializers.serialize('json', [Company.objects.get(id=post['company_id']),])
        company = json.loads(company_serialized)[0]['fields']
        post['name'] = company['name']
        post['ticker'] = company['ticker']
        post['date'] = dateformat.format(post['date'], 'd-m-Y')
        json_object[company['name']] = post

    json_object = json.dumps(json_object)

    return JsonResponse(json_object, safe=False)
    
def GetCompany(request, slug):
    template = loader.get_template('company.html')

    company = Company.objects.get(ticker=slug)
    stock_data = CompanyStockData.objects.filter(company__ticker=slug).order_by('date').first()

    context = {
        'company': company,
        'stock': stock_data,
    }

    return HttpResponse(template.render(context, request))

def getStockData(request, slug):
    print('Starting')
    #get ticker from the AJAX POST request
    ticker = request.POST.get('ticker', 'null')
    ticker = ticker.upper()

    all_data = CompanyStockData.objects.filter(company__ticker=slug).values()
    company = Company.objects.get(ticker=slug)

    stock_data = {}
    sma_data = {}
    company_name = f'{company.name}'

    # Form the data in the correct way to use it for the chart
    for data in all_data:
        date = data['date'].strftime('%m-%d-%Y')
        stock_data[date] = {}
        stock_data[date]['open'] = data['open']
        stock_data[date]['high'] = data['high']
        stock_data[date]['low'] = float(data['low'])
        stock_data[date]['close'] = float(data['close'])
        stock_data[date]['adjusted_close'] = float(data['adjustedClose'])
        sma_data[date] = float(data['sma'])

    #package up the data in an output dictionary 
    context = {
        'name': company_name,
        'sma_data': sma_data,
        'stock_data': stock_data,
    }

    print('Finished')
    #return the data back to the frontend AJAX call 
    return JsonResponse(context, safe=False)