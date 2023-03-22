from django.contrib import admin
from .models import Post, Company, CompanyStockData, General

# Register your models here.
# Positive database
class PostListAdmin(admin.ModelAdmin):
    list_display = ('company', 'date', 'post')

admin.site.register(Post, PostListAdmin)

# Medium database
class CompanyListAdmin(admin.ModelAdmin):
    list_display = ('name', 'ticker',)
    prepopulated_fields = {'slug': ['ticker']}

admin.site.register(Company, CompanyListAdmin)

class GeneralListAdmin(admin.ModelAdmin):
    list_display = ('lastUpdated', 'apiCalls')

admin.site.register(General, GeneralListAdmin)

class CompanyStockDataListAdmin(admin.ModelAdmin):
    list_display = ('date', 'company')

admin.site.register(CompanyStockData, CompanyStockDataListAdmin)