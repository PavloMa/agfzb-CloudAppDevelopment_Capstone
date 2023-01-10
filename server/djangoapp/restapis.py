import requests
import json
# import related models here
from .models import CarDealer
from .models import DealerReview
from requests.auth import HTTPBasicAuth
from requests import Response

from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, EntitiesOptions, KeywordsOptions, SentimentOptions

# Create a `get_request` to make HTTP GET requests
# e.g., response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
#                                     auth=HTTPBasicAuth('apikey', api_key))
def get_request(url, **kwargs):
    print(kwargs)
    print("GET from {} ".format(url))
    response = Response()
    try:
        # Call get method of requests library with URL and parameters
        # response = requests.get(url, headers={'Content-Type': 'application/json'},
        #                             params=kwargs)
        #if api_key:
        #response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
        #                            auth=HTTPBasicAuth('apikey', api_key))
        #else:
        #    print("Short request")
        response = requests.get(url, params=kwargs, headers={'Content-Type': 'application/json'})

        status_code = response.status_code
        print("With status {} ".format(status_code))
        json_data = json.loads(response.text)
        print(json_data)
        return json_data
    except:
        # If any error occurs
        print("Network exception occurred")
        status_code = response.status_code
        print("With status {} ".format(status_code))

# Create a `post_request` to make HTTP POST requests
# e.g., response = requests.post(url, params=kwargs, json=payload)
def post_request(url, payload, **kwargs):
    print(kwargs)
    print("POST to {} ".format(url))
    print(payload)
    
    response = requests.post(url, params=kwargs, json=payload)
    status_code = response.status_code
    print("With status {} ".format(status_code))
    json_data = json.loads(response.text)
    return json_data

# Create a get_dealers_from_cf method to get dealers from a cloud function
# def get_dealers_from_cf(url, **kwargs):
# - Call get_request() with specified arguments
# - Parse JSON results into a CarDealer object list
def get_dealers_from_cf(url, **kwargs):
    results = []
    state = kwargs.get("state")
    if state:
        json_result = get_request(url, state=state)
    else:
        json_result = get_request(url)

    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result
        # For each dealer object
        for dealer in dealers:
            # Get its content in `doc` object
            dealer_doc = dealer["doc"]
            
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"],
                                   id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"], full_name=dealer_doc["full_name"],
                                
                                   st=dealer_doc["st"], zip=dealer_doc["zip"], short_name=dealer_doc["short_name"])
            results.append(dealer_obj)

    return results

# Create a get_dealers_from_cf method to get dealers from a cloud function
def get_dealer_by_id_from_cf(url, id):
    results = []

    # Call get_request with a URL parameter
    json_result = get_request(url, id=id)
    # print("JSON result: " + json_result)

    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result # a list of dealers with the same id
        # print(dealers,"75")

        # For each dealer object
        for dealer in dealers:
            # Get its content in `doc` object
            dealer_doc = dealer
            if dealer_doc["id"] == id:
                # Create a CarDealer object with values in `doc` object
                dealer_obj = CarDealer(address=dealer_doc["address"], 
                                       city=dealer_doc["city"], 
                                       full_name=dealer_doc["full_name"],
                                       id=dealer_doc["id"], 
                                       lat=dealer_doc["lat"], 
                                       long=dealer_doc["long"],
                                       short_name=dealer_doc["short_name"],
                                       st=dealer_doc["st"], 
                                       zip=dealer_doc["zip"])                    
                results.append(dealer_obj)

    return results[0]


# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
# def get_dealer_by_id_from_cf(url, dealerId):
# - Call get_request() with specified arguments
# - Parse JSON results into a DealerView object list
"""
DB Format:
{
 "id": "3893752c232f3c3c54c7775da8bd85f9",
 "key": "3893752c232f3c3c54c7775da8bd85f9",
 "value": {
  "rev": "1-7031cb847c7749341bc32966bf6d577e"
 },
 "doc": {
  "_id": "3893752c232f3c3c54c7775da8bd85f9",
  "_rev": "1-7031cb847c7749341bc32966bf6d577e",
  "another": "field",
  "car_make": "Audi",
  "car_model": "Car",
  "car_year": 2021,
  "dealership": 15,
  "id": 1114,
  "name": "Upkar Lidder",
  "purchase": false,
  "purchase_date": "02/16/2021",
  "review": "Great service!"
 }
}
"""
def get_dealer_reviews_from_cf(url, **kwargs):
    results = []
    id = kwargs.get("id")
    if id: # if it is defined
        json_result = get_request(url, id=id)
    else:
        json_result = get_request(url)
    #print(json_result, "1")
    if json_result:
        reviews = json_result["data"]["docs"]
        for dealer_review in reviews:
            review_obj = DealerReview(dealership=dealer_review["dealership"],
                                   name=dealer_review["name"],
                                   purchase=dealer_review["purchase"],
                                   review=dealer_review["review"])
            if "id" in dealer_review:
                review_obj.id = dealer_review["id"]
            if "purchase_date" in dealer_review:
                review_obj.purchase_date = dealer_review["purchase_date"]
            if "car_make" in dealer_review:
                review_obj.car_make = dealer_review["car_make"]
            if "car_model" in dealer_review:
                review_obj.car_model = dealer_review["car_model"]
            if "car_year" in dealer_review:
                review_obj.car_year = dealer_review["car_year"]
            
            sentiment = analyze_review_sentiments(review_obj.review)
            #print(sentiment)
            review_obj.sentiment = sentiment
            results.append(review_obj)

    return results


# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
# def analyze_review_sentiments(text):
# - Call get_request() with specified arguments
# - Get the returned sentiment label such as Positive or Negative
def analyze_review_sentiments(review):
    url = "https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/398d79bf-092a-4be1-9820-137d6dbfceba"
    api_key = "q-oW38vxNxVYDBwXay3bk5pE6jQtLYTGIqBKoQg75huU"
    
    authenticator = IAMAuthenticator(api_key)
    natural_language_understanding = NaturalLanguageUnderstandingV1(version='2021-08-01', authenticator=authenticator)
    natural_language_understanding.set_service_url(url)
    
    response = natural_language_understanding.analyze(text=review + ". " + review, features=Features(sentiment=SentimentOptions(targets=[review + ". " + review]))).get_result()
    # label=json.dumps(response, indent=2)
    label = response['sentiment']['document']['label']
       
    return(label)

# add_review view method:
#def add_review(review):
#added in views.py

