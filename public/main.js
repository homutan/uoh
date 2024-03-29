function selectToken(value) {
  var params = new URLSearchParams(window.location.search);
  params.set("token", value);
  window.location.search = params.toString();
}

function selectSnapshot(value) {
  var params = new URLSearchParams(window.location.search);
  params.set("snapshot", value);
  window.location.search = params.toString();
}

function forceUpdate() {
  button = document.querySelector("#update-button");
  button.disabled = true;

  fetch("/update", { method: "POST" })
    .then(
      (_) => selectSnapshot("latest"),
      (reject) => console.error(reject)
    )
    .finally((_) => (button.disabled = false));
}
