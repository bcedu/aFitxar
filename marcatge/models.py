from django.db import models
from django.utils import timezone
from django.utils.html import format_html
from datetime import timedelta, time, datetime
from django.core.validators import MinLengthValidator
from .validators import validate_numeric_char
from django.utils.translation import gettext as _
import tempfile
import csv
from django import forms


def format_result_as_hours(totsec):
    h = str(totsec // 3600).split(".")[0]
    m = str((totsec % 3600) // 60).split(".")[0]
    return h.zfill(2) + ":" + m.zfill(2)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class Treballador(models.Model):
    nom = models.CharField(max_length=200)
    vat = models.CharField(max_length=20)
    codi_entrada = models.CharField(
        max_length=4,
        validators=[
            validate_numeric_char,
            MinLengthValidator(4)
        ]
    )

    def obrir_marcatges(self):
        return format_html('<a class="button" href="/admin/marcatge/marcatge/?treballador__id__exact={}">Marcatges</a>', self.pk)

    obrir_marcatges.short_description = 'Obrir Marcatges'
    obrir_marcatges.allow_tags = True

    def __str__(self):
        return self.nom

    def get_time_spent_on_date(self, data):
        trobats = Marcatge.objects.filter(
            entrada__range=(datetime.combine(data, time.min), datetime.combine(data, time.max)),
            sortida__isnull=False,
            treballador=self
        )
        acumulat = 0
        for trobat in trobats:
            acumulat += trobat.get_time_spent().total_seconds()
        return acumulat

    @staticmethod
    def get_treballador_from_codi(codi):
        treballador_id = Treballador.objects.filter(codi_entrada=codi)
        if not treballador_id:
            return False, _("El codi introduit no es correspon amb cap treballador")
        elif len(treballador_id) > 1:
            return False, _("Atencio! Hi ha mes de un treballador amb el codi {0}! Nomes pot haver-hi 1 treballador per codi.").format(codi)
        else:
            return treballador_id[0], _("Treballador amb codi {0} trobat correctament").format(codi)

    def get_estat_marcatges(self):
        msg = ""

        marcatges_en_marxa = Marcatge.objects.filter(sortida__isnull=True, treballador=self)
        if marcatges_en_marxa:
            marcatge_en_marxa = marcatges_en_marxa[0]
            msg += _(u"Tens un marcatge en marxa iniciat a les {0}. ").format(marcatge_en_marxa.entrada.strftime("%H:%M del %d/%m/%Y"))
        else:
            msg += _(u"No tens cap marcatge en marxa. ")

        inici_avui = timezone.now()
        inici_avui = inici_avui.replace(hour=0, minute=0, second=0)
        marcats_avui = Marcatge.objects.filter(treballador=self, entrada__gte=inici_avui)
        total_spent = timedelta(seconds=0)
        for marcat_avui in marcats_avui:
            total_spent += marcat_avui.get_time_spent()
        msg = _("Total marcat avui: {0}.\n").format(str(total_spent).split(".")[0]) + msg
        return msg

    @staticmethod
    def generar_resum(treballadors, data_desde, data_fins):
        if not isinstance(data_desde, datetime):
            data_desde = datetime.strptime(data_desde, "%Y-%m-%d")
        if not isinstance(data_fins, datetime):
            data_fins = datetime.strptime(data_fins, "%Y-%m-%d")

        fname = 'resum_hores_{0}_{1}'.format(data_desde.strftime("%Y-%m-%d"), data_fins.strftime("%Y-%m-%d"))
        tf = tempfile.NamedTemporaryFile('w+t', prefix=fname, suffix=".csv")
        tfwriter = csv.writer(tf, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        tfwriter.writerow(["Dia"]+[t.nom for t in treballadors])

        delta = data_fins - data_desde
        for i in range(delta.days + 1):
            gastats = []
            day = data_desde + timedelta(days=i)
            for y in range(len(treballadors)):
                gastat = format_result_as_hours(treballadors[y].get_time_spent_on_date(day))
                gastats.append(gastat)
            tfwriter.writerow([day.strftime("%d-%m-%Y")]+gastats)
        tf.seek(0)
        return tf


class Marcatge(models.Model):
    entrada = models.DateTimeField()
    entrada_ = models.DateTimeField()
    entrada_ip = models.CharField(max_length=16, null=True, blank=True)
    sortida = models.DateTimeField(null=True, blank=True)
    sortida_ = models.DateTimeField()
    sortida_ip = models.CharField(null=True, blank=True, max_length=16)
    treballador = models.ForeignKey(Treballador, on_delete=models.CASCADE)

    def entrada_(self):
        if not self.entrada:
            return format_html("-")
        return format_html('<b>{0}</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{1}', self.entrada.strftime("%d/%m/%Y"), self.entrada.strftime("%H:%M"))

    def sortida_(self):
        if not self.sortida:
            return format_html("-")
        return format_html('{0}', self.sortida.strftime("%H:%M"))

    entrada_.allow_tags = True
    sortida_.allow_tags = True

    def get_time_spent(self):
        if not self.entrada:
            return timedelta(seconds=0)
        sortida = self.sortida
        if not sortida:
            sortida = timezone.now()
        return sortida - self.entrada

    @staticmethod
    def fes_entrada(treballador, ip=None):
        en_marxa = Marcatge.objects.filter(sortida__isnull=True, treballador=treballador)
        if en_marxa:
            return False, _(u"No pots fer una entrada si ja en tens una en marxa. Has de marcar una sortia.")
        m = Marcatge(entrada=timezone.now(), treballador=treballador, entrada_ip=ip)
        m.save()
        return True, _(u"Entrada realitzada amb èxit")

    @staticmethod
    def fes_sortida(treballador, ip=None):
        en_marxa = Marcatge.objects.filter(sortida__isnull=True, treballador=treballador)
        if not en_marxa:
            return False, _(u"No pots fer una sortida si no tens cap marcatge en marxa. Has de marcar una entrada.")
        en_marxa.update(sortida=timezone.now(), sortida_ip=ip)
        return True, _(u"Sortida realitzada amb èxit.")

