import datetime
import os
import pymongo
import shutil

class ExtractEmailsPipeline(object):
    collection_name = ""
    def open_spider(self, spider):
        if spider.name == 'get_emails':
            if os.path.isfile('get_emails.csv'):
                os.remove('get_emails.csv')
                print("==================== removing csv file and creating one ======================")
            self.collection_name = 'get_email'

        if spider.name == 'guestpostscraper':
            if os.path.isfile('guestpostscraper.csv'):
                os.remove('guestpostscraper.csv')
            self.collection_name = 'scraper_db'

            
        print("=============================================collection name", self.collection_name)
        # PRODUCTION DB INFO
        self.client = pymongo.MongoClient("mongodb+srv://nayeem:imunbd990@cluster0.vh1iq.mongodb.net/scraper_db?retryWrites=true&w=majority")
        print("Connecting database to -------------------------------", self.collection_name)
        self.db = self.client[self.collection_name]
        
        # DEVELOPMENT ENV DB INFO
        # self.client = pymongo.MongoClient('mongodb://localhost:27017')
        # self.db = self.client["scraper_db"]


    def process_item(self, item, spider):
        if spider.name == 'get_emails':
            if item['email'] != 'NA':
                if item['da'] == 'NA':
                    print(f'ERROR: Skipping db insertion because DA for {item["website"]} was not found')
                elif item['pa'] == 'NA':
                    print(f'ERROR: Skipping db insertion because PA for {item["website"]} was not found')
                elif item['cf'] == 'NA':
                    print(f'ERROR: Skipping db insertion because CF for {item["website"]} was not found')
                elif item['tf'] == 'NA':
                    print(f'ERROR: Skipping db insertion because TF for {item["website"]} was not found')
                else:
                    # print(f'get_emails db Insert --------------->>>>>>---------> {item}')
                    self.db[self.collection_name].update_one(
                        {"url": item["url"]}, {"$set": item}, upsert=True
                    )
            else:
                print(f'ERROR: Skipping db insertion because no email was not found for {item["website"]}')

        # if the spider is guestpostscraper then insert to gostpostscraper mongodb
        else:
            print(f'guestpostscraper bb Insert -> {item}')
            self.db[self.collection_name].update_one(
                {"website_url": item["website_url"]}, {"$set": item}, upsert=True
            )
        return item





    def close_spider(self, spider):
        if spider.name == 'get_emails':
            if os.path.isfile('get_emails.csv'):
                shutil.copyfile('get_emails.csv', 'get_emails.out.csv')
        
        if spider.name == 'guestpostscraper':
            if os.path.isfile('guestpostscraper.csv'):
                print("YOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO+==============================")
                shutil.copyfile('guestpostscraper.csv', 'guestpostscraper.out.csv')
        self.client.close()