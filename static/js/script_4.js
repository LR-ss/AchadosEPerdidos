
  document.addEventListener('DOMContentLoaded', function() {

    const tempoParaSumir = 4000; // 4 segundos

    setTimeout(() => {
      document.querySelectorAll('.alert').forEach(el => {

        el.classList.add('hide');

        setTimeout(() => el.remove(), 500);

      });
    }, tempoParaSumir);
  });
