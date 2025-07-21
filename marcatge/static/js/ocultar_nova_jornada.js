// Assegurem que jQuery estigui disponible i esperem a que el DOM estigui llest
window.addEventListener('load', function () {
  const $ = django.jQuery;

  console.log("📦 DOM carregat — executant toggleNovaJornada()");

  function toggleNovaJornada() {
    const forcar = $('#id_forcar_jornada_diaria').is(':checked');
    const novaJornadaRow = $('#id_nova_jornada_diaria').closest('.form-group');

    console.log("🛠 forcar =", forcar);

    if (forcar) {
      novaJornadaRow.show();
    } else {
      novaJornadaRow.hide();
    }
  }

  $('#id_forcar_jornada_diaria').on('change', toggleNovaJornada);
  toggleNovaJornada();
});
