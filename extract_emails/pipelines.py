import datetime
import os
import pymongo
import shutil

class ExtractEmailsPipeline(object):
    collection_name = ""
    
    def open_spider(self, spider):
        # if spider.name == 'get_emails':
        #     if os.path.isfile('get_emails.csv'):
        #         os.remove('get_emails.csv')
        #         print("==================== removing csv file and creating one ======================")
        #     # self.collection_name = 'get_email'

        # if spider.name == 'guestpostscraper':
        #     if os.path.isfile('guestpostscraper.csv'):
        #         os.remove('guestpostscraper.csv')
            # self.collection_name = 'scraper_db'
        self.client = pymongo.MongoClient("mongodb+srv://nayeem:imunbd990@cluster0.vh1iq.mongodb.net/bloggerhit?retryWrites=true&w=majority")
        # self.client = pymongo.MongoClient("mongodb+srv://admin-santhej:2&fX#zF9JzG$@cluster0.3dv1a.mongodb.net/scraper_db?retryWrites=true&w=majority")
                                         # mongodb+srv://admin-santhej:2&fX#zF9JzG$@cluster0.3dv1a.mongodb.net/myFirstDatabase?retryWrites=true&w=majority


       

    def process_item(self, item, spider):
        self.db = self.client[str(item["user"])]
        
        print()
        # print("THIS IS THE ITEMM ", item)
       

        if spider.name == 'get_emails':
            if item['email'] != 'NA':
                if item['da'] == 'NA':
                    print()
                    print(f' >>>>>>>>> DA for {item["website"]} was not found')
                elif item['pa'] == 'NA':
                    print()
                    print(f' >>>>>>>>> PA for {item["website"]} was not found')
                elif item['cf'] == 'NA':
                    print()
                    print(f' >>>>>>>>> CF for {item["website"]} was not found')
                elif item['tf'] == 'NA':
                    print()
                    print(f' >>>>>>>>> TF for {item["website"]} was not found')
                else:
                    print("Err")
                    print(f'get_emails db Insert --------------->>>--------->--------------->>>>>>--------->--------------->>>>>>---------> {item}')
                    self.db[str(item["report_title"])].update_one({"url": item["url"]}, {"$set": item}, upsert=True)

            else:
                print()
                print(f'ERROR: Skipping db insertion because no email was not found for {item["website"]}')
        
        else:
            print(f'guestpostscraper bb Insert -> {item}')
            print()
            self.db[str(item["report_title"])].update_one({"website_url": item["website_url"]}, {"$set": item}, upsert=True)
        return item




    def close_spider(self, spider):
        # if spider.name == 'get_emails':
        #     if os.path.isfile('get_emails.csv'):
        #         shutil.copyfile('get_emails.csv', 'get_emails.out.csv')
        #         print("YOOOOOOOOOOOOOOO get email OOOOOOOOOOOOOOOOOOOOOOOOOOO+==============================")
        
        # if spider.name == 'guestpostscraper':
        #     if os.path.isfile('guestpostscraper.csv'):
        #         print("YOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO+==============================")
        #         shutil.copyfile('guestpostscraper.csv', 'guestpostscraper.out.csv')
        self.client.close()