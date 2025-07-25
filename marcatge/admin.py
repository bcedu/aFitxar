from django.contrib import admin
from .models import Treballador, Marcatge, DiaTreball
from django.shortcuts import render, HttpResponse
import csv
from django.utils import timezone
from django.http import FileResponse
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import admin
from django import forms
from django.contrib import admin, messages
from django import forms
from django.shortcuts import render, redirect
from django.urls import path
from .models import DiaTreball
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from ast import literal_eval

class AssignarHoresMassiuForm(forms.Form):
    dies = forms.ModelMultipleChoiceField(
        queryset=DiaTreball.objects.all(),
        widget=forms.MultipleHiddenInput
    )
    hores = forms.DecimalField(label="Hores a assignar", min_value=0)


class EstatMarcatgeListFilter(admin.SimpleListFilter):
    title = 'Estat Marcatge'
    parameter_name = 'estat_marcatge'

    def lookups(self, request, model_admin):
        return (
            ('en_marxa', 'Treballant'),
            ('sense_marcatge', 'Sense Marcatge Actiu'),
        )

    def queryset(self, request, queryset):
        text_cerca = 'en marxa'
        if self.value() == 'en_marxa':
            return queryset.filter(
                id__in=[treballador.id for treballador in queryset if treballador.estat_marcatge_html and text_cerca in treballador.estat_marcatge_html]
            )
        elif self.value() == 'sense_marcatge':
            return queryset.filter(
                id__in=[treballador.id for treballador in queryset if treballador.estat_marcatge_html and text_cerca not in treballador.estat_marcatge_html]
            )
        return queryset


class MarcatgeInline(admin.TabularInline):
    model = Marcatge
    extra = 0
    fields = ('tipus', 'data', 'treballador')

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        """Emplena automàticament el treballador segons el DiaTreball."""
        if db_field.name == "treballador":
            obj = self.get_object_from_request(request)
            if obj:
                kwargs["initial"] = obj.treballador
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_object_from_request(self, request):
        """Obtén l'objecte DiaTreball des de la URL del request."""
        if "_popup" in request.GET:  # Per evitar problemes amb finestres emergents
            return None
        try:
            dia_treball_id = request.resolver_match.kwargs.get('object_id')
            if dia_treball_id:
                return DiaTreball.objects.get(pk=dia_treball_id)
        except DiaTreball.DoesNotExist:
            return None
        return None


class TreballadorAdmin(admin.ModelAdmin):
    list_display = ('nom', 'vat', 'codi_entrada', 'jornada_diaria_view', 'hores_totals_avui_view', 'hores_restants_view', 'estat_marcatge_html', 'obrir_dies')
    readonly_fields = ['obrir_dies']
    search_fields = ('nom', 'vat', 'codi_entrada')
    list_filter = [EstatMarcatgeListFilter]
    ordering = ['nom', 'vat']

    def jornada_diaria_view(self, obj):
        return obj.jornada_diaria_view
    jornada_diaria_view.short_description = "Jornada Laboral"

    def hores_totals_avui_view(self, obj):
        return obj.hores_totals_avui_view
    hores_totals_avui_view.short_description = "Hores totals d'avui"

    def hores_restants_view(self, obj):
        return obj.hores_restants_view
    hores_restants_view.short_description = "Hores restants d'avui"

    def estat_marcatge_html(self, obj):
        return obj.estat_marcatge_html
    estat_marcatge_html.short_description = 'Estat'

    def obrir_dies(self, obj):
        url = reverse('admin:marcatge_diatreball_changelist')  # Canvia 'app_name' pel nom de la teva app
        return format_html(
            '<a href="{}?treballador__id__exact={}" class="button" >Veure dies treball</a>',
            url,
            obj.id
        )
    obrir_dies.short_description = "Dies treball"

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


class MarcatgeAdmin(admin.ModelAdmin):
    list_display = ('treballador', 'tipus_html', 'data')
    search_fields = ('treballador', 'tipus', 'data')
    list_filter = ('treballador', 'tipus', 'data')
    ordering = ['-data', '-tipus', 'treballador']
    actions = ['exportar_com_csv']

    def exportar_com_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="marcatges.csv"'
        writer = csv.writer(response)
        writer.writerow(['Treballador', 'Tipus', 'Data'])
        for marcatge in queryset:
            writer.writerow([marcatge.treballador.nom, marcatge.tipus, marcatge.local_data])
        return response
    exportar_com_csv.short_description = "Exportar com a CSV"


class DiaTreballAdmin(admin.ModelAdmin):

    class Media:
        js = ('js/ocultar_nova_jornada.js',)

    list_display = ('treballador', 'dia', 'jornada_diaria_view', 'hores_totals_view', 'hores_restants_view', 'marcatge_en_marxa_html', 'marcatges_relacionats')
    search_fields = ('treballador', 'dia')
    list_filter = ('treballador', 'dia', 'hores_totals', 'hores_restants')
    ordering = ['-dia', 'treballador']
    exclude = ('marcatges_relacionats_txt_backup',)
    inlines = [MarcatgeInline]
    actions = ['assignar_hores_massiu', 'exportar_com_csv']
    fields = [
        "treballador",
        "dia",
        "hores_totals",
        "hores_restants",
        "forcar_jornada_diaria",
        "nova_jornada_diaria",
        "hores_ajustades",
    ]
    readonly_fields = [
        'hores_totals',
        'hores_restants',
    ]

    def marcatges_relacionats(self, obj):
        return obj.marcatges_relacionats_txt
    marcatges_relacionats.short_description = 'Marcatges del dia'

    def jornada_diaria_view(self, obj):
        if obj.forcar_jornada_diaria:
            return obj.nova_jornada_diaria_view
        else:
            return obj.treballador.jornada_diaria_view
    jornada_diaria_view.short_description = 'Jornada Laboral'

    def hores_totals_view(self, obj):
        return obj.hores_totals_view
    hores_totals_view.short_description = 'Hores Treballades'

    def hores_restants_view(self, obj):
        return obj.hores_restants_view
    hores_restants_view.short_description = 'Hores Restants'

    def marcatge_en_marxa_html(self, obj):
        return obj.marcatge_en_marxa_html
    marcatge_en_marxa_html.short_description = 'Treballant'

    def has_add_permission(self, request):
        # Es crearan autoamticament al fer un marcatge
        return False

    def exportar_com_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="marcatges_per_dia.csv"'
        writer = csv.writer(response)
        writer.writerow(['Treballador', 'dia', 'hores_totals', 'hores_restants', 'marcatges_relacionats'])
        for dia_treball in queryset:
            writer.writerow([dia_treball.treballador.nom, dia_treball.dia, dia_treball.hores_totals_view, dia_treball.hores_restants_view, dia_treball.marcatges_relacionats_txt])
        return response
    exportar_com_csv.short_description = "Exportar com a CSV"

    def assignar_hores_massiu(self, request, queryset):
        form = AssignarHoresMassiuForm(initial={'dies': queryset})
        context = {
            'form': form,
            'title': 'Modificar hores treballades',
        }
        return render(request, 'admin/assignar_hores_massiu.html', context)
    assignar_hores_massiu.short_description = "Modificar hores treballades"

    def processar_assignacio_hores(self, request):
        if request.method == 'POST':
            form = AssignarHoresMassiuForm(request.POST)
            if form.is_valid():
                dies = form.cleaned_data['dies']
                hores = form.cleaned_data['hores']
                for dia in dies:
                    dia.ajustar_a_x_hores(hores)
                self.message_user(request, f"Hores modificades a {dies.count()} dies.", messages.SUCCESS)
                return redirect('../..')
        else:
            form = AssignarHoresMassiuForm()

        return render(request, 'admin/assignar_hores_massiu.html', {
            'form': form,
            'title': 'Error al formulari',
        })

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('assignar-hores/processar/', self.admin_site.admin_view(self.processar_assignacio_hores),
                 name='assignar_hores_massiu')
        ]
        return custom_urls + urls


# Registra els models al panell d'administració
admin.site.register(Treballador, TreballadorAdmin)
admin.site.register(DiaTreball, DiaTreballAdmin)
admin.site.register(Marcatge, MarcatgeAdmin)