from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
# from .models import related models
from .models import CarModel, CarMake
# from .restapis import related methods
from .restapis import get_dealers_from_cf, get_dealer_by_id_from_cf, get_dealer_reviews_from_cf, post_request
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
# def login_request(request):
def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['pwd']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return render(request, 'djangoapp/index.html', context)
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'djangoapp/index.html', context)
    else:
        context['message'] = "Invalid request."
        return render(request, 'djangoapp/index.html', context)

# Create a `logout_request` view to handle sign out request
# def logout_request(request):
def logout_request(request):
    print("Loging out the user '{}'".format(request.user.username))
    logout(request)
    return redirect('djangoapp/index.html')

# Create a `registration_request` view to handle sign up request
# def registration_request(request):
def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['pwd']
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
            user.is_superuser = True
            user.is_staff=True
            user.save()  
            login(request, user)
            return redirect("djangoapp:index")
        else:
            messages.warning(request, "The user already exists.")
            return redirect("djangoapp:registration")

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    context = {}
    if request.method == "GET":
        # Changed to my address:
        url = "https://us-south.functions.appdomain.cloud/api/v1/web/13b00405-d053-41c3-a9c2-efb1edc6eea5/dealership-package/get-dealership"
        # Get dealers from the URL
        dealerships = get_dealers_from_cf(url)
        context["dealership_list"] = dealerships
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
# def get_dealer_details(request, dealer_id):
# ...
def get_dealer_details(request, id): # for one dealer id
    if request.method == "GET":
        context = {}
        get_dealership_url = "https://us-south.functions.appdomain.cloud/api/v1/web/13b00405-d053-41c3-a9c2-efb1edc6eea5/dealership-package/get-dealership"

        dealer = get_dealer_by_id_from_cf(get_dealership_url, id=id)
        context["dealer"] = dealer
        # print(dealer)

        get_review_url = "https://us-south.functions.appdomain.cloud/api/v1/web/13b00405-d053-41c3-a9c2-efb1edc6eea5/dealership-package/get-review"
        reviews = get_dealer_reviews_from_cf(get_review_url, id=id)
        context["reviews"] = reviews
        # print(reviews)
        
        return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
# View to submit a new review
def add_review(request, id):
    context = {}

    dealer_url = "https://us-south.functions.appdomain.cloud/api/v1/web/13b00405-d053-41c3-a9c2-efb1edc6eea5/dealership-package/get-dealership"
    review_post_url = "https://us-south.functions.appdomain.cloud/api/v1/web/13b00405-d053-41c3-a9c2-efb1edc6eea5/dealership-package/post-review"

    dealer = get_dealer_by_id_from_cf(dealer_url, id=id)
    
    context["dealer"] = dealer # add dealer info to the context
    
    if request.method == 'GET':
        # Get cars for the dealer
        cars = CarModel.objects.all()
        # print(cars)
        context["cars"] = cars
       
        return render(request, 'djangoapp/add_review.html', context)
    elif request.method == 'POST':
        # First check if user is authenticated because 
        # only authenticated users can post reviews 
        # for a dealer.
        if request.user.is_authenticated:
            username = request.user.username
            print(request.POST)
            review = dict()
            car_id = request.POST["car"]
            car = CarModel.objects.get(pk=car_id)
            review["time"] = datetime.utcnow().isoformat()
            review["name"] = username
            review["dealership"] = id # why same ids?
            review["id"] = id
            review["review"] = request.POST["content"]
            review["purchase"] = False
            if "purchasecheck" in request.POST:
                if request.POST["purchasecheck"] == 'on':
                    review["purchase"] = True
            review["purchase_date"] = request.POST["purchasedate"]           
            review["car_model"] = car.name
            
            json_payload = {}
            json_payload["review"] = review

            post_request(review_post_url, json_payload, id=id)
        
        return redirect("djangoapp:dealer_details", id=id)
