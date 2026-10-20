// Toont de lokale tijd in Gent in de kop.
const klok = document.querySelector(".klok");
const formaat = new Intl.DateTimeFormat("nl-BE", { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Brussels" });

function toon() {
  klok.textContent = formaat.format(new Date());
}

toon();
setInterval(toon, 30000);
