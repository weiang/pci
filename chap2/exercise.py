#!/usr/bin/env python
# -*- encoding=utf-8 -*-

from recommendations import *
from pydelicious import *
import time

def initializeTagDict(tags, count=5):
    tag_dict = {}

    posts = []
    for tag in tags:
        for i in range(5):
            try:    
                posts = get_popular(tag=tag)
                posts = posts[0:count]
                break
            except:
                print "Failed tag " + tag + ", retrying"
                time.sleep(2)

        for p1 in posts:
            tag = p1['tags']
            tag_dict[tag] = {}

    for tag in tag_dict:
        print "Tag: %s" %(tag)
    return tag_dict

def fillTags(tag_dict):
    all_urls = {}

    posts = []
    for tag in tag_dict:
        for i in range(5):
            try:
                posts = get_popular(tag=tag)
                break
            except:
                print "Failed tag " + tag + ", retrying"
                time.sleep(2)
        for post in posts:
            url = post['url']
            tag_dict[tag][url] = 1.0
            all_urls[url] = 1

    for url in all_urls:
        for tag in tag_dict:
            if url not in tag_dict[tag]:
                tag_dict[tag][url] = .0

def exercise2():
    tag1 = 'programming'
    tags = [tag1, "language", "c++", "code"]
    tag_dict = initializeTagDict(tags)
    fillTags(tag_dict)
    print topMatches(tag_dict, tag1) 
    print getRecommendations(tag_dict, tag1)

if __name__ == '__main__':
    exercise2()
