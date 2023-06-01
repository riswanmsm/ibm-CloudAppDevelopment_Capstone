import requests
import json
# import related models here
from .models import CarDealer, DealerReview
from requests.auth import HTTPBasicAuth
from ibm_watson.natural_language_understanding_v1 import Features, SentimentOptions
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from datetime import datetime


def get_request(url, **kwargs):

    try:
        # call get method of requests library with URL and parameters
        response = requests.get(
            url, headers={'Content-Type': 'application/json'}, params=kwargs)

        status_code = response.status_code
        print('With status {}'.format(status_code))
        json_data = json.loads(response.text)
        return json_data
    except:
        print('Network exception occured while get dealerships')


# Create a `post_request` to make HTTP POST requests
# e.g., response = requests.post(url, params=kwargs, json=payload)
def post_request(url, json_payload, **kwargs):

    print(f'post to {url}')
    # requests.post(url, params=kwargs, json=json_payload)
    # try:
    response = requests.post(
        url, params=kwargs, json=json_payload)
    return response
    # except:
    #     print('there is an error while posting review')


# Create a get_dealers_from_cf method to get dealers from a cloud function
def get_dealers_from_cf(url, **kwargs):
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url)
    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result["result"]
        # For each dealer object
        for dealer in dealers:
            # Get its content in `doc` object
            dealer_doc = dealer
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"], full_name=dealer_doc["full_name"],
                                   id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"],
                                   short_name=dealer_doc["short_name"],
                                   st=dealer_doc["st"], zip=dealer_doc["zip"])
            results.append(dealer_obj)
    return results


def get_dealers_by_id(url, **kwargs):

    # Call get_request with a URL parameter
    print('get_dealers_by_id ======')
    json_result = get_request(url, **kwargs)
    if json_result:
        # Get the row list in JSON as dealers
        dealer = json_result["result"][0]
        # For each dealer object
        # print(dealer)
        dealer_obj = CarDealer(address=dealer["address"], city=dealer["city"], full_name=dealer["full_name"],
                               id=dealer["id"], lat=dealer["lat"], long=dealer["long"],
                               short_name=dealer["short_name"],
                               st=dealer["st"], zip=dealer["zip"])
        print(dealer_obj)
        return dealer_obj


def get_dealers_by_state(url, **kwargs):
    results = []
    # Call get_request with a URL parameter
    print('get_dealers_by_state ======')
    json_result = get_request(url, **kwargs)
    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result["result"]
        # For each dealer object
        for dealer in dealers:
            # Get its content in `doc` object
            dealer_doc = dealer
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"], full_name=dealer_doc["full_name"],
                                   id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"],
                                   short_name=dealer_doc["short_name"],
                                   st=dealer_doc["st"], zip=dealer_doc["zip"])
            results.append(dealer_obj)
    return results


# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
def get_dealer_reviews_from_cf(url, **kwargs):
    print('get_dealer_reviews_from_cf')
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url, **kwargs)

    # print(json_result)
    if 'body' in json_result.keys():
        # Get the row list in JSON as reviews
        # print(json_result)
        reviews = json_result["body"]["data"]
        print(reviews[0]["dealership"])
        # For each dealer object
        for review in reviews:
            # Get its content in `doc` object
            # dealer_doc = dealer
            # Create a CarDealer object with values in `doc` object
            dealer_review_obj = DealerReview(dealership=review["dealership"], name=review["name"],
                                             purchase=review["purchase"], review=review["review"],
                                             purchase_date=review["purchase_date"] if "purchase_date" in review else datetime.utcnow(
            ).isoformat(),
                car_make=review["car_make"], car_model=review["car_model"],
                car_year=review["car_year"], sentiment='', id=review["id"])
            # appending the response from IBM NLU to the sentiment property of dealer object
            dealer_review_obj.sentiment = analyze_review_sentiments(
                dealer_review_obj.review)
            results.append(dealer_review_obj)
    else:
        results = ''

    return results

# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text


def analyze_review_sentiments(review_text):
    NLU_API_KEY = 'oL91GSc8-OOA6APvU0QvjSaWmF4RKoHW3psVlSzEmEkv'
    URL = 'https://api.au-syd.natural-language-understanding.watson.cloud.ibm.com/instances/1cd71557-8376-4aa7-93fa-4654ed312b81'
    sentiment_label = 'neutral'

    version = '2021-08-01'
    authenticator = IAMAuthenticator(NLU_API_KEY)
    nlu = NaturalLanguageUnderstandingV1(
        version=version, authenticator=authenticator)
    nlu.set_service_url(URL)

    # get sentiment of the review
    try:
        response = nlu.analyze(text=review_text, features=Features(
            sentiment=SentimentOptions())).get_result()
        print(json.dumps(response))
        # sentiment_score = str(response["sentiment"]["document"]["score"])
        sentiment_label = response["sentiment"]["document"]["label"]
    except:
        print("Review is too short for sentiment analysis. Assigning default sentiment value 'neutral' instead")
        sentiment_label = "neutral"

    # print(sentiment_score)
    # print(sentiment_label)

    return sentiment_label
