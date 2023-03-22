from django.db import models

# Create your models here.
class Company(models.Model):
    name = models.CharField(max_length=255)
    ticker = models.CharField(max_length=10)
    description = models.TextField(null=False)
    sector = models.CharField(max_length=255)
    industry = models.CharField(max_length=500)
    equity = models.CharField(max_length=50)
    debt = models.CharField(max_length=50)
    returnOnEquity = models.DecimalField(decimal_places=4, max_digits=7)
    beta = models.DecimalField(decimal_places=4, max_digits=6)
    value = models.CharField(max_length=50)
    dividendPerShare = models.DecimalField(decimal_places=4, max_digits=7)
    lastModified = models.DateTimeField()
    slug = models.SlugField(default="", null=False)

    def __str__(self):
        return f'{self.name}'

class Post(models.Model):
    POS = 'positive'
    NEUT = 'neutral'
    NEG = 'negative'

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    date = models.DateField()
    post = models.CharField(max_length=500)
    sentiment = models.CharField(max_length=10, 
                            choices=((POS, 'positive'), (NEUT, 'neutral'), (NEG, 'negative')))
    
class General(models.Model):
    lastUpdated = models.DateTimeField()
    apiCalls = models.IntegerField()
    
class CompanyStockData(models.Model):
    DAY = 'daily'
    SMIN = '60 minutes'
    FTMIN = '15 minutes'
    FMIN = '5 minutes'
    OMIN = '1 minute'

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    date = models.DateTimeField()
    open = models.DecimalField(decimal_places=4,max_digits=8)
    high = models.DecimalField(decimal_places=4,max_digits=8)
    low = models.DecimalField(decimal_places=4,max_digits=8)
    close = models.DecimalField(decimal_places=4,max_digits=8)
    adjustedClose = models.DecimalField(decimal_places=4,max_digits=8)
    sma = models.DecimalField(decimal_places=4,max_digits=8)
    interval = models.CharField(max_length=10, choices=((DAY, 'daily'), (SMIN, '60 minutes'), (FTMIN, '15 minutes'), (FMIN, '5 minutes'), (OMIN, '1 minute')))
    