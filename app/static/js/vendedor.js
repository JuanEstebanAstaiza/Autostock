/**
 * Autostock - JavaScript para Vendedor
 * Funcionalidades específicas del rol de vendedor
 */

document.addEventListener('DOMContentLoaded', function() {
    // Funcionalidad de búsqueda de productos
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        const productosContainer = document.querySelector('.productos-grid');
        setupSearch(searchInput, productosContainer, '/vendedor/api/productos/search');
    }

    // Funcionalidad de selección de productos en tarjetas
    const productoCards = document.querySelectorAll('.producto-card');
    productoCards.forEach(card => {
        card.addEventListener('click', function() {
            // Remover selección previa
            productoCards.forEach(c => c.classList.remove('selected'));
            // Seleccionar esta tarjeta
            this.classList.add('selected');

            // Llenar formulario con datos del producto
            const productoData = {
                id: this.dataset.id,
                nombre: this.dataset.nombre,
                precio: parseFloat(this.dataset.precio),
                stock: parseInt(this.dataset.stock),
                codigo: this.dataset.codigo
            };

            fillProductForm(productoData);
        });
    });

    // Funcionalidad de búsqueda por código
    const searchByCodeBtn = document.getElementById('search-by-code');
    if (searchByCodeBtn) {
        searchByCodeBtn.addEventListener('click', function() {
            const code = document.getElementById('product-code').value.trim();
            if (code) {
                searchProductByCode(code);
            } else {
                Utils.showNotification('Ingrese un código de producto', 'warning');
            }
        });
    }

    // Cálculo automático del total
    const quantityInput = document.getElementById('quantity');
    if (quantityInput) {
        quantityInput.addEventListener('input', calculateTotal);
    }

    // Validación del formulario de venta
    const saleForm = document.getElementById('sale-form');
    if (saleForm) {
        saleForm.addEventListener('submit', function(e) {
            const quantity = parseInt(quantityInput.value) || 0;
            const availableStock = parseInt(document.getElementById('available-stock').textContent) || 0;

            if (quantity > availableStock) {
                e.preventDefault();
                Utils.showNotification('No hay suficiente stock disponible', 'error');
                return;
            }

            if (quantity <= 0) {
                e.preventDefault();
                Utils.showNotification('La cantidad debe ser mayor a 0', 'warning');
                return;
            }

            // Mostrar confirmación
            const productName = document.getElementById('product-name').textContent;
            const total = document.getElementById('total-amount').textContent;

            if (!Utils.confirm(`¿Confirmar venta de ${productName} por ${total}?`)) {
                e.preventDefault();
            }
        });
    }

    // Funcionalidad de escaneo (simulado)
    const scanBtn = document.getElementById('scan-product');
    if (scanBtn) {
        scanBtn.addEventListener('click', function() {
            // Simular escaneo con un código de ejemplo
            const mockCodes = ['PROD001', 'PROD002', 'PROD003', 'LLANTA001', 'LLANTA002'];
            const randomCode = mockCodes[Math.floor(Math.random() * mockCodes.length)];

            document.getElementById('product-code').value = randomCode;
            Utils.showNotification(`Código escaneado: ${randomCode}`, 'info');
        });
    }
});

// Función para buscar producto por código
function searchProductByCode(code) {
    Utils.ajax(`/vendedor/api/productos/${code}`)
        .then(product => {
            fillProductForm(product);
            Utils.showNotification('Producto encontrado', 'success');
        })
        .catch(error => {
            Utils.showNotification('Producto no encontrado', 'error');
            clearProductForm();
        });
}

// Función para llenar el formulario con datos del producto
function fillProductForm(product) {
    document.getElementById('product-id').value = product.id;
    document.getElementById('product-name').textContent = product.nombre;
    document.getElementById('product-price').textContent = Utils.formatCurrency(product.precio);
    document.getElementById('available-stock').textContent = product.cantidad;
    document.getElementById('product-category').textContent = product.categoria || 'N/A';

    // Mostrar información del producto
    const productInfo = document.getElementById('product-info');
    if (productInfo) {
        productInfo.style.display = 'block';
    }

    // Habilitar campo de cantidad
    const quantityInput = document.getElementById('quantity');
    if (quantityInput) {
        quantityInput.disabled = false;
        quantityInput.focus();
    }

    // Calcular total inicial
    calculateTotal();
}

// Función para limpiar el formulario
function clearProductForm() {
    document.getElementById('product-id').value = '';
    document.getElementById('product-name').textContent = 'Seleccione un producto';
    document.getElementById('product-price').textContent = '$0.00';
    document.getElementById('available-stock').textContent = '0';
    document.getElementById('product-category').textContent = 'N/A';
    document.getElementById('quantity').value = '';
    document.getElementById('total-amount').textContent = '$0.00';

    const productInfo = document.getElementById('product-info');
    if (productInfo) {
        productInfo.style.display = 'none';
    }

    const quantityInput = document.getElementById('quantity');
    if (quantityInput) {
        quantityInput.disabled = true;
    }
}

// Función para calcular el total
function calculateTotal() {
    const priceText = document.getElementById('product-price').textContent;
    const price = parseFloat(priceText.replace(/[^0-9.-]+/g, '')) || 0;
    const quantity = parseInt(document.getElementById('quantity').value) || 0;
    const total = price * quantity;

    document.getElementById('total-amount').textContent = Utils.formatCurrency(total);
}

// Función para manejar resultados de búsqueda
window.handleSearchResults = function(data, container) {
    if (!data || !data.productos) return;

    container.innerHTML = '';

    data.productos.forEach(producto => {
        const card = document.createElement('div');
        card.className = 'producto-card';
        card.dataset.id = producto.id;
        card.dataset.nombre = producto.nombre;
        card.dataset.precio = producto.precio;
        card.dataset.stock = producto.cantidad;
        card.dataset.codigo = producto.codigo;

        card.innerHTML = `
            <h4>${producto.nombre}</h4>
            <p class="producto-codigo">${producto.codigo}</p>
            <p class="producto-precio">${Utils.formatCurrency(producto.precio)}</p>
            <p class="producto-stock">Stock: ${producto.cantidad}</p>
            <button class="btn btn-sm seleccionar-producto">Seleccionar</button>
        `;

        card.addEventListener('click', function() {
            fillProductForm(producto);
        });

        container.appendChild(card);
    });
};

// Funcionalidad de vista de inventario
function initializeInventoryView() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filter = this.dataset.filter;

            // Remover clase active de todos los botones
            filterButtons.forEach(btn => btn.classList.remove('active'));
            // Agregar clase active al botón clickeado
            this.classList.add('active');

            // Filtrar productos
            filterProducts(filter);
        });
    });
}

function filterProducts(filter) {
    const cards = document.querySelectorAll('.producto-card');

    cards.forEach(card => {
        const stock = parseInt(card.dataset.stock);
        let show = true;

        switch(filter) {
            case 'low-stock':
                show = stock <= 10;
                break;
            case 'out-of-stock':
                show = stock === 0;
                break;
            case 'available':
                show = stock > 0;
                break;
            default:
                show = true;
        }

        card.style.display = show ? 'block' : 'none';
    });
}

// Inicializar funcionalidades específicas de la página
if (document.querySelector('.productos-grid')) {
    initializeInventoryView();
}
