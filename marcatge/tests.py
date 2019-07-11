import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import *


def create_treballador(nom="Eduard Berloso", vat="11111111H", codi="1234"):
    return Treballador.objects.create(nom=nom, vat=vat, codi_entrada=codi)


def fer_entrada(treballador_id=None, entrada=timezone.now()):
    if not treballador_id:
        treballador_id = Treballador.objects.all()
        if not treballador_id:
            return False
        else:
            treballador_id = treballador_id[0]
    return Marcatge.objects.create(treballador=treballador_id, entrada=entrada)


def fer_sortida(marcatge_id=None, sortida=timezone.now()):
    if marcatge_id is None:
        marcatge_id = Marcatge.objects.filter(sortida__isnull=True)
        if not marcatge_id:
            return False
        else:
            marcatge_id = marcatge_id[0]
    m = marcatge_id
    m.sortida = sortida
    m.save()
    return marcatge_id


class TreballadorTest(TestCase):

    def test_get_treballador_from_codi_not_treballador(self):
        res = Treballador.get_treballador_from_codi("9999")
        self.assertFalse(res[0])
        self.assertEqual(res[1], "El codi introduit no es correspon amb cap treballador")

    def test_get_treballador_from_codi_various_treballador(self):
        create_treballador(codi="9999")
        create_treballador(nom="Treballador 2", codi="9999")
        res = Treballador.get_treballador_from_codi("9999")
        self.assertFalse(res[0])
        self.assertEqual(res[1], "Atencio! Hi ha mes de un treballador amb el codi 9999! Nomes pot haver-hi 1 treballador per codi.")

    def test_get_treballador_from_codi_OK(self):
        tr = create_treballador(codi="9999")
        res = Treballador.get_treballador_from_codi("9999")
        self.assertTrue(res[0])
        self.assertEqual(res[0], tr)
        self.assertEqual(res[1], "Treballador amb codi 9999 trobat correctament")

    def test_get_estat_marcatges(self):
        tr = create_treballador(codi="9999")
        fer_entrada()
        fer_sortida()
        fer_entrada()
        fer_sortida()
        fer_entrada()
        res = tr.get_estat_marcatges()
        self.assertIn("Tens un marcatge en marxa iniciat", res)
        self.assertIn("Total marcat avui:", res)
        self.assertNotIn("No tens cap marcatge en marxa.", res)


class MarcatgeTest(TestCase):

    def test_fes_entrada_error_previous_running(self):
        create_treballador(codi="9999")
        treballador_id, msg = Treballador.get_treballador_from_codi("9999")
        fer_entrada()
        res = Marcatge.fes_entrada(treballador_id)
        self.assertFalse(res[0])
        self.assertEqual(res[1], "No pots fer una entrada si ja en tens una en marxa. Has de marcar una sortia.")

    def test_fes_entrada_OK(self):
        create_treballador(codi="9999")
        treballador, msg = Treballador.get_treballador_from_codi("9999")
        res = Marcatge.fes_entrada(treballador)
        self.assertTrue(res[0])
        self.assertEqual(res[1], "Entrada realitzada amb èxit")

    def test_fes_sortida_error_sense_entrada(self):
        create_treballador(codi="9999")
        treballador_id, msg = Treballador.get_treballador_from_codi("9999")
        res = Marcatge.fes_sortida(treballador_id)
        self.assertFalse(res[0])
        self.assertEqual(res[1], "No pots fer una sortida si no tens cap marcatge en marxa. Has de marcar una entrada.")

    def test_fes_sortida_OK(self):
        create_treballador(codi="9999")
        treballador, msg = Treballador.get_treballador_from_codi("9999")
        fer_entrada()
        res = Marcatge.fes_sortida(treballador)
        self.assertTrue(res[0])
        self.assertEqual(res[1], "Sortida realitzada amb èxit.")
        marcatge = Marcatge.objects.all()[0]
        self.assertTrue(marcatge.entrada)
        self.assertTrue(marcatge.sortida)
