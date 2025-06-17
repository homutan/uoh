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

function selectLatest(value) {
  var params = new URLSearchParams(window.location.search);
  params.set("latest", value);
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

function filterItems(text) {
  len = 0;
  filtered = 0;

  document.querySelectorAll(".item").forEach((item) => {
    len += 1;
    if (!item.textContent.toLowerCase().includes(text)) {
      item.hidden = true;
      filtered += 1;
    } else {
      item.hidden = false;
    }
  });

  if (filtered > 0) {
    document.querySelector("#filter-status").textContent = `${len - filtered}/${len}`;
  } else {
    document.querySelector("#filter-status").textContent = `${len}/${len}`;
  }
}
