// Function for "bestille fra kantina"
// Kundeinformasjon
function toggleKoststedInput() {
    const select = document.getElementById('koststedSelect');
    const label = document.getElementById('koststedLabelInput');

    label.style.display = select.value === 'other' ? 'inline-block' : 'none';
    label.required = select.value === 'other';
}

// Dato
function toggleSpiseIKantina() {
    const checkbox = document.getElementById('spise_i_kantina');
    const antallContainer = document.getElementById('antallContainer');
    const Meny = document.getElementById('Meny');

    antallContainer.style.display = checkbox.checked ? 'flex' : 'none';
    antallContainer.required = checkbox.checked;
    Meny.style.display = checkbox.checked ? 'none' : 'block';
}



// Menu
// Add and remove items from "cart"
function changeQuantity(itemId, delta) {
    const pElement = document.querySelector('p.antall-p[name="' + itemId + '"]');

    let currentQuantity = parseInt(pElement.innerText, 10);
    if (isNaN(currentQuantity)) currentQuantity = 0;

    const newQuantity = Math.max(0, currentQuantity + delta);
    pElement.innerText = newQuantity;

    const hiddenInput = document.querySelector('input[name="item_' + itemId + '"][type="number"]');
    if (hiddenInput) hiddenInput.value = newQuantity;
}

// Replace the p with an input for direct editing
function editQuantity(itemId) {
    const p = document.querySelector(`p.antall-p[name="${itemId}"]`);
    if (!p) return;

    const currentValue = parseInt(p.innerText, 10) || 0;

    const width = p.offsetWidth + 40 + "px";

    const input = document.createElement("input");
    input.type = "number";
    input.value = currentValue;
    input.className = "antall-input-edit";
    input.style.width = width;
    input.style.textAlign = "center";

    p.replaceWith(input);
    input.focus();
    input.select();

    function restore(newValue) {
        const newP = document.createElement("p");
        newP.className = "antall-p";
        newP.setAttribute("name", itemId);
        newP.setAttribute("tabindex", "0");
        newP.onclick = () => editQuantity(itemId);
        newP.innerText = newValue;
        input.replaceWith(newP);
    }

    function commit() {
        let newValue = parseInt(input.value, 10);
        if (isNaN(newValue) || newValue < 0) newValue = 0;

        const hidden = document.querySelector(`input.antall-input[name="item_${itemId}"]`);
        if (hidden) hidden.value = newValue;
        restore(newValue);
    }

    function cancel() {
        restore(currentValue);
    }

    input.addEventListener("keydown", e => {
        if (e.key === "Enter") commit();
        if (e.key === "Escape") cancel();
    });

    input.addEventListener("blur", commit);
}


// Show and hide description
function toggleReadMore(event) {
    const lesMerElement = event.target;
    const descriptionElement = lesMerElement.nextElementSibling;

    if (descriptionElement.style.display === 'none') {
        descriptionElement.style.display = 'block';
        lesMerElement.innerText = 'Les mindre ▲';
    } else {
        descriptionElement.style.display = 'none';
        lesMerElement.innerText = 'Les mer ▼';
    }
}

// Submenu function
function toggleSubMenu() {
    const submenu = document.querySelector('.submenu');
    const iconUse = document.getElementById('plusMinusIcon');

    submenu.classList.toggle('open');

    if (submenu.classList.contains('open')) {
        iconUse.setAttribute('href', '#icon-minus');
    } else {
        iconUse.setAttribute('href', '#icon-plus');
    }
}

// Dark mode
document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("themeToggle");
    const icon = document.getElementById("themeIcon");

    if (!btn || !icon) return;

    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
        document.body.classList.add("dark");
        icon.setAttribute("href", "#icon-sun");
    }

    btn.addEventListener("click", () => {
        const isDark = document.body.classList.toggle("dark");

        localStorage.setItem("theme", isDark ? "dark" : "light");

        icon.setAttribute("href", isDark ? "#icon-sun" : "#icon-moon");
    });
});

// Back to top
const backToTop = document.getElementById("backToTop");

window.addEventListener("scroll", () => {
    if (window.scrollY > 150) {
        backToTop.style.display = 'block';
    } else {
        backToTop.style.display = 'none';
    }
});

if (backToTop) {
    backToTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
}