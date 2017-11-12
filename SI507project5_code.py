'''IMPORT STATEMENTS'''
import requests_oauthlib
import webbrowser
import json
import secret_tumblr_data # need properly formatted file, see example
from datetime import datetime
import csv

## ADDITIONAL CODE for program should go here...
## Perhaps authentication setup, functions to get and process data, a class definition... etc.
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DEBUG = True

'''CACHING SETUP'''
# Caching constants
CACHE_FNAME = "cache_contents.json"
CREDS_CACHE_FILE = "creds.json"

# Load data cache
try:
    with open(CACHE_FNAME, 'r') as cache_file:
        cache_json = cache_file.read()
        CACHE_DICTION = json.loads(cache_json) # create a python dictionary from the json string pulled from the file...
except:
    CACHE_DICTION = {} # or just make a new cache dictionary

# Load creds cache
try:
    with open(CREDS_CACHE_FILE,'r') as creds_file:
        cache_creds = creds_file.read()
        CREDS_DICTION = json.loads(cache_creds)
except:
    CREDS_DICTION = {}


'''CACHING FUNCTIONS FOR CRED & DATA'''
# cache credentials in one file, "creds.json". Put it all in a function and do it once, so don't have to repeat authentication evry time grab data from tumblr.
def has_cache_expired(timestamp_str, expire_in_days):
    """Check if cache timestamp is over expire_in_days old"""
    # gives current datetime
    now = datetime.now()

    # datetime.strptime converts a formatted string into datetime object
    cache_timestamp = datetime.strptime(timestamp_str, DATETIME_FORMAT)

    # subtracting two datetime objects gives you a timedelta object
    delta = now - cache_timestamp
    delta_in_days = delta.days

    # now that we have days as integers, we can just use comparison
    # and decide if cache has expired or not
    if delta_in_days > expire_in_days:
        return True # It's been longer than expiry time
    else:
        return False

def get_from_cache(identifier, dictionary):
    """If unique identifier exists in specified cache dictionary and has not expired, return the data associated with it from the request, else return None"""
    identifier = identifier.upper() # Assuming none will differ with case sensitivity here
    if identifier in dictionary:
        data_assoc_dict = dictionary[identifier]
        if has_cache_expired(data_assoc_dict['timestamp'],data_assoc_dict["expire_in_days"]):
            if DEBUG:
                print("Cache has expired for {}".format(identifier))
            # also remove old copy from cache
            del dictionary[identifier]
            data = None
        else:
            data = dictionary[identifier]['values']
    else:
        data = None
    return data


def set_in_data_cache(identifier, data, expire_in_days):
    """Add identifier and its associated values (literal data) to the data cache dictionary, and save the whole dictionary to a file as json"""
    identifier = identifier.upper()
    CACHE_DICTION[identifier] = {
        'values': data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT),
        'expire_in_days': expire_in_days
    }

    with open(CACHE_FNAME, 'w') as cache_file:
        cache_json = json.dumps(CACHE_DICTION)
        cache_file.write(cache_json)

def set_in_creds_cache(identifier, data, expire_in_days):
    """Add identifier and its associated values (literal data) to the credentials cache dictionary, and save the whole dictionary to a file as json"""
    identifier = identifier.upper() # make unique
    CREDS_DICTION[identifier] = {
        'values': data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT),
        'expire_in_days': expire_in_days
    }

    with open(CREDS_CACHE_FILE, 'w') as cache_file:
        cache_json = json.dumps(CREDS_DICTION)
        cache_file.write(cache_json)

'''OAUTH1 API CONSTANTS'''
## OAuth1 API Constants - vary by API
### Private data in a hidden secret_tumblr_data.py file
CLIENT_KEY = secret_tumblr_data.client_key
CLIENT_SECRET = secret_tumblr_data.client_secret

### Specific to API URLs, not private. Taken from: https://www.tumblr.com/oauth/apps
REQUEST_TOKEN_URL = "https://www.tumblr.com/oauth/request_token"
BASE_AUTH_URL = "https://www.tumblr.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://www.tumblr.com/oauth/access_token"
REDIRECT_URI = "https://www.programsinformationpeople.org/runestone/oauth"
# A note on Tumblr rate limit: Newly registered consumers are rate limited to 1,000 requests per hour, and 5,000 requests per day.

'''OATH1 FLOW'''
# Alot of these methods from OAuth1 handle a lot of the trickery to access the desired API
# this function does steps 2-5 in OAuth1 flow (see lecture notes)
def get_tokens(client_key=CLIENT_KEY, client_secret=CLIENT_SECRET,request_token_url=REQUEST_TOKEN_URL,base_authorization_url=BASE_AUTH_URL,access_token_url=ACCESS_TOKEN_URL,verifier_auto=False):
    # creates instance of OAuth1Session, upon which we can invoke methods
    oauth_inst = requests_oauthlib.OAuth1Session(client_key,client_secret=client_secret)

    # Use .fetch method that returns a dictionary of credential data
    fetch_response = oauth_inst.fetch_request_token(request_token_url)

    # Using the dictionary .get method in these lines
    resource_owner_key = fetch_response.get('oauth_token') # get value of oauth token
    resource_owner_secret = fetch_response.get('oauth_token_secret') # get value of oauth secret

    # get authentication url. base url is only the first step, because have to pass some parameters through this url (i.e. verifier) to get info back...
    auth_url = oauth_inst.authorization_url(base_authorization_url)
    # Open the auth url in browser so that user can put in their verifier:
    webbrowser.open(auth_url) # For user to interact with & approve access of this app -- this script

    # Deal with required input, which will vary by API
    if verifier_auto: # if the input is default (True), like Tumblr
        verifier = input("Please input the verifier:  ")
    else:
        redirect_result = input("Paste the full redirect URL here:  ")
        oauth_resp = oauth_inst.parse_authorization_response(redirect_result) # returns a dictionary -- you may want to inspect that this works and edit accordingly
        verifier = oauth_resp.get('oauth_verifier')

    # Regenerate instance of oauth1session class with more data
    oauth_inst = requests_oauthlib.OAuth1Session(client_key, client_secret=client_secret, resource_owner_key=resource_owner_key, resource_owner_secret=resource_owner_secret, verifier=verifier)

    oauth_tokens = oauth_inst.fetch_access_token(access_token_url) # returns a dictionary

    # Use that dictionary to get these things
    # Tuple assignment syntax
    resource_owner_key, resource_owner_secret = oauth_tokens.get('oauth_token'), oauth_tokens.get('oauth_token_secret')

    return client_key, client_secret, resource_owner_key, resource_owner_secret, verifier

def get_tokens_from_service(service_name_ident, expire_in_days=7): # Default: 7 days for creds expiration
    creds_data = get_from_cache(service_name_ident, CREDS_DICTION)
    if creds_data:
        if DEBUG:
            print("Loading creds from cache...")
            print()
    else:
        if DEBUG:
            print("Fetching fresh credentials...")
            print("Prepare to log in via browser.")
            print()
        creds_data = get_tokens()
        set_in_creds_cache(service_name_ident, creds_data, expire_in_days=expire_in_days)
    return creds_data

'''REQUESTING DATA'''

def create_request_identifier(url, params_diction):
    sorted_params = sorted(params_diction.items(),key=lambda x:x[0])
    params_str = "_".join([str(e) for l in sorted_params for e in l]) # Make the list of tuples into a flat list using a complex list comprehension
    total_ident = url + "?" + params_str
    return total_ident.upper() # Creating the identifier

def get_data_from_api(request_url,service_ident, params_diction=None, expire_in_days=7):
    """Check in cache, if not found, load data, save in cache and then return that data"""
    ident = create_request_identifier(request_url, params_diction)
    data = get_from_cache(ident,CACHE_DICTION)
    if data:
        if DEBUG:
            print("Loading from data cache: {}... data".format(ident))
    else:
        if DEBUG:
            print("Fetching new data from {}".format(request_url))

        # Get credentials
        client_key, client_secret, resource_owner_key, resource_owner_secret, verifier = get_tokens_from_service(service_ident)

        # Create a new instance of oauth to make a request with
        oauth_inst = requests_oauthlib.OAuth1Session(client_key, client_secret=client_secret,resource_owner_key=resource_owner_key,resource_owner_secret=resource_owner_secret)
        # Call the get method on oauth instance
        # Work of encoding and "signing" the request happens behind the sences, thanks to the OAuth1Session instance in oauth_inst
        resp = oauth_inst.get(request_url,params=params_diction)
        # Get the string data and set it in the cache for next time
        data_str = resp.text
        data = json.loads(data_str)
        set_in_data_cache(ident, data, expire_in_days)
    return data

'''INVOKING FUNCTIONS'''
if not CLIENT_KEY or not CLIENT_SECRET:
    print("You need to fill in client_key and client_secret in the secret_data.py file.")
    exit()
if not REQUEST_TOKEN_URL or not BASE_AUTH_URL:
    print("You need to fill in this API's specific OAuth2 URLs in this file.")
    exit()

# Invoke functions -- this is where use specific Tumblr methods: https://www.tumblr.com/docs/en/api/v2#auth
blog_identifier = "julieoncruise.tumblr.com/"

# /info = Retrieve high-level blog info:
tumblr_info_baseurl = "https://api.tumblr.com/v2/blog/julieoncruise.tumblr.com/info"
tumblr_info_params = {
"blog-identifier":blog_identifier,
"api_key":CLIENT_KEY,
}
tumblr_result_info = get_data_from_api(tumblr_info_baseurl,"Tumblr",tumblr_info_params) # Default expire_in_days
# print(type(tumblr_result))


# /following = list of blogs followed
tumblr_following_baseurl = "https://api.tumblr.com/v2/blog/julieoncruise.tumblr.com/following"
tumbr_following_params = {}
tumblr_result_following = get_data_from_api(tumblr_following_baseurl,"Tumblr",tumbr_following_params)
tumblr_blogs = tumblr_result_following["response"]["blogs"]
# print(tumblr_result_following.keys())
# for b in tumblr_blogs:
#     print (b)
# print(type(tumblr_blogs))

# /tags = get posts with a tag
tumblr_tag_baseurl = "https://api.tumblr.com/v2/tagged"
tumblr_tag_params = {
"tag":"social justice",
"limit":20
}
tumblr_result_tags = get_data_from_api(tumblr_tag_baseurl,"Tumblr",tumblr_tag_params)
tumblr_tags = tumblr_result_tags["response"]
# for t in tumblr_tags:
#     print(t)
# print(tumblr_result_tags.keys())
# print(type(tumblr_result_tags))

'''CREATING CLASSES'''
class TumblrBlog(object):
    def __init__(self,blog_data):
        try:
            self.name = blog_data["name"]
            self.title = blog_data["title"]
            self.description = blog_data["description"]
            self.url = blog_data["url"]
        except:
            self.name = ""
            self.title = ""
            self.description = ""
            self.url = ""

class TumblrTag(object):
    def __init__(self,tag_data):
        try:
            self.type = tag_data["type"]
            self.blog_name = tag_data["blog_name"]
            self.url = tag_data["post_url"]
            self.id = tag_data["id"]
            self.related_tags = tag_data["tags"]
        except:
            self.type = ""
            self.blog_name = ""
            self.url = ""
            self.id = None
            self.related_tags = []


'''CREATING CSV FILES'''
## Make sure to run your code and write CSV files by the end of the program.
blog_objects = [TumblrBlog(b) for b in tumblr_blogs]
tag_objects = [TumblrTag(t) for t in tumblr_tags]
# print (blog_objects)
# print (blog_objects[0].name,blog_objects[0].title,blog_objects[0].description,blog_objects[0].url)
# print(tag_objects)
# print(tag_objects[0].type,tag_objects[0].blog_name,tag_objects[0].url,tag_objects[0].id,tag_objects[0].related_tags)

with open("social_justice_blogs.csv", 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Blog Name','Type','URL','Blog ID','Related Tags'])
    for t in tag_objects:
        writer.writerow([t.blog_name,t.type,t.url,t.id,t.related_tags])

with open("tumblr_blogs_followed.csv", 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Blog Name','Title','Description','URL'])
    for b in blog_objects:
        writer.writerow([b.name,b.title,b.description,b.url])
