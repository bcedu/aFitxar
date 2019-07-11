from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from .models import Treballador, Marcatge, get_client_ip


def portal_marcatge(request):
    context = {}
    return render(request, 'marcatge/index.html', context)


def marcar_entrada(request):
    codi = request.POST.get("codi", "-1")
    found, message = Treballador.get_treballador_from_codi(codi)
    if not found:
        return render(request, 'marcatge/index.html', {
            'success_message': None,
            'error_message': message,
        })
    ip = get_client_ip(request)
    done, message = Marcatge.fes_entrada(found, ip)
    if not done:
        return render(request, 'marcatge/index.html', {
            'success_message': None,
            'error_message': message,
        })
    else:
        return render(request, 'marcatge/index.html', {
                'success_message': message,
                'error_message': None,
            })


def marcar_sortida(request):
    codi = request.POST.get("codi", "-1")
    found, message = Treballador.get_treballador_from_codi(codi)
    if not found:
        return render(request, 'marcatge/index.html', {
            'success_message': None,
            'error_message': message,
        })

    ip = get_client_ip(request)
    done, message = Marcatge.fes_sortida(found, ip)
    if not done:
        return render(request, 'marcatge/index.html', {
            'success_message': None,
            'error_message': message,
        })
    else:
        return render(request, 'marcatge/index.html', {
            'success_message': message,
            'error_message': None,
        })


def consultar_marcatge(request):
    codi = request.GET.get("codi", "-1")
    found, message = Treballador.get_treballador_from_codi(codi)
    if not found:
        return render(request, 'marcatge/index.html', {
            'success_message': None,
            'error_message': message,
        })

    message = found.get_estat_marcatges()
    return render(request, 'marcatge/index.html', {
        'success_message': message,
        'error_message': None,
    })
