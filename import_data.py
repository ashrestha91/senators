import requests
import time
import sys

from collections import defaultdict
from pymongo import MongoClient

client = MongoClient()
db = client["senators"]
coll = db["raw_xml"]

def try_request(url, retries=0):
    if retries == 10:
        print url
    if retries > 15:
        print url
        return None
    req = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:39.0) Gecko/20100101 Firefox/39.0'
        })
    try:
        etree.fromstring(req.content)
        return req.content
    except:
        time.sleep(retries)
        return try_request(url, retries+1)

# Load senate data

for cong in range(101,115):
    for sess in range(1,3):
        root = etree.fromstring(try_request("http://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_{}_{}.xml".format(cong, sess)))

        for vote_num in root.xpath("votes/vote/vote_number"):
            if not coll.find_one({"congress": cong, "session": sess, "vote_num": vote_num.text}):
                print cong, sess, vote_num.text
                sys.stdout.flush()

                raw_xml = try_request("http://www.senate.gov/legislative/LIS/roll_call_votes/vote{cong}{sess}/vote_{cong}_{sess}_{vote_num}.xml".format(cong=cong, sess=sess, vote_num=vote_num.text))
                roll_call_vote = etree.fromstring(raw_xml)
                member_votes = []
                for member in roll_call_vote.xpath("members/member"):
                    name = member.find("member_full").text
                    vote = member.find("vote_cast").text
                    if vote=='Yea':
                        vote_score = 1
                    elif vote=='Nay':
                        vote_score = -1
                    else:
                        vote_score = 0
                    member_votes.append({ 
                            "name": name,
                            "vote_cast": vote,
                            "vote_score": vote_score
                        })
                coll.insert_one({
                            "raw": raw_xml,
                            "congress": cong,
                            "session": sess,
                            "vote_num": vote_num.text,
                            "votes": member_votes
                    })
