# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
import pymongo
import shutil

class ExtractEmailsPipeline(object):
    collection_name = ""

    def open_spider(self, spider):
        if spider.name == 'guestpostscraper':
            if os.path.isfile('guestpostscraper.csv'):
                os.remove('guestpostscraper.csv')
            self.collection_name = 'urls'
            
        if spider.name == 'get_emails':
            if os.path.isfile('get_emails.csv'):
                os.remove('get_emails.csv')
            self.collection_name = 'emails'
        
        # PRODUCTION DB INFO
        # mongodb+srv://admin-santhej:<password>@cluster0.3dv1a.mongodb.net/<dbname>?retryWrites=true&w=majority
        self.client = pymongo.MongoClient('mongodb+srv://admin-santhej:test1234@cluster0.3dv1a.mongodb.net/retryWrites=true&w=majority')

        # DEVELOPMENT ENV DB INFO
        # self.client = pymongo.MongoClient('mongodb://localhost:27017')
        self.db = self.client["scraper_db"]

    def process_item(self, item, spider):
        self.db[self.collection_name].insert(item)
        return item

    def close_spider(self, spider):
        if spider.name == 'guestpostscraper':
            if os.path.isfile('guestpostscraper.csv'):
                shutil.copyfile('guestpostscraper.csv', 'guestpostscraper.out.csv')
        
        if spider.name == 'get_emails':
            if os.path.isfile('get_emails.csv'):
                shutil.copyfile('get_emails.csv', 'get_emails.out.csv')
        
        self.client.close()