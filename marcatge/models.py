from collections import OrderedDict
from random import randrange, choice

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
from tqdm import tqdm
from workalendar.europe import Spain


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
        default=6, max_digits=5, decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(24)
        ]
    )
    ajustar_jornada_diaria = models.BooleanField(null=True, blank=True, default=True)

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

    def fes_entrada(self, ip=None, data=timezone.now()):
        en_marxa = self.te_marcatge_actiu(data)
        if en_marxa:
            return False, u"No pots fer una entrada si ja en tens una en marxa. Has de marcar una sortia."
        m = Marcatge(tipus="entrada", data=data, treballador=self)
        m.save()
        return True, u"Entrada realitzada amb èxit"

    def fes_sortida(self, ip=None, data=timezone.now()):
        en_marxa = self.te_marcatge_actiu(data)
        if not en_marxa:
            return False, u"No pots fer una sortida si no tens cap marcatge en marxa. Has de marcar una entrada."
        m = Marcatge(tipus="sortida", data=data, treballador=self)
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

    def ajustar_hores(self, data=timezone.now()):
        if self.ajustar_jornada_diaria:
            calendari = Spain()
            if calendari.is_working_day(data):
                dia_de_treball, created = DiaTreball.objects.get_or_create(
                    treballador=self, dia=data
                )
            else:
                dia_de_treball = DiaTreball.objects.get(
                    treballador=self, dia=data
                )
            if dia_de_treball:
                dia_de_treball.ajustar_hores()
        return True

    @staticmethod
    def cron_ajustar_hores(dia=timezone.now()):
        if isinstance(dia, str):
            dia = datetime.strptime(dia, "%Y-%m-%d")
        from django.db import transaction
        treballadors = Treballador.objects.all()  # Busca tots els treballadors
        for treballador in tqdm(treballadors):
            try:
                with transaction.atomic():  # Manté cada operació independent
                    treballador.ajustar_hores(dia)
            except Exception as e:
                print(f"Error ajustant hores per {treballador.nom}: {e}")


class DiaTreball(models.Model):
    treballador = models.ForeignKey(Treballador, on_delete=models.CASCADE)
    dia = models.DateField()
    hores_totals = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    hores_restants = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    hores_ajustades = models.BooleanField(default=False, null=True, blank=True)
    marcatges_relacionats_txt_backup = models.CharField(null=True, max_length=256)

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

    def ajustar_hores(self, marge=0.15):
        if not self.hores_ajustades:
            self.marcatges_relacionats_txt_backup = self.marcatges_relacionats_txt
            self.save()
            self.ajustar_marcatges_erronis()
            self.actualitzar_hores_totals()
            self.save()
            if abs(float(self.hores_restants)) > marge:
                # nomes ajustem hores si no es un dia festiu
                calendari = Spain()
                if calendari.is_working_day(self.dia):
                    if self.hores_restants >= 0:
                        self.ajustar_hores_restants()
                    else:
                        self.ajustar_hores_sobrants()
                    self.actualitzar_hores_totals()
            self.hores_ajustades = True
            self.save()
        return True

    def ajustar_marcatges_erronis(self):
        # Cas 1: tenim una unica sortida sense cap entrada. Eliminem la sortida.
        if self.ultim_marcatge and self.ultim_marcatge.tipus == "sortida":
            entrades = Marcatge.objects.filter(treballador=self.treballador, data__date=self.dia, tipus="entrada")
            if not entrades:
                self.ultim_marcatge.delete()

        # Cas 2: Tenim una entrada i una sortida a la mateixa hora i minut.
        ultim_marcatge = Marcatge.objects.filter(treballador=self.treballador, dia_treball=self).order_by('-data').first()
        if ultim_marcatge:
            ultim_marcatge_2 = Marcatge.objects.exclude(
                id=ultim_marcatge.id
            ).filter(
                treballador=self.treballador, dia_treball=self
            ).order_by('-data').first()
            if ultim_marcatge_2 and ultim_marcatge_2.data.strftime("%Y-%m-%s %H:%M") == ultim_marcatge.data.strftime("%Y-%m-%s %H:%M"):
                marcatges_posteriors = Marcatge.objects.exclude(
                    id__in=[ultim_marcatge.id, ultim_marcatge_2.id]
                ).filter(
                    treballador=self.treballador, dia_treball=self, data__gte=ultim_marcatge.data
                )
                # 2.1: No tenim cap marcatge posterior.
                if not marcatges_posteriors:
                    marcatge_anterior = Marcatge.objects.exclude(
                        id__in=[ultim_marcatge.id, ultim_marcatge_2.id]
                    ).filter(
                        treballador=self.treballador, dia_treball=self, data__lte=ultim_marcatge.data
                    ).order_by('-data').first()
                    eliminar_sortida = False
                    eliminar_entrada = False
                    # No hi ha marcatge anterior. Eliminem la sortida incorrecte.
                    if not marcatge_anterior:
                        eliminar_sortida = True
                    # El marcatge anterior es una entrada. Eliminem la entrada incorrecte.
                    elif marcatge_anterior.tipus == "entrada":
                        eliminar_entrada = True
                    # El marcatge anterior es una sortida. Eliminem la entrada i la sortida incorrectes.
                    else:  # marcatge_anterior.tipus == "sortida"
                        eliminar_entrada = eliminar_sortida = True
                    for a_eliminar in [ultim_marcatge, ultim_marcatge_2]:
                        if (a_eliminar.tipus == "entrada" and eliminar_entrada) or (a_eliminar.tipus == "sortida" and eliminar_sortida):
                            a_eliminar.delete()

        # Cas 3: El primer marcarge es una sortida. L'eliminem
        primer_marcatge = Marcatge.objects.filter(treballador=self.treballador, dia_treball=self).order_by('-data').last()
        if primer_marcatge:
            if primer_marcatge.tipus == "entrada":
                # Podem tindre una sortida a la mateixa hora i minut
                primer_marcatge_2 = Marcatge.objects.exclude(
                    id=primer_marcatge.id
                ).filter(
                    treballador=self.treballador, dia_treball=self
                ).order_by('data').first()
                if (
                    primer_marcatge_2 and primer_marcatge_2.tipus == "sortida"
                    and primer_marcatge_2.data.strftime("%Y-%m-%s %H:%M") == primer_marcatge.data.strftime("%Y-%m-%s %H:%M")
                ):
                    primer_marcatge = primer_marcatge_2
            if primer_marcatge and primer_marcatge.tipus == "sortida":
                primer_marcatge.delete()
        return True

    def ajustar_hores_restants(self):
        if self.ultim_marcatge and self.ultim_marcatge.tipus == "entrada":
            # Si tenim una entrada marcada la reaprofitem, no cal fer res de moment
            start_date = self.ultim_marcatge.data
        else:
            if self.ultim_marcatge and self.ultim_marcatge.tipus == "sortida":
                # Si ja haviem marcat algo avui, el nou marcatge el començarem uns 10 minuts despres
                start_date = self.ultim_marcatge.data + timedelta(minutes=randrange(9))
            else:
                # Si no hem marcat res, començarem en algun moment de les 8 del mati
                start_date = datetime.combine(self.dia, datetime.min.time())
                start_date = start_date.replace(hour=8, minute=randrange(50), second=0)
            # Marquem la entrada nova
            self.treballador.fes_entrada(data=start_date)
            start_date = self.ultim_marcatge.data

        # Ara que ja tenim una entrada com a punt de partida,
        # calculem la nova sortida per arrivar a les hores que toquen
        num = choice([i for i in range(-5, 6)]) / 100.0
        nova_sortida = start_date + timedelta(hours=float(self.hores_restants) + num)
        if nova_sortida < start_date:
            nova_sortida = start_date + timedelta(hours=float(self.hores_restants))
        if nova_sortida.strftime("%Y-%m-%d") != self.ultim_marcatge.data.strftime("%Y-%m-%d"):
            raise Exception("No es pot ajustar les hores.")
        self.treballador.fes_sortida(data=nova_sortida)
        return True

    def ajustar_hores_sobrants(self):
        if self.ultim_marcatge and self.ultim_marcatge.tipus == "entrada":
            # Si tenim una entrada marcada la reaprofitem, la eliminem
            self.ultim_marcatge.delete()
        if not self.ultim_marcatge:
            raise Exception("No es pot ajustar les hores.")
        if self.ultim_marcatge.tipus ==     "entrada":
            raise Exception("No es pot ajustar les hores.")
        num = choice([i for i in range(-5, 6)]) / 100.0
        nova_sortida = self.ultim_marcatge.data + timedelta(hours=float(self.hores_restants) + num)
        ultima_entrada = Marcatge.objects.filter(treballador=self.treballador, dia_treball=self, tipus="entrada").order_by('data').last()
        if not ultima_entrada:
            raise Exception("No es pot ajustar les hores.")
        if nova_sortida < ultima_entrada.data:
            raise Exception("No es pot ajustar les hores.")
        self.ultim_marcatge.data = nova_sortida
        self.ultim_marcatge.save()
        return True


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
