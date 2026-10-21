// Verstuurt het contactformulier naar Formspree. Wordt alleen geladen op de startpagina.
const formulier = document.querySelector("#contact form");
const status = formulier.querySelector(".status-formulier");
const knop = formulier.querySelector("button[type=submit]");

formulier.addEventListener("submit", async (gebeurtenis) => {
  gebeurtenis.preventDefault();
  knop.disabled = true;
  status.dataset.toestand = "bezig";
  status.textContent = formulier.dataset.bezig;
  try {
    const antwoord = await fetch(formulier.action, {
      method: "POST",
      body: new FormData(formulier),
      headers: { Accept: "application/json" },
    });
    if (!antwoord.ok) throw new Error(`Formspree antwoordde met status ${antwoord.status}`);
    formulier.reset();
    status.dataset.toestand = "gelukt";
    status.textContent = formulier.dataset.gelukt;
  } catch (fout) {
    console.error(fout);
    status.dataset.toestand = "mislukt";
    status.textContent = formulier.dataset.mislukt;
  } finally {
    knop.disabled = false;
  }
});
