from django.shortcuts import render

from django.shortcuts import render

def game(request):
    return render(request, 'game/game.html')

