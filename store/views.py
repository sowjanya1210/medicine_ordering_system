from django.shortcuts import render, redirect
from .models import Product,Category,Profile
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .forms import SignUpForm,UserUpdateForm,ChangePasswordForm, UserInfoForm
from django.db.models import Q
from cart.cart import Cart
import json
from payment.forms import ShippingForm
from payment.models import ShippingAddress
# Create your views here.
def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})

def about(request):
    return render(request, 'about.html',{})

def product(request,pk):
    products = Product.objects.get(id=pk)
    return render(request, 'product.html', {'products': products})


def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            current_user = Profile.objects.get(user__id=request.user.id)
            saved_cart = current_user.old_cart
            if saved_cart:
                converted_cart = json.loads(saved_cart)
                cart = Cart(request)
                for key,value in converted_cart.items():
                    cart.db_add(product=key,quantity=value)
            messages.success(request, 'Logged in successfully')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('login')
    else:
        return render(request, 'login.html')

def logout_user(request): 
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('home')


def register_user(request):
    form = SignUpForm()
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, 'Registration successful! Please fill the user info...')
            return redirect('update_info')
        else:
            messages.error(request, 'Error in registration')
    return render(request, 'register.html',{ 'form': form})



def category(request, foo):
    foo = foo.replace("-", " ")
    try:
        cat = Category.objects.get(name__iexact=foo)
    except Category.DoesNotExist:
        messages.error(request, 'No such category found')
        return redirect('home')
    products = Product.objects.filter(category=cat)
    return render(request, 'category.html', {'products': products, 'category': cat})

def category_summary(request):
    categories = Category.objects.all()

    return render(request,'category_summary.html',{"categories":categories})

def update_user(request):
    if request.user.is_authenticated:
        current_user = User.objects.get(id=request.user.id)
        user_form = UserUpdateForm(request.POST or None, instance=current_user)
        if user_form.is_valid():
            user_form.save()
            login(request, current_user)
            messages.success(request, 'Profile updated successfully')
            return redirect('home')
            
        return render(request,'update_user.html',{'user_form': user_form})
    else:
        messages.success(request, 'You need to login first')
        return redirect('login')
    
def update_password(request):
    if request.user.is_authenticated:
        current_user = request.user
        if request.method == "POST":
            form = ChangePasswordForm(current_user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(
                    request, "Your password has been updated. Enjoy your experience"
                )
                login(request, current_user)
                return redirect("update_user")
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)
                    return redirect("update_password")
        else:
            form = ChangePasswordForm(current_user)
            context = {"form": form}
            return render(request, "update_password.html", context)
    else:
        messages.error(request, "You must be authenticated to access this page!")
        return redirect("home")


def update_info(request):
    if request.user.is_authenticated:
        current_user, created = Profile.objects.get_or_create(user=request.user)
        shipping_user, created = ShippingAddress.objects.get_or_create(user=request.user)

        form = UserInfoForm(request.POST or None, instance=current_user)
        shipping_form = ShippingForm(request.POST or None, instance=shipping_user)

        if form.is_valid() and shipping_form.is_valid():
            form.save()
            shipping_form.save()
            messages.success(request, "Your Info was updated successfully.")
            return redirect("home")

        return render(
            request,
            "update_info.html",
            {"form": form, "shipping_form": shipping_form},
        )
    else:
        messages.info(request, "You must be authenticated to access this page!")
        return redirect("home")


def search(request):
    if request.method == "POST":
        searched = request.POST["q"]
        searched = Product.objects.filter(
            Q(name__icontains=searched) | Q(description__icontains=searched)
        )
        if not searched:
            messages.info(request, "That product does not exist, please try again.")
            return render(request, "search.html", {})
        else:
            context = {"searched": searched}
            return render(request, "search.html", context)
    else:
        context = {}
        return render(request, "search.html", context)