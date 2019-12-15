
from django.urls import path

from . import views

app_name = 'marcatge'
urlpatterns = [
    path('', views.portal_marcatge, name='portal_marcatge'),
    path('entrada', views.marcar_entrada, name='marcar_entrada'),
    path('sortida', views.marcar_sortida, name='marcar_sortida'),
    path('consulta', views.consultar_marcatge, name='consultar_marcatge'),
    path('setup_subtotals', views.setup_subtotals, name='setup_subtotals'),
]
