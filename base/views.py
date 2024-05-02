from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from .models import Room, Topic, Message
from .forms import RoomForm

# Create your views here.

# rooms = [
#     {'id': 1, 'name': 'test1'},
#     {'id': 2, 'name': 'test2'},
#     {'id': 3, 'name': 'test3'},
# ]


def login_page(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist')
            
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username or password does not exist')
        
    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def logout_user(request):
    logout(request)
    return redirect('home')


def register_page(request):
    page = 'register'
    form = UserCreationForm()
    context = {'form': form}
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error has occurred during registration')
        
    return render(request, 'base/login_register.html', context)
    

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q) |
        Q(host__username__icontains=q)
        )
    
    topics = Topic.objects.all() #filter top topics/topics w the most rooms
    room_count = rooms.count()
    room_msgs = Message.objects.filter(
        Q(room__topic__name__icontains=q)
        ) # change to only following activity feed
    
    context = {'rooms': rooms, 
               'topics': topics, 
               'room_count': room_count,
               'room_msgs': room_msgs}
    return render(request, 'base/home.html', context)


def room(request, pk):
    room = Room.objects.get(id=pk)
    room_msgs = room.message_set.all().order_by('-created')
    participants = room.participants.all()
    
    if request.method == 'POST':
        msg = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)
        
    context = {'room': room, 
               'room_msgs': room_msgs, 
               'participants': participants}
    return render(request, 'base/room.html', context)


def user_profile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_msgs = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user': user,
               'rooms': rooms,
               'room_msgs': room_msgs,
               'topics': topics
               }
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')
def create_room(request):
    form = RoomForm()
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.host = request.user
            room.save()
            return redirect('home')
            
    context = {'form': form}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def update_room(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    
    if request.user != room.host:
        return HttpResponse('You\'re not allowed edit this room!')
    
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect('home')
    
    context = {'form': form}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def delete_room(request, pk):
    room = Room.objects.get(id=pk)
    
    if request.user != room.host:
        return HttpResponse('You\'re not allowed edit this room!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})


@login_required(login_url='login')
def delete_msg(request, pk):
    msg = Message.objects.get(id=pk)
    
    if request.user != msg.user:
        return HttpResponse('You\'re not allowed edit this room!')

    if request.method == 'POST':
        msg.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': msg})