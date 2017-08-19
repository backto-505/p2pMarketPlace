# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from forms import SignUpForm, LoginForm, PostForm, LikeForm, CommentForm, CommentLikeForm
from models import UserModel, SessionToken, PostModel, CommentModel, LikeModel, CommentLikeModel
from django.http import HttpResponse
from imgurpython import ImgurClient
from marketplace.settings import BASE_DIR
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime
from django.core.mail import send_mail


# Create your views here.

def signup_view(request):
    today = datetime.now()
    message1 = ''
    message2 = ''
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']

            if len(username) < 4:
                if len(username) == 0:
                    message1 = "Username cannot be empty"
                else:
                    message1 = "Username length should be of 4 or more characters"

            name = form.cleaned_data['name']
            email = form.cleaned_data['email']

            password = form.cleaned_data['password']
            if len(password) < 5:
                message2 = "Password must be of atleast 5 characters"

            if len(message1) == 0 and len(message2) == 0:
                send_mail("Welcome to GarageSale", "Hello! We are glad to have you on board!\n Login now and start "
                                                   "buying/selling!", "aanchal.012@gmail.com", [email])
                user = UserModel(name=name, email=email, username=username, password=make_password(password))
                user.save()
                return render(request, 'success.html')
            else:
                return render(request, 'index.html',
                              {'form': form, 'today': today, 'message1': message1, 'message2': message2})

        else:
            return render(request, 'index.html',
                          {'form': form, 'today': today})

    elif request.method == "GET":
        form = SignUpForm()

    return render(request, 'index.html', {'form': form, 'method': request.method, 'today': today})


def login_view(request):
    response_data = {}
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = UserModel.objects.filter(username=username).first()
            if user:
                if check_password(password, user.password):
                    token = SessionToken(user=user)
                    token.create_token()
                    token.save()
                    response = redirect('feed/')
                    response.set_cookie(key='session_token', value=token.session_token)
                    return response
                else:
                    return render(request, 'login.html',
                                  {'form': form, 'message':"Incorrect Password! Try Again."})
            else:
                return render(request, 'login.html',
                              {'form': form, 'message':"Invalid Username"})

    elif request.method == 'GET':
        form = LoginForm()
        return render(request, 'login.html')

    response_data['form'] = form
    return render(request, 'login.html', response_data)


def feed_view(request):
    user = check_validation(request)
    if user:
        posts = PostModel.objects.all().order_by("-created_on")
        return render(request, 'feed.html', {
            "posts": posts
        })
    else:
        return redirect('/login/')


def check_validation(request):
    if request.COOKIES.get('session_token'):
        session = SessionToken.objects.filter(session_token=request.COOKIES.get('session_token')).first()
        if session:
            return session.user
    else:
        return None


def like_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = LikeForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            existing_like = LikeModel.objects.filter(post_id=post_id, user=user).first()
            if not existing_like:
                LikeModel.objects.create(post_id=post_id, user=user)
                post_user = PostModel.objects.filter(id=post_id).first()
                recepient = UserModel.objects.filter(id=post_user.user_id).first()
                send_mail("New Comment", "Someone liked your upload. Check GarageSale to view",
                          "aanchal.012@gmail.com", [recepient.email])
                print "Like successfully generated"
            else:
                existing_like.delete()
            return redirect('/feed/')
    else:
     return redirect('/login/')


def comment_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            comment_text = form.cleaned_data.get('comment_text')
            comment = CommentModel.objects.create(user=user, post_id=post_id, comment_text=comment_text)
            comment.save()
            post_user = PostModel.objects.filter(id=post_id).first()
            recepient = UserModel.objects.filter(id=post_user.user_id).first()
            send_mail("New Comment","Someone commented on your upload. Check GarageSale to view", "aanchal.012@gmail.com", [recepient.email])
            print "Comment successfully posted"
            return redirect('/feed/')
        else:
            return redirect('/feed/')
    else:
        return redirect('/login')

def comment_like_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = CommentLikeForm(request.POST)
        if form.is_valid():
            comment_id = form.cleaned_data.get('comment').id
            existing_like = CommentLikeModel.objects.filter(comment_id=comment_id, user=user).first()
            if not existing_like:
                CommentLikeModel.objects.create(comment_id=comment_id, user=user)
                print "Like on comment successfully generated"
            else:
                existing_like.delete()
            return redirect('/feed/')
    else:
        return redirect('/login/')


def post_view(request):
    user = check_validation(request)
    if user:
        if request.method == "GET":
            form = PostForm()
            return render(request,"post.html",{
            "form" : form
            })
    else:
        return redirect("/login/")

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data.get('image')
            caption = form.cleaned_data.get('caption')
            post = PostModel(user = user , image = image , caption = caption)
            post.save()
            path = str(BASE_DIR + "\\" + post.image.url)
            client = ImgurClient("247e8cde53a7073", "0d7a494a106eff885e1ed09fb0c63c6809d46038")
            post.image_url = client.upload_from_path(path, anon=True)['link']
            post.save()
            return redirect("/feed")