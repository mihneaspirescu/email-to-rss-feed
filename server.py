from flask import Flask
from flask import jsonify
from flask import request
import hashlib

from rfeed import *

try:
    from urllib.parse import urlparse
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urlparse
from werkzeug.contrib.atom import AtomFeed
import datetime

from bs4 import BeautifulSoup

app = Flask(__name__)

# all news DB
allnews = {}


def merge_two_dicts(x, y):
    z = x.copy()  # start with x's keys and values
    z.update(y)  # modifies z with y's keys and values & returns None
    return z


def captureContent(tr):
    h1 = tr.findAll('h1')
    titles = [' '.join(x.span.get_text().split()) for x in h1]

    content_raw = tr.findAll('p')
    content = [' '.join(x.span.get_text().split()) for x in content_raw if ' '.join(x.span.get_text().split()) != '']

    link = tr.find('a')

    return titles, content, link


def captureText(tables):
    news11 = {}
    news13 = {}
    trs11 = tables[11].findAll('tr')
    trs13 = tables[13].findAll('tr')

    for tr in trs13:
        titles, content, link = captureContent(tr)
        if len(titles) != 0 and len(content) != 0:
            hash_object = hashlib.md5((str(titles[0]) + str(content) + str(link.get('href'))).encode())
            news13[hash_object.hexdigest()] = (titles[0], content, link.get('href'))

    for tr in trs11:
        titles, content, link = captureContent(tr)
        if len(titles) != 0 and len(content) != 0:
            hash_object = hashlib.md5((str(titles[0]) + str(content) + str(link.get('href'))).encode())
            print(hash_object.hexdigest())

            news11[hash_object.hexdigest()] = (titles[0], content, link.get('href'))

    if len(news11) != 0:
        print(news11.items())
        return news11
    else:
        print(news13.items())
        return news13


def make_external(url):
    return urljoin(request.url_root, "http://google.com")


def split_list(alist, wanted_parts=1):
    length = len(alist)
    return [alist[i * length // wanted_parts: (i + 1) * length // wanted_parts]
            for i in range(wanted_parts)]


def save_data(content):
    count = 0
    count_added = 0

    content = content.decode("utf-8")
    mystring = content.replace('\n', ' ').replace('\r', '').replace('\t', '')
    soup = BeautifulSoup(mystring, "lxml")

    tables = soup.find_all('table')

    for id, data in captureText(tables).items():
        if id not in allnews:
            allnews[id] = (
            data[0], '\n'.join(data[1][:-2]), data[1][len(data[1]) - 2][8:], data[2], datetime.datetime.today())
            count_added += 1
        else:
            count += 1

    return count, count_added


@app.route('/update', methods=['POST'])
def update_feed():
    count, count_added = save_data(request.data)
    return jsonify({"success": True, "added": count_added, "duplicates": count})


@app.route('/testfeed')
def test_feed():
    item1 = Item(
        title="First article",
        link="http://www.example.com/articles/1",
        description="This is the description of the first article",
        author="Santiago L. Valdarrama",
        guid=Guid("http://www.example.com/articles/1"),
        pubDate=datetime.datetime(2014, 12, 29, 10, 00))

    item2 = Item(
        title="Second article",
        link="http://www.example.com/articles/2",
        description="This is the description of the second article",
        author="Santiago L. Valdarrama",
        guid=Guid("http://www.example.com/articles/2"),
        pubDate=datetime.datetime(2014, 12, 30, 14, 15))

    feed = Feed(
        title="Sample RSS Feed",
        link="http://www.example.com/rss",
        description="This is an example of how to use rfeed to generate an RSS 2.0 feed",
        language="en-US",
        lastBuildDate=datetime.datetime.now(),
        items=[item1, item2])
    return feed.rss()


@app.route('/')
def recent_feed():
    feed = AtomFeed('Recent Articles',
                    feed_url=request.url, url=request.url_root)

    print(allnews.values())
    # for each line in the table
    for i in allnews.values():
        # getting the identifier


        feed.add(i[0].encode('ascii', 'ignore').decode('ascii'), i[1].encode('ascii', 'ignore').decode('ascii'),
                 content_type='html',
                 author=i[2],
                 url=make_external(i[3]),
                 updated=i[4]
                 )

    return feed.get_response()
