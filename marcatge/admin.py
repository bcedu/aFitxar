from django.contrib import admin
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.utils import timezone
from django.http import FileResponse
from .models import Marcatge
from modelclone import ClonableModelAdmin


class MarcatgeAdmin(ClonableModelAdmin):
    list_display = ['treballador', 'entrada_', 'sortida_', 'subtotal', 'subtotal_dia']
    ordering = ['treballador', '-entrada', 'sortida']
    list_filter = ['entrada', 'sortida', 'treballador']
    readonly_fields = ['subtotal', 'subtotal_dia']

admin.site.register(Marcatge, MarcatgeAdmin)


class TreballadorAdmin(ClonableModelAdmin):
    list_display = ['nom', 'vat', 'codi_entrada', 'obrir_marcatges']
    readonly_fields = ['obrir_marcatges']
    ordering = ['nom']
    list_filter = ['nom']
    actions = ["generar_resum"]

    def generar_resum(self, request, queryset):
        if 'apply' in request.POST:
            data_desde = request.POST.get("data_desde")
            if not data_desde:
                data_desde = "{0}-{1}-01".format(timezone.now().year, str(timezone.now().month).zfill(2))

            data_fins = request.POST.get("data_fins")
            if not data_fins:
                data_fins = timezone.now().strftime("%Y-%m-%d")

            resum = Treballador.generar_resum(queryset, data_desde, data_fins)

            response = FileResponse(open(resum.name, 'rb'), as_attachment=True, filename=resum.name, content_type='text/csv')

            return response
        else:
            return render(request, 'admin/generar_resum.html', context={'treballadors': queryset})

    generar_resum.short_description = "Generar Resum d'Hores"


from .models import Treballador
admin.site.register(Treballador, TreballadorAdmin)
