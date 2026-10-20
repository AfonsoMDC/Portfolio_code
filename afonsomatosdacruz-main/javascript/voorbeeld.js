// Toont een groot voorbeeldbeeld dat de muis volgt, als je over een regel van een lijst gaat.
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
    voorbeeld.style.transform = `translate(${gebeurtenis.clientX + 24}px, ${gebeurtenis.clientY - 120}px)`;
  });
  rij.addEventListener("mouseleave", () => voorbeeld.classList.remove("zichtbaar"));
});
