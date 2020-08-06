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
        
        self.client = pymongo.MongoClient('mongodb+srv://admin-amit:test1234@cluster0-thgjr.mongodb.net/email_db?retryWrites=true&w=majority')
        self.db = self.client["email_db"]

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