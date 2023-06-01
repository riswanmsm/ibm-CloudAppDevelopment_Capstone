from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarModel, CarDealer
from .restapis import get_dealers_by_id, get_dealers_by_state, get_dealers_from_cf, get_dealer_reviews_from_cf, post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/about.html', context)

# Create a `contact` view to return a static contact page


def contact(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/contact.html', context)

# Create a `login_request` view to handle sign in request


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'djangoapp/user_login_bootstrap.html', context)
    else:
        return render(request, 'djangoapp/user_login_bootstrap.html', context)

# Create a `logout_request` view to handle sign out request


def logout_request(request):
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("djangoapp:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships


def get_dealerships(request):
    context = {}
    if request.method == "GET":
        URL = 'https://us-south.functions.appdomain.cloud/api/v1/web/751c0cc7-acd5-4f8c-b8a8-0c4b0c8d7662/api/dealership.json'
        # Get dealers from the cloudant URL through defined function in restapi
        dealership = get_dealers_from_cf(URL, dealerId=1)
        # Concat all dealers short names
        context['dealership_list'] = dealership
        # dealer_names = ' '.join([dealer.short_name for dealer in dealership])
        # Return a list fo dealers short name
        # return HttpResponse(dealer_names)
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id, dealer_name):
    if request.method == 'GET':
        context = {}
        context['dealer_name'] = dealer_name
        context['dealer_id'] = dealer_id
        URL = 'https://us-south.functions.appdomain.cloud/api/v1/web/751c0cc7-acd5-4f8c-b8a8-0c4b0c8d7662/api/get-review.json'
        # Get reviews from the cloudant URL through defined function in restapi
        reviews_details = get_dealer_reviews_from_cf(URL, dealerId=dealer_id)
        # Concat all reviews of a dealer
        context['reviews_details'] = reviews_details
        # Take Dealer name
        # print(CarDealer)
        # if reviews_details != '':
        #     reveiws = ' '.join(
        #         [review.review + ' ' + review.sentiment for review in reviews_details])
        # else:
        #     reveiws = 'Incorrect Dealer Id'
        # Return a list fo dealers short name
        return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review


def add_review(request, dealer_id, dealer_name):
    if request.user.is_authenticated:
        if request.method == 'POST':
            # construcr a dictionary object to hold append keys
            form_data = request.POST
            # Get car information from car model using car id from submitted form
            car = CarModel.objects.get(pk=form_data['car'])
            # print(form_data)
            # print(car.make.name)
            review = {
                'time': json.dumps(datetime.utcnow().isoformat(), default=str),
                'dealership': dealer_id,
                'id': dealer_id,
                'car_make': car.make.name,
                'car_model': car.name,
                'car_year': car.get_year(),
                'name': request.user.first_name + request.user.last_name if request.user.first_name or request.user.last_name else request.user.username,
                'purchase': form_data.get('purchasecheck'),
                "review": form_data.get('content')
            }

            if review['purchase']:
                review['purchase_date'] = datetime.strptime(
                    form_data.get("purchasedate"), "%m/%d/%Y").isoformat()
            print(review)
            json_payload = {
                'review': review
            }
            # URL of python Action in IBM Functions
            URL = 'https://us-south.functions.appdomain.cloud/api/v1/web/751c0cc7-acd5-4f8c-b8a8-0c4b0c8d7662/api/post-review'

            # posting the review to cloudant
            posted_response = post_request(
                URL, json_payload, dealerId=dealer_id)

            if int(posted_response.status_code) == 200:
                print("Review posted successfully.")

            # After posting the review the user is redirected back to the dealer details page
            return redirect("djangoapp:dealer_details", dealer_id=dealer_id, dealer_name=dealer_name)
        else:
            context = {}
            URL = 'https://us-south.functions.appdomain.cloud/api/v1/web/751c0cc7-acd5-4f8c-b8a8-0c4b0c8d7662/api/dealership.json'
            dealer = get_dealers_by_id(URL, dealerId=dealer_id)
            # print(dealer['id'])
            context['dealer_name'] = dealer
            context['dealer_id'] = dealer_id
            context['cars'] = CarModel.objects.all()
            print(context['cars'])

            return render(request, 'djangoapp/add_review.html', context)
    else:
        return redirect("/djangoapp/login")
