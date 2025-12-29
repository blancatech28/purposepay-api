from django.shortcuts import render

def index(request):
    """A landing page for PurposePay."""
    return render(request, "home/index.html")

