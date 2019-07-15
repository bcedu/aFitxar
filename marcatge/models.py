from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.validators import MinLengthValidator
from .validators import validate_numeric_char
from django.utils.translation import gettext as _


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

    def __str__(self):
        return self.nom

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
        msg += _("\nTotal marcat avui: {0}.").format(str(total_spent).split(".")[0])
        return msg


class Marcatge(models.Model):
    entrada = models.DateTimeField()
    entrada_ip = models.CharField(max_length=16, null=True, blank=True)
    sortida = models.DateTimeField(null=True, blank=True)
    sortida_ip = models.CharField(null=True, blank=True, max_length=16)
    treballador = models.ForeignKey(Treballador, on_delete=models.CASCADE)

    def __str__(self):
        name = self.treballador.nom + "  "
        if self.entrada:
            name += self.entrada.strftime("%d/%m/%Y %H:%M") + " - "
        if self.sortida:
            name += self.sortida.strftime("%d/%m/%Y %H:%M")
        return name

    def get_time_spent(self):
        if not self.entrada:
            return timedelta(seconds=0)
        sortida = self.sortida
        if not sortida:
            sortida = timezone.now()
        return sortida - self.entrada

    @staticmethod
    def fes_entrada(treballador, ip):
        en_marxa = Marcatge.objects.filter(sortida__isnull=True, treballador=treballador)
        if en_marxa:
            return False, _(u"No pots fer una entrada si ja en tens una en marxa. Has de marcar una sortia.")
        m = Marcatge(entrada=timezone.now(), treballador=treballador, entrada_ip=ip)
        m.save()
        return True, _(u"Entrada realitzada amb èxit")

    @staticmethod
    def fes_sortida(treballador, ip):
        en_marxa = Marcatge.objects.filter(sortida__isnull=True, treballador=treballador)
        if not en_marxa:
            return False, _(u"No pots fer una sortida si no tens cap marcatge en marxa. Has de marcar una entrada.")
        en_marxa.update(sortida=timezone.now(), sortida_ip=ip)
        return True, _(u"Sortida realitzada amb èxit.")
