from collections import OrderedDict

from django.db import models
from django.utils import timezone
from django.utils.html import format_html
from datetime import timedelta, time, datetime
from django.core.validators import MinLengthValidator, RegexValidator, MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import tempfile
import csv
from decimal import Decimal


def format_as_hours(hores_decimals):
    hores_decimals = hores_decimals
    hores = int(hores_decimals)
    minuts = int((hores_decimals - hores) * 60)
    return f"{hores}h {minuts:02d}m"


class Treballador(models.Model):
    nom = models.CharField(max_length=200)
    vat = models.CharField(max_length=20)
    codi_entrada = models.CharField(
        max_length=4,
        validators=[
            RegexValidator(regex=r'^\d{4}$', message="El codi d'entrada ha de ser exactament 4 dígits."),
            MinLengthValidator(4)
        ]
    )
    jornada_diaria = models.DecimalField(
        help_text="Hores de la jornada laboral de 1 dia. Atenció: '1.5' son '1h 30m'.",
        default=8, max_digits=5, decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(24)
        ]
    )

    @property
    def jornada_diaria_view(self):
        return format_as_hours(self.jornada_diaria)

    @property
    def hores_totals_avui(self):
        dia_treball = self.get_dia_treball(timezone.now().date())
        if dia_treball:
            return dia_treball.hores_totals
        return 0

    @property
    def hores_totals_avui_view(self):
        return format_as_hours(self.hores_totals_avui)

    @property
    def hores_restants(self):
        dia_treball = self.get_dia_treball(timezone.now().date())
        if dia_treball:
            return dia_treball.hores_restants
        return 0

    @property
    def hores_restants_view(self):
        return format_as_hours(self.hores_restants)

    @property
    def estat_marcatge_html(self):
        avui = timezone.now().date()
        te_marcatge_actiu = self.te_marcatge_actiu(avui)
        if te_marcatge_actiu:
            marcatge_actiu = self.get_ultim_marcatge(avui)
            return format_html(
                '<span style="color: green;">Entrada en marxa des de les {}</span>',
                marcatge_actiu.local_data.strftime('%H:%M del %d/%m/%Y')
            )
        return format_html('<span style="color: red;">Sense marcatge actiu</span>')

    def __str__(self):
        return self.nom

    def get_dia_treball(self, data):
        dia_treball = DiaTreball.objects.filter(dia=data, treballador=self)
        if dia_treball:
            return dia_treball[0]
        return False

    def get_ultim_marcatge(self, data):
        dia_treball = self.get_dia_treball(data)
        if dia_treball:
            return dia_treball.ultim_marcatge
        return False

    def te_marcatge_actiu(self, data):
        dia_treball = self.get_dia_treball(data)
        if dia_treball:
            return dia_treball.marcatge_en_marxa
        return False

    @staticmethod
    def generar_resum(treballadors, data_desde, data_fins):
        """ Ambdos dates son incloses"""
        if not isinstance(data_desde, datetime):
            data_desde = datetime.strptime(data_desde, "%Y-%m-%d")
        if not isinstance(data_fins, datetime):
            data_fins = datetime.strptime(data_fins, "%Y-%m-%d")

        fname = 'resum_hores_{0}_{1}'.format(data_desde.strftime("%Y-%m-%d"), data_fins.strftime("%Y-%m-%d"))
        tf = tempfile.NamedTemporaryFile('w+t', prefix=fname, suffix=".csv")
        tfwriter = csv.writer(tf, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        tfwriter.writerow(["Dia"] + [t.nom for t in treballadors])

        total_hores_treballador = OrderedDict()
        while data_desde <= data_fins:
            gastats = []
            for t in treballadors:
                if t.nom not in total_hores_treballador:
                    total_hores_treballador[t.nom] = 0
                dia_treball = DiaTreball.objects.filter(dia=data_desde, treballador=t).first()
                if not dia_treball:
                    gastats.append(0)
                else:
                    gastats.append(dia_treball.hores_totals_view)
                    total_hores_treballador[t.nom] += dia_treball.hores_totals
            tfwriter.writerow([data_desde.strftime("%d-%m-%Y")] + gastats)
            data_desde += timedelta(days=1)
        for t in total_hores_treballador:
            total_hores_treballador[t] = format_as_hours(total_hores_treballador[t])
        tfwriter.writerow(["Total mes: "] + list(total_hores_treballador.values()))
        tf.seek(0)
        return tf

    @staticmethod
    def get_treballador_from_codi(codi):
        treballador_id = Treballador.objects.filter(codi_entrada=codi)
        if not treballador_id:
            return False, "El codi introduit no es correspon amb cap treballador"
        elif len(treballador_id) > 1:
            return False, "Atencio! Hi ha mes de un treballador amb el codi {0}! Nomes pot haver-hi 1 treballador per codi.".format(codi)
        else:
            return treballador_id[0], "Treballador amb codi {0} trobat correctament".format(codi)

    def fes_entrada(self, ip=None):
        data = timezone.now()
        en_marxa = self.te_marcatge_actiu(data)
        if en_marxa:
            return False, u"No pots fer una entrada si ja en tens una en marxa. Has de marcar una sortia."
        m = Marcatge(tipus="entrada", data=timezone.now(), treballador=self)
        m.save()
        return True, u"Entrada realitzada amb èxit"

    def fes_sortida(self, ip=None):
        data = timezone.now()
        en_marxa = self.te_marcatge_actiu(data)
        if not en_marxa:
            return False, u"No pots fer una sortida si no tens cap marcatge en marxa. Has de marcar una entrada."
        m = Marcatge(tipus="sortida", data=timezone.now(), treballador=self)
        m.save()
        return True, u"Sortida realitzada amb èxit."

    def get_estat_marcatges(self):
        msg = ""
        data = timezone.now()
        marcatges_en_marxa = self.te_marcatge_actiu(data)
        if marcatges_en_marxa:
            marcatge = self.get_ultim_marcatge(data)
            msg += u"Tens un marcatge en marxa iniciat a les {0}. ".format(marcatge.local_data.strftime("%H:%M del %d/%m/%Y"))
        else:
            msg += u"No tens cap marcatge en marxa. "

        msg = "Total marcat avui: {0}.\n".format(self.hores_totals_avui_view) + msg
        return msg


class DiaTreball(models.Model):
    treballador = models.ForeignKey(Treballador, on_delete=models.CASCADE)
    dia = models.DateField()
    hores_totals = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    hores_restants = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    @property
    def hores_totals_view(self):
        return format_as_hours(self.hores_totals)

    @property
    def hores_restants_view(self):
        return format_as_hours(self.hores_restants)

    @property
    def ultim_marcatge(self):
        marcatge = Marcatge.objects.filter(treballador=self.treballador, dia_treball=self).order_by('-data').first()
        return marcatge or False

    @property
    def marcatge_en_marxa(self):
        ultim = self.ultim_marcatge
        return ultim.tipus == "entrada" if ultim else False

    @property
    def marcatge_en_marxa_html(self):
        if self.marcatge_en_marxa:
            return format_html('<span style="color: green; font-size: 20px;">&#8226;</span>')  # Punt verd
        return format_html('<span style="color: red; font-size: 20px;">&#8226;</span>')  # Punt vermell

    @property
    def marcatges_relacionats_txt(self):
        marcatges = Marcatge.objects.filter(treballador=self.treballador, data__date=self.dia)
        return ", ".join([f"{marcatge.tipus} - {marcatge.local_data.strftime('%H:%M')}" for marcatge in marcatges])

    def __str__(self):
        return f"Dia de treball per {self.treballador.nom} - {self.dia}"

    def actualitzar_hores_totals(self):
        marcatges = Marcatge.objects.filter(treballador=self.treballador, dia_treball=self)
        hores_total = timedelta()
        entrada = None
        for marcatge in marcatges:
            if marcatge.tipus == 'entrada':
                entrada = marcatge.data
            elif marcatge.tipus == 'sortida' and entrada:
                sortida = marcatge.data
                hores_total += sortida - entrada
                entrada = None
        self.hores_totals = hores_total.total_seconds() / 3600
        self.hores_restants = self.treballador.jornada_diaria - Decimal(self.hores_totals)
        self.save()


class Marcatge(models.Model):
    treballador = models.ForeignKey(Treballador, on_delete=models.CASCADE)
    tipus = models.CharField(max_length=10, choices=[('entrada', 'Entrada'), ('sortida', 'Sortida')])
    data = models.DateTimeField(default=timezone.now)
    dia_treball = models.ForeignKey(DiaTreball, on_delete=models.CASCADE, null=True, blank=True)

    @property
    def local_data(self):
        return timezone.localtime(self.data)

    @property
    def tipus_html(self):
        if self.tipus == "entrada":
            return format_html('<span style="color: green;">Entrada</span>')
        return format_html('<span style="color: red;">Sortida</span>')

    def __str__(self):
        return f"{self.treballador.nom} - {self.tipus} - {self.local_data}"


# Signal per crear/actualitzar automàticament un DiaTreball quan es fa un nou marcatge
@receiver(post_save, sender=Marcatge)
def crear_dia_de_treball(sender, instance, created, **kwargs):
    if created:
        treballador = instance.treballador
        dia = instance.data.date()
        dia_de_treball, created = DiaTreball.objects.get_or_create(
            treballador=treballador, dia=dia
        )
        instance.dia_treball = dia_de_treball
        instance.save()
        dia_de_treball.actualitzar_hores_totals()


# Signal que s'activa abans de guardar l'objecte Treballador
@receiver(pre_save, sender=Treballador)
def actualitzar_hores_totals_signal(sender, instance, **kwargs):
    if instance.pk:
        old_instance = Treballador.objects.get(pk=instance.pk)
        if old_instance.jornada_diaria != instance.jornada_diaria:
            for dia in DiaTreball.objects.filter(treballador=instance):
                dia.treballador = instance
                dia.actualitzar_hores_totals()
