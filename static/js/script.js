function abrirModal(src) {
    document.getElementById("modalImagem").style.display = "block";
    document.getElementById("imgAmpliada").src = src;
  }

  function fecharModal() {
    document.getElementById("modalImagem").style.display = "none";
  }