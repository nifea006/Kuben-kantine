// Function for "bestille fra kantina"
// Kundeinformasjon
function toggleKoststedInput() {
    const select = document.getElementById('koststedSelect');
    const input = document.getElementById('koststedInput');
    input.style.display = select.value === 'other' ? 'inline-block' : 'none';
    input.required = select.value === 'other';
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
    const pElement = document.querySelector('p.antall-p[name="item_' + itemId + '"]');
    let currentQuantity = parseInt(pElement.innerText, 10);
    if (isNaN(currentQuantity)) currentQuantity = 0;
    const newQuantity = Math.max(0, currentQuantity + delta);
    pElement.innerText = newQuantity;
    const hiddenInput = document.querySelector('input[name="item_' + itemId + '"][type="number"]');
    if (hiddenInput) hiddenInput.value = newQuantity;
}

// Replace the p with an input for direct editing
function editQuantity(itemId) {
    const pElement = document.querySelector('p.antall-p[name="item_' + itemId + '"]');
    if (!pElement) return;

    const currentQuantity = parseInt(pElement.innerText, 10) || 0;
    const inputElement = document.createElement('input');
    inputElement.value = currentQuantity;

    pElement.replaceWith(inputElement);
    inputElement.focus();
    inputElement.select();

    function commit() {
        let inputValue = parseInt(inputElement.value, 10);
        if (isNaN(inputValue) || inputValue < 0) inputValue = 0;
        const hiddenInput = document.querySelector('.antall-input[name="item_' + itemId + '"]');
        if (hiddenInput) hiddenInput.value = inputValue;

        const newP = document.createElement('p');
        newP.className = 'antall-p';
        newP.setAttribute('name', 'item_' + itemId);
        newP.setAttribute('tabindex', '0');
        newP.onclick = function () { editQuantity(itemId); };
        newP.innerText = inputValue;
        inputElement.replaceWith(newP);
    }

    function cancel() {
        const originalP = document.createElement('p');
        originalP.className = 'antall-p';
        originalP.setAttribute('name', 'item_' + itemId);
        originalP.setAttribute('tabindex', '0');
        originalP.onclick = function () { editQuantity(itemId); };
        originalP.innerText = currentQuantity;
        inputElement.replaceWith(originalP);
    }

    inputElement.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            commit();
        } else if (e.key === 'Escape') {
            cancel();
        }
    });
    inputElement.addEventListener('blur', function () {
        commit();
    });
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
    const hideMainChoices = document.querySelectorAll('.main-menu-li');
    if (submenu.style.display === 'none') {
        submenu.style.display = 'block';
        hideMainChoices.forEach(li => {
            li.style.display = 'none';
        });
    } else {
        submenu.style.display = 'none';
        hideMainChoices.forEach(li => {
            li.style.display = 'block';
        });
    }
}

// // Edit menu
// let changes = {};
// let newItems = {};
// let deletedItems = new Set();
// let positionChanges = {};

// // Create an item
// function addMenuItemToCategory(category) {
//     const itemId = 'menu-item_' + Date.now();
//     const menuDiv = document.getElementById('Meny');

//     let categorySection = Array.from(menuDiv.querySelectorAll('h3')).find(h => h.textContent === category);
//     let categoryDiv = categorySection?.nextElementSibling;

//     if (!categoryDiv || !categoryDiv.classList.contains('menu-category')) {
//         return;
//     }

//     const menuItem = document.createElement('div');
//     menuItem.className = 'menu-item';
//     menuItem.dataset.id = itemId;
//     menuItem.innerHTML = `
//         <img src="#" alt="Bilde av ny vare" width="150" height="150" style="cursor: pointer;" onclick="editItemImage('${itemId}')">
//         <div class="information">
//             <p style="text-align: center; cursor: pointer;">Ny vare</p>
//             <p class="les-mer" onclick="toggleReadMore(event)">Les mer ▼</p>
//             <p class="description" style="display: none;">Beskrivelse</p>
//             <p>0 kr</p>
//         </div>
//     `;

//     categoryDiv.appendChild(menuItem);
//     newItems[itemId] = { category, title: 'Ny vare', description: 'Beskrivelse', price: 0, image_url: '' };
//     setupEditableElements();
// }

// // Edit item image
// function editItemImage(itemId) {
//     const imageInput = document.getElementById('Bilde av ' + itemId);
//     const image = document.querySelector(`[data-id="${itemId}"] img`);

//     if (imageInput.style.display === 'none') {
//         image.style.display = 'none';
//         imageInput.style.display = 'block';
//         imageInput.click();
//     } else {
//         image.style.display = 'block';
//         imageInput.style.display = 'none';
//     }
// }

// // Make elements editable
// function makeTextEditable(element, itemId, field) {
//     if (element.querySelector('input')) return;

//     const oldValue = element.textContent.trim().replace('kr', '').trim();
//     const input = document.createElement('input');
//     input.type = field === 'price' ? 'number' : 'text';
//     input.value = oldValue;
//     if (field === 'price') input.step = '1';
//     input.style.width = 'min-content';
//     input.style.padding = '6px';

//     element.innerHTML = '';
//     element.appendChild(input);
//     input.focus();
//     input.select();

//     function saveEdit() {
//         let newValue = input.value.trim();
//         if (!newValue) newValue = oldValue;

//         if (field === 'price') {
//             newValue = parseFloat(newValue) || 0;
//             element.textContent = newValue + ' kr';
//         } else {
//             element.textContent = newValue;
//         }

//         if (itemId && itemId.toString().startsWith('menu-item_')) {
//             if (!newItems[itemId]) newItems[itemId] = {};
//             newItems[itemId][field] = newValue;
//         } else if (itemId) {
//             if (!changes[itemId]) changes[itemId] = {};
//             changes[itemId][field] = newValue;
//         }
//     }

//     input.addEventListener('blur', saveEdit);
//     input.addEventListener('keydown', (e) => {
//         if (e.key === 'Enter') saveEdit();
//         if (e.key === 'Escape') element.textContent = oldValue;
//     });
// }

// // Make the elements "clickable"
// function setupEditableElements() {
//     document.querySelectorAll('.menu-item').forEach(item => {
//         const itemId = item.dataset.id;

//         // Title
//         const titleEl = item.querySelector('p[style*="text-align: center"]');
//         if (titleEl && !titleEl.onclick) {
//             titleEl.style.cursor = 'pointer';
//             titleEl.onclick = () => makeTextEditable(titleEl, itemId, 'title');
//         }

//         // Description
//         const descEl = item.querySelector('.description');
//         if (descEl && !descEl.editableSetup) {
//             descEl.style.cursor = 'pointer';
//             descEl.onclick = (e) => {
//                 e.stopPropagation();
//                 makeTextEditable(descEl, itemId, 'description');
//             };
//             descEl.editableSetup = true;
//         }

//         // Price
//         const priceEls = item.querySelectorAll('p');
//         const priceEl = Array.from(priceEls).find(p => p.textContent.includes('kr'));
//         if (priceEl && !priceEl.editableSetup) {
//             priceEl.style.cursor = 'pointer';
//             priceEl.onclick = () => makeTextEditable(priceEl, itemId, 'price');
//             priceEl.editableSetup = true;
//         }
//     });
// }

// // Delete menu item
// function deleteMenuItem(itemId) {
//     const menuItem = document.querySelector(`[data-id="${itemId}"]`);
//     if (!menuItem) return;

//     if (confirm('Er du sikker på at du vil slette denne varen?')) {
//         menuItem.remove();
//         if (!itemId.toString().startsWith('menu-item_')) {
//             deletedItems.add(itemId);
//         } else {
//             delete newItems[itemId];
//         }
//     }
// }

// // Update item position in DOM
// function updateItemPosition(itemId, direction) {
//     const item = document.querySelector(`[data-id="${itemId}"]`);
//     if (!item) return;

//     const parent = item.parentElement;
//     const items = Array.from(parent.querySelectorAll('.menu-item'));
//     const currentIndex = items.indexOf(item);

//     if (direction === 'left' && currentIndex > 0) {
//         item.parentElement.insertBefore(item, items[currentIndex - 1]);
//     } else if (direction === 'right' && currentIndex < items.length - 1) {
//         items[currentIndex + 1].parentElement.insertBefore(items[currentIndex + 1], item);
//     }

//     if (!itemId.toString().startsWith('menu-item_')) {
//         positionChanges[itemId] = currentIndex + (direction === 'left' ? -1 : 1);
//     }
// }

// // Save all changes to database
// function saveMenu() {
//     const menuName = document.querySelector('[data-menu-name]')?.dataset.menuName || 'kantine';

//     document.querySelectorAll('.menu-item').forEach((item, idx) => {
//         const itemId = item.dataset.id;
//         if (!itemId.toString().startsWith('menu-item_')) {
//             positionChanges[itemId] = idx;
//         }
//     });

//     const payload = {
//         menu: menuName,
//         changes: changes,
//         newItems: newItems,
//         deletedItems: Array.from(deletedItems),
//         positions: positionChanges
//     };

//     fetch('/rediger-meny/mass-save', {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify(payload)
//     })
//         .then(r => r.json())
//         .then(data => {
//             if (data.ok) {
//                 alert('Meny lagret med suksess!');
//                 changes = {};
//                 newItems = {};
//                 deletedItems = new Set();
//                 positionChanges = {};
//             } else {
//                 alert('Feil ved lagring: ' + (data.error || 'Ukjent feil'));
//             }
//         })
//         .catch(e => alert('Nettverksfeil: ' + e));
// }

// document.addEventListener('DOMContentLoaded', setupEditableElements);