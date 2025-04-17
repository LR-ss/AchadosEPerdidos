function toggleSenha() {
    var campoSenha = document.getElementById("senha");
    if (campoSenha.type === "password") {
      campoSenha.type = "text";
    } else {
      campoSenha.type = "password";
    }
  }