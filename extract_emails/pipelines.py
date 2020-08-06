# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
import shutil

class ExtractEmailsPipeline(object):
    def open_spider(self, spider):
        if os.path.isfile('guestpostscraper.csv'):
            os.remove('guestpostscraper.csv')
        if os.path.isfile('get_emails.csv'):
            os.remove('get_emails.csv')

    def process_item(self, item, spider):
        return item

    def close_spider(self, spider):
        if os.path.isfile('guestpostscraper.csv'):
            shutil.copyfile('guestpostscraper.csv', 'guestpostscraper.out.csv')
        if os.path.isfile('get_emails.csv'):
            shutil.copyfile('get_emails.csv', 'get_emails.out.csv')