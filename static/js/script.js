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

// Require at least one item in the cart before submitting the form
function validateOrder(event) {
    const inputs = document.querySelectorAll('input[name^="item_"]');
    const Meny = document.getElementById('Meny');
    let totalSelected = 0;

    inputs.forEach(input => {
        const value = parseInt(input.value || "0", 10);
        if (value > 0) totalSelected++;
    });

    if (totalSelected === 0 && Meny.style.display != 'none') {
        event.preventDefault();
        alert("Du må velge minst en vare før du sender inn bestillingen!");
        return false;
    }

    return true;
}

// Show and hide description
function toggleReadMore(event) {
    const triggerElement = event.currentTarget;
    const descriptionElement = triggerElement.nextElementSibling;

    if (!descriptionElement) return;

    if (descriptionElement.style.display === 'none' || descriptionElement.style.display === '') {
        descriptionElement.style.display = 'block';
        triggerElement.innerText = 'Skjul detaljer ▲';
    } else {
        descriptionElement.style.display = 'none';
        triggerElement.innerText = 'Vis detaljer ▼';
    }
}

// Admin users: search by name
function filterUsers() {
    const input = document.getElementById("userSearch");
    if (!input) return;
    const value = input.value.trim().toLowerCase();
    const userCards = document.querySelectorAll(".user-card");
    userCards.forEach(card => {
        const name = card.dataset.userName || "";
        card.style.display = name.includes(value) ? "" : "none";
    });
    const receiptCards = document.querySelectorAll(".receipt-card");
    receiptCards.forEach(card => {
        const name = (card.dataset.clientName || "").toLowerCase();
        card.style.display = name.includes(value) ? "" : "none";
    });
}

// Menu editor: mark item for deletion
function markDelete(itemId) {
    const item = document.getElementById(`menu_item_${itemId}`);
    const hidden = document.querySelector(`input[name="delete_${itemId}"]`);
    if (!item || !hidden) return;

    const shouldDelete = hidden.value !== "1";
    hidden.value = shouldDelete ? "1" : "0";
    item.classList.toggle("committing-delete", shouldDelete);
}

// Menu editor: add new item to a category
let newItemCounter = 0;
function addMenuItem(category) {
    newItemCounter += 1;
    const idx = newItemCounter;
    const container = document.querySelector(`.menu-category[data-category="${category}"]`);
    if (!container) return;

    const wrapper = document.createElement("div");
    wrapper.className = "menu-item";
    wrapper.id = `new_menu_item_${idx}`;

    wrapper.innerHTML = `
        <input type="hidden" name="new_item_index" value="${idx}">
        <div class="menu-item-image">
            <img id="image_preview_new_${idx}" src="" alt="Bilde" width="150" height="200"
                onclick="triggerImageUpload('image_file_new_${idx}')">
            <input class="image-input" type="file" name="new_image_file_${idx}" id="image_file_new_${idx}"
                accept=".png,.jpg,.jpeg,.gif,.webp" onchange="previewImage(event, 'image_preview_new_${idx}')">
            <input type="hidden" name="new_image_url_${idx}" value="">
        </div>
        <div class="information">
            <input class="plain-input display-title" type="text" name="new_title_${idx}" placeholder="Tittel">
            <select class="plain-input display-category" name="new_category_${idx}">
                ${buildCategoryOptions(category)}
            </select>
            <p class="les-mer display-field" onclick="toggleReadMore(event)">Vis detaljer ▼</p>
            <textarea class="plain-input description" style="display: none;" name="new_description_${idx}" rows="3" placeholder="Beskrivelse"></textarea>
            <input class="plain-input display-price" type="text" name="new_price_${idx}" placeholder="Pris (kr)">
        </div>
        <label class="checkbox-inline">
            <input type="checkbox" name="new_active_${idx}" style="width: fit-content;" checked>
            Tilgjengelig
        </label>
        <button type="button" class="btn-danger" onclick="removeNewItem(${idx})">
            <svg class="icon">
                <use href="#icon-trash"></use>
            </svg>
            Slett
        </button>
    `;

    container.insertBefore(wrapper, container.querySelector(".menu-add"));
}

function removeNewItem(idx) {
    const item = document.getElementById(`new_menu_item_${idx}`);
    if (item) item.remove();
}

function triggerImageUpload(inputId) {
    const input = document.getElementById(inputId);
    if (input) input.click();
}

function previewImage(event, imgId) {
    const img = document.getElementById(imgId);
    if (!img) return;
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    if (img.dataset.objectUrl) {
        URL.revokeObjectURL(img.dataset.objectUrl);
    }
    const url = URL.createObjectURL(file);
    img.src = url;
    img.dataset.objectUrl = url;
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function getCategoryNames() {
    return Array.from(document.querySelectorAll(".category-block")).map(b => b.dataset.category);
}

function buildCategoryOptions(selected) {
    return getCategoryNames()
        .map(name => {
            const safe = escapeHtml(name);
            const isSelected = name === selected ? " selected" : "";
            return `<option value="${safe}"${isSelected}>${safe}</option>`;
        })
        .join("");
}

function updateCategorySelectOptions() {
    const selects = document.querySelectorAll("select.display-category");
    const names = getCategoryNames();
    selects.forEach(select => {
        const current = select.value || select.dataset.selected || "";
        select.innerHTML = names
            .map(name => {
                const safe = escapeHtml(name);
                const isSelected = name === current ? " selected" : "";
                return `<option value="${safe}"${isSelected}>${safe}</option>`;
            })
            .join("");
        if (current && !names.includes(current)) {
            const opt = document.createElement("option");
            opt.value = current;
            opt.textContent = current;
            opt.selected = true;
            select.prepend(opt);
        }
    });
}

function rebuildCategoryOrderInputs() {
    const container = document.getElementById("categoryOrderInputs");
    if (!container) return;
    container.innerHTML = "";
    getCategoryNames().forEach(name => {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = "category_order";
        input.value = name;
        container.appendChild(input);
    });
}

function moveCategory(button, direction) {
    const block = button.closest(".category-block");
    if (!block) return;
    const sibling = direction < 0 ? block.previousElementSibling : block.nextElementSibling;
    if (!sibling || !sibling.classList.contains("category-block")) return;
    if (direction < 0) {
        block.parentNode.insertBefore(block, sibling);
    } else {
        block.parentNode.insertBefore(sibling, block);
    }
    rebuildCategoryOrderInputs();
}

function addCategory() {
    const input = document.getElementById("newCategoryName");
    if (!input) return;
    const name = input.value.trim();
    if (!name) return;

    const existing = getCategoryNames();
    if (existing.includes(name)) {
        input.value = "";
        return;
    }

    const block = document.createElement("div");
    block.className = "category-block";
    block.dataset.category = name;

    const header = document.createElement("div");
    header.className = "category-header";

    const title = document.createElement("input");
    title.type = "text";
    title.className = "plain-input category-name-input";
    title.value = name;
    title.addEventListener("input", () => renameCategory(title));

    const actions = document.createElement("div");
    actions.className = "category-actions";

    const btnUp = document.createElement("button");
    btnUp.type = "button";
    btnUp.innerHTML = `
    <svg class="icon">
        <use href="#icon-arrow-up"></use>
    </svg>
    `;
    btnUp.addEventListener("click", () => moveCategory(btnUp, -1));

    const btnDown = document.createElement("button");
    btnDown.type = "button";
    btnDown.innerHTML = `
    <svg class="icon">
        <use href="#icon-arrow-down"></use>
    </svg>
    `;
    btnDown.addEventListener("click", () => moveCategory(btnDown, 1));

    const btnDelete = document.createElement("button");
    btnDelete.type = "button";
    btnDelete.className = "btn-danger";
    btnDelete.innerHTML = `
    <svg class="icon">
        <use href="#icon-trash"></use>
    </svg>
    `;
    btnDelete.addEventListener("click", () => deleteCategory(btnDelete));

    actions.appendChild(btnUp);
    actions.appendChild(btnDown);
    actions.appendChild(btnDelete);

    header.appendChild(title);
    header.appendChild(actions);

    const menuCategory = document.createElement("div");
    menuCategory.className = "menu-category";
    menuCategory.dataset.category = name;

    const menuAdd = document.createElement("div");
    menuAdd.className = "menu-item menu-add";
    menuAdd.style.cursor = "pointer";
    menuAdd.innerHTML = `
        <svg>
            <use href="#icon-plus"></use>
        </svg>
        <span>Legg til vare</span>
    `;
    menuAdd.addEventListener("click", () => addMenuItem(name));

    menuCategory.appendChild(menuAdd);

    const hidden = document.createElement("input");
    hidden.type = "hidden";
    hidden.name = "new_category";
    hidden.value = name;

    const hiddenName = document.createElement("input");
    hiddenName.type = "hidden";
    hiddenName.name = "category_name";
    hiddenName.value = name;

    const hiddenDeleted = document.createElement("input");
    hiddenDeleted.type = "hidden";
    hiddenDeleted.name = `category_deleted_${name}`;
    hiddenDeleted.value = "0";

    block.appendChild(header);
    block.appendChild(menuCategory);
    block.appendChild(hidden);
    block.appendChild(hiddenName);
    block.appendChild(hiddenDeleted);

    const menuSection = document.getElementById("Meny");
    menuSection.appendChild(block);

    input.value = "";
    updateCategorySelectOptions();
    rebuildCategoryOrderInputs();
}

function renameCategory(inputEl) {
    const block = inputEl.closest(".category-block");
    if (!block) return;
    const oldName = block.dataset.category;
    const newName = inputEl.value.trim() || oldName;

    block.dataset.category = newName;

    const hiddenName = block.querySelector('input[name="category_name"]');
    if (hiddenName) hiddenName.value = newName;

    const hiddenDeleted = block.querySelector(`input[name="category_deleted_${oldName}"]`);
    if (hiddenDeleted) hiddenDeleted.name = `category_deleted_${newName}`;

    block.querySelectorAll('input[name^="old_category_"]').forEach(i => {
        i.value = newName;
    });

    updateCategorySelectOptions();
    rebuildCategoryOrderInputs();
}

function deleteCategory(button) {
    const block = button.closest(".category-block");
    if (!block) return;
    const name = block.dataset.category;
    const hiddenDeleted = block.querySelector(`input[name="category_deleted_${name}"]`);
    if (hiddenDeleted) hiddenDeleted.value = "1";
    block.style.display = "none";
    updateCategorySelectOptions();
    rebuildCategoryOrderInputs();
}



// Submenu function
function updateDropdownIcon(container, isOpen) {
    if (!container) return;
    const useEl = container.querySelector(".dropdown-toggle-icon use");
    if (!useEl) return;
    useEl.setAttribute("href", isOpen ? "#icon-minus" : "#icon-plus");
}

function toggleSubMenu(event) {
    const button = event?.currentTarget;
    const container = button ? button.closest(".menu-dropdown") : null;
    const submenu = container ? container.querySelector(".submenu") : document.querySelector(".submenu");
    if (!submenu) return;
    const isOpen = submenu.classList.toggle("open");
    if (container) {
        container.classList.toggle("open", isOpen);
        updateDropdownIcon(container, isOpen);
    }
}



// Handle action
async function handleAction(event, targetId, actionType) {
    event.preventDefault();
    const form = event.target;
    const card = document.getElementById(targetId);

    card.classList.add('committing-' + actionType);

    try {
        const response = await fetch(form.action, { method: 'POST' });

        if (response.ok) {
            if (actionType === 'delete') {
                card.classList.add('deleted-animation');
                setTimeout(() => card.remove(), 600);
            } else {
                card.classList.add('success-animation');
                setTimeout(() => window.location.reload(), 500);
            }
        } else {
            card.classList.remove('committing-' + actionType);
            alert("Action failed.");
        }
    } catch (error) {
        card.classList.remove('committing-' + actionType);
        console.error("Error:", error);
    }
}



// Dark mode
document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("themeToggle");
    const iconUse = document.getElementById("themeIconUse");
    const iconSVG = document.getElementById("themeIconSVG");
    const navToggle = document.querySelector(".nav-toggle");
    const navDrawer = document.getElementById("navDrawer");
    const navCloseTargets = document.querySelectorAll("[data-nav-close]");

    const form = document.getElementById("menyEditorForm");
    if (form) {
        rebuildCategoryOrderInputs();
        updateCategorySelectOptions();
        form.addEventListener("submit", rebuildCategoryOrderInputs);
    }

    if (navToggle && navDrawer) {
        const closeDrawer = () => {
            navDrawer.classList.remove("open");
            navToggle.setAttribute("aria-expanded", "false");
            document.body.classList.remove("nav-locked");
        };

        navToggle.addEventListener("click", () => {
            const isOpen = navDrawer.classList.toggle("open");
            navToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
            document.body.classList.toggle("nav-locked", isOpen);
        });

        navCloseTargets.forEach(btn => btn.addEventListener("click", closeDrawer));
        navDrawer.querySelectorAll("a").forEach(link => link.addEventListener("click", closeDrawer));
    }

    document.querySelectorAll("[data-menu-toggle]").forEach(button => {
        button.addEventListener("click", toggleSubMenu);
    });

    const dropdownToggles = document.querySelectorAll("[data-dropdown-toggle]");
    if (dropdownToggles.length) {
        const closeDropdowns = () => {
            document.querySelectorAll(".nav-dropdown.open").forEach(dropdown => {
                dropdown.classList.remove("open");
                const toggle = dropdown.querySelector("[data-dropdown-toggle]");
                if (toggle) toggle.setAttribute("aria-expanded", "false");
                updateDropdownIcon(dropdown, false);
            });
        };

        dropdownToggles.forEach(toggle => {
            toggle.addEventListener("click", event => {
                event.stopPropagation();
                const dropdown = toggle.closest(".nav-dropdown");
                if (!dropdown) return;
                const isOpen = dropdown.classList.toggle("open");
                toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
                updateDropdownIcon(dropdown, isOpen);
                document.querySelectorAll(".nav-dropdown").forEach(other => {
                    if (other !== dropdown) {
                        other.classList.remove("open");
                        const otherToggle = other.querySelector("[data-dropdown-toggle]");
                        if (otherToggle) otherToggle.setAttribute("aria-expanded", "false");
                        updateDropdownIcon(other, false);
                    }
                });
            });
        });

        document.addEventListener("click", event => {
            if (!event.target.closest(".nav-dropdown")) {
                closeDropdowns();
            }
        });

        document.addEventListener("keydown", event => {
            if (event.key === "Escape") closeDropdowns();
        });
    }

    if (!btn || !iconUse) return;

    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
        document.body.classList.add("dark");
        iconUse.setAttribute("href", "#icon-sun");
    }

    btn.addEventListener("click", () => {
        const isDark = document.body.classList.toggle("dark");

        localStorage.setItem("theme", isDark ? "dark" : "light");

        if (isDark) {
            iconSVG.style.transform = "rotate(180deg)";
            iconSVG.style.transition = "transform 0.7s ease";
            iconUse.setAttribute("href", "#icon-sun");
        } else {
            iconSVG.style.transform = "rotate(0deg)";
            iconSVG.style.transition = "transform 0.7s ease";
            iconUse.setAttribute("href", "#icon-moon");
        }
    });

});

// Back to top
const backToTop = document.getElementById("backToTop");

function updateBackToTopVisibility() {
    if (!backToTop) return;
    backToTop.style.display = window.scrollY > 150 ? "block" : "none";
}

if (backToTop) {
    window.addEventListener("scroll", updateBackToTopVisibility, { passive: true });
    backToTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
}

// Back to bottom
window.addEventListener('beforeunload', () => {
    sessionStorage.setItem('scrollPos', window.scrollY);
});

window.addEventListener('load', () => {
    const scrollPos = sessionStorage.getItem('scrollPos');
    if (scrollPos) window.scrollTo(0, parseInt(scrollPos, 10));
    sessionStorage.removeItem('scrollPos');
    updateBackToTopVisibility();
});
