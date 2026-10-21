// Toont een voorbeeldbeeld naast de muis als je over een regel van een lijst gaat.
// Alleen op schermen met een muis. De regels tonen zelf al een klein beeld, dus niets hangt van hover af.
if (matchMedia("(hover: hover) and (pointer: fine)").matches) {
  const marge = 16;
  const voorbeeld = document.createElement("img");
  voorbeeld.className = "voorbeeld";
  voorbeeld.alt = "";
  document.body.append(voorbeeld);

  document.querySelectorAll(".rij").forEach((rij) => {
    rij.addEventListener("mouseenter", () => {
      voorbeeld.src = rij.dataset.voorbeeld;
      voorbeeld.classList.add("zichtbaar");
    });
    rij.addEventListener("mousemove", (gebeurtenis) => {
      const { width, height } = voorbeeld.getBoundingClientRect();
      const links = gebeurtenis.clientX + 28 + width > innerWidth - marge ? gebeurtenis.clientX - 28 - width : gebeurtenis.clientX + 28;
      const boven = Math.min(Math.max(gebeurtenis.clientY - height / 2, marge), innerHeight - height - marge);
      voorbeeld.style.transform = `translate(${links}px, ${boven}px)`;
    });
    rij.addEventListener("mouseleave", () => voorbeeld.classList.remove("zichtbaar"));
  });
}
