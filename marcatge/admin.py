from django.contrib import admin
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.utils import timezone
from django.http import FileResponse
from .models import Marcatge
admin.site.register(Marcatge)


class TreballadorAdmin(admin.ModelAdmin):
    list_display = ['nom', 'vat', 'codi_entrada']
    ordering = ['nom']
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
