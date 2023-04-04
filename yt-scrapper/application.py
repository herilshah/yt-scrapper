from flask import Flask, request, render_template,jsonify,redirect
from flask_cors import CORS,cross_origin
import requests
import logging
import os
import pymongo
logging.basicConfig(filename="scrapper.log" , level=logging.INFO)
import re
import pandas as pd

application = Flask(__name__)
app=application

@app.route("/")
@cross_origin()
def home():
    return render_template('index.html')

@app.route('/results',methods=['POST','GET'])
@cross_origin()
def scrape_videos():
    video_details=[]
    if request.method=='POST':
        try:

            save_directory='data/'              # all csv files save here
            if not os.path.exists(save_directory):
                os.makedirs(save_directory)

            # ask user channel name to scrape
            search_query=request.form['query'].replace(" ","")
            
            # convert channel name to url
            url=f"https://www.youtube.com/@{search_query}/videos"

            headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0',
                        'Accept-Language': 'en-US,en;q=0.9'
            }

            response=requests.get(url,headers)
            response_docs=response.text

            # scraping video url links with regular expression
            video_links = re.findall(r"watch\?v=[A-Za-z0-9_-]{11}", response_docs)[:5]

            # scraping thumbnail url links with regular expression
            thumbnail_links = re.findall('"thumbnail":{"thumbnails":\[{"url":"https://i.ytimg.com/vi/[A-Za-z0-9_-]{11}/.*?"', response_docs)[:5]

            # scraping video titles with regular expression
            video_titles = re.findall('"title":{"runs":\[{"text":".*?"', response_docs)

            # scraping video views with regular expression
            video_views = re.findall('{"accessibilityData":{"label":"[0-9]{0,5}K views"}}',response_docs)

            # scraping video time of post with regular expression
            posting_timePattern = re.compile('\d+ (minutes|hours|hour|days|day|weeks|week|years|year) ago')
            posting_timeMatch=posting_timePattern.finditer(response_docs)
            posting_time=[]
            for i in posting_timeMatch:
                posting_time.append(i[0])
            final_posting_time=posting_time[0:10:2]

            
            for i in range(len(video_links)):
                try:
                    video_url='https://www.youtube.com/'+video_links[i]
                except:
                    logging.info('video url')
                
                try:
                    thumnail_url=thumbnail_links[i].split('"')[-2].split('?')[-2]
                except:
                    logging.info('thumbnail url')

                try:
                    video_title=video_titles[i].split('"')[-2]
                except:
                    logging.info('title')

                try:
                    views=video_views[i].split('"')[-2]
                except:
                    logging.info('views')
                
                try:
                    video_posting=final_posting_time[i]
                except:
                    logging.info('video posting')
                
                youtube_dict={'video_url':video_url,
                            'thumbnail_url':thumnail_url,
                            'video_title':video_title,
                            'views':views,
                            'video_posting':video_posting}
                video_details.append(youtube_dict)   


            df=pd.DataFrame(video_details)
            df.to_csv(f"{save_directory}{search_query}.csv",index=None)

            # save into the mongodb database
            client = pymongo.MongoClient("mongodb+srv://herilshah:ZKQlyEZ84a04vPwM@cluster0.anyatip.mongodb.net/?retryWrites=true&w=majority")
            db = client['youtube_scraping']
            youtube_coll=db['video_scrape_data']
            youtube_coll.insert_many(video_details)
            
#             return "success"
            
            return render_template('results.html',videos=video_details)

        except Exception as e:
            logging.info(e)
            print('something is wrong')
    else:
        return render_template('index.html')


if __name__=="__main__":
    app.run(host="0.0.0.0")
