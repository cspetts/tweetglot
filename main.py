import logging
import tweepy
import os
import webbrowser
import json
import re

from datetime import datetime
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0

log = logging.getLogger('tweetglot')
log.setLevel(logging.DEBUG)

log_dir = 'log'
log_filename = 'tweetglot.log.%s' % datetime.now().strftime("%Y%m%d_%H")
log_format = logging.Formatter("%(asctime)s %(levelname)s %(message)s",
                              "%Y-%m-%d %H:%M:%S")

fh = logging.FileHandler(os.path.join(log_dir,log_filename))
fh.setLevel(logging.DEBUG)
fh.setFormatter(log_format)
log.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(log_format)
log.addHandler(ch)

log.info("Initialising...")

twitter_keys = {}
for line in open(".keys", "r").read().splitlines():
    line = line.split(":")
    twitter_keys[line[0]] = line[1]

lang_codes = {}
for line in open("language_codes/lang-codes.csv", "r").read().splitlines():
    line = line.split(",")
    lang_codes[line[0]] = line[1]

log.debug("Creating auth object: %s / %s" % (twitter_keys.get('api_key'),
                                             twitter_keys.get('api_key_secret')))
# Authenticate to Twitter
auth = tweepy.OAuthHandler(twitter_keys.get('api_key'),
                           twitter_keys.get('api_key_secret'))

if(os.path.isfile('.tokens')):
    for line in open(".tokens", "r").read().splitlines():
        line = line.split(":")
        auth.set_access_token(line[0], line[1])
else:
    log.debug("Attempting to get callback url..")
    try:
        redirect_url = auth.get_authorization_url()
    except Exception as msg:
        log.error('Failed to get request token - %s' % str(msg))

    if(redirect_url):
        log.debug("Got redirect URL: %s" % redirect_url)
        webbrowser.open(redirect_url, new=2)
    user_pin = input("Verification PIN: ")

    try: 
        auth.get_access_token(user_pin)
    except Exception as msg:
        log.error('Failed to get access token - %s' % str(msg))

    log.debug('Got access token: %s / %s' % (auth.access_token,
                                            auth.access_token_secret))
    open('.tokens', 'w').write("%s:%s" % (auth.access_token,
                                          auth.access_token_secret))

log.info('Successfully set up tweetglot')

api = tweepy.API(auth)

resp = api.home_timeline(
    count=100,
    include_rts='false'
)

i = 0
errs = 0
langs = {}
for tweet in resp:
    try:
        content = tweet.text.lower()
        content = re.sub('http[^\s]+', '', content)
        content = re.sub('(@|#)[^\s]+', '', content)

        if len(content) > 25:
            lang = detect(content)
            langs[lang] = langs.get(lang, 0) + 1
            
            log.debug("Detected langauge - [%s] %s" % (lang, lang_codes[lang]))
            log.debug("Tweet             - %s" % content)
            log.debug("-------------------")
        else:
            log.error("Tweet too short: %s" % content)
            errs = errs + 1
    except Exception as msg:
        log.error("Unable to detect language: %s" % str(msg))
        errs = errs + 1
    i = i+1

log.info("Analysis of %s tweets (%i errors):\n\n" % (i, errs))

for lang in langs.keys():
    log.info("[%s] %s : %s" % (lang, lang_codes[lang], langs[lang]))