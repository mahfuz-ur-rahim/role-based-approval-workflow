from django.shortcuts import redirect


def home(request):
    return redirect('workflow:document-list')
