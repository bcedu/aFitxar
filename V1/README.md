# aFitxar
Engega un servidor que ofereix un portal per fitxar en la jornada laboral tal i com estableix 
el [Real Decreto-ley 8/2019, de 8 de marzo](https://www.boe.es/buscar/doc.php?id=BOE-A-2019-3481)
i seguint els requeriments descrits en aquesta [guía](https://factorialhr.es/wp-content/uploads/2019/05/15113751/guia-control-horario.pdf).


## Funcionament

Cada cop que algú fitxa es guarda la hora del marcatge, el codi de treballador introduït i la direcció IP de on ha arribat el marcatge.

Hi ha 3 accións disponibles desde el portal de marcatge:

- **Entrada**: per marcar es comença la jornada laboral.
<p align="center">
 <img src="/marcatge/fixtures/entrada.gif" width="100%"/></a>
</p>

- **Sortida**: per marcar s'acaba la jornada laboral.
<p align="center">
 <img src="/marcatge/fixtures/sortida.gif" width="100%"/></a>
</p>

- **Consulta**: per marcar consultar les hores treballades en el dia d'avui.
<p align="center">
 <img src="/marcatge/fixtures/consulta.gif" width="100%"/></a>
</p>


## Portal d'administrador

Desde el portal d'administrador es poden consultar tots els treballadors donats d'alta i els seus marcatges.

<p float="center">
  <img src="/marcatge/fixtures/llista_treballadors.png" width="49%" />
  <img src="/marcatge/fixtures/llista_marcatges.png" width="49%" />
</p>


Tambe permet modificar i donar d'alta nous treballadors.

<p align="center">
 <img src="/marcatge/fixtures/formulari_treballador.png" width="100%"/></a>
</p>
