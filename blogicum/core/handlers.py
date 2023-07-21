# handlers.py

from django.shortcuts import render

def server_error(request):
    return render(request, 'pages/500.html', status=500)
