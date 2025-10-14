/**
 * Autostock - JavaScript para Administrador
 * Funcionalidades específicas del rol de administrador
 */

document.addEventListener('DOMContentLoaded', function() {
    // Funcionalidad de modales
    initializeModals();

    // Funcionalidad de formularios CRUD
    initializeCRUDForms();

    // Funcionalidad de tablas interactivas
    initializeDataTables();

    // Funcionalidad de reportes
    initializeReports();

    // Funcionalidad de exportación
    initializeExportFeatures();
});

// Inicializar modales
function initializeModals() {
    const modalTriggers = document.querySelectorAll('[data-modal]');
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.modal-close, .modal-cancel');

    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            const modalId = this.dataset.modal;
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.style.display = 'block';
                document.body.style.overflow = 'hidden';
            }
        });
    });

    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                modal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
    });

    // Cerrar modal al hacer click fuera
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
    });
}

// Inicializar formularios CRUD
function initializeCRUDForms() {
    // Formulario de productos
    const productForm = document.getElementById('product-form');
    if (productForm) {
        productForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const data = Object.fromEntries(formData);

            // Validaciones específicas
            if (parseFloat(data.precio) <= 0) {
                Utils.showNotification('El precio debe ser mayor a 0', 'error');
                return;
            }

            if (parseInt(data.cantidad) < 0) {
                Utils.showNotification('La cantidad no puede ser negativa', 'error');
                return;
            }

            // Enviar datos
            const method = data.id ? 'PUT' : 'POST';
            const url = data.id ? `/negocio/inventario/${data.id}` : '/negocio/inventario';

            Utils.ajax(url, {
                method: method,
                data: data
            })
            .then(response => {
                Utils.showNotification('Producto guardado exitosamente', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            })
            .catch(error => {
                Utils.showNotification('Error al guardar producto', 'error');
            });
        });
    }

    // Formulario de ventas
    const saleForm = document.getElementById('register-sale-form');
    if (saleForm) {
        // Cargar productos dinámicamente
        loadProductsForSale();

        // Cargar vendedores
        loadVendedoresForSale();

        saleForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const data = Object.fromEntries(formData);

            Utils.ajax('/negocio/ventas', {
                method: 'POST',
                data: data
            })
            .then(response => {
                Utils.showNotification('Venta registrada exitosamente', 'success');
                this.reset();
            })
            .catch(error => {
                Utils.showNotification('Error al registrar venta', 'error');
            });
        });
    }
}

// Cargar productos para formulario de ventas
function loadProductsForSale() {
    const productSelect = document.getElementById('sale-product-id');
    if (!productSelect) return;

    Utils.ajax('/api/products/for-sale')
        .then(products => {
            productSelect.innerHTML = '<option value="">Seleccione un producto</option>';
            products.forEach(product => {
                const option = document.createElement('option');
                option.value = product.id;
                option.textContent = `${product.nombre} (${product.cantidad} disponibles)`;
                option.dataset.stock = product.cantidad;
                productSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error cargando productos:', error);
        });
}

// Cargar vendedores para formulario de ventas
function loadVendedoresForSale() {
    const vendedorSelect = document.getElementById('sale-vendedor-id');
    if (!vendedorSelect) return;

    Utils.ajax('/api/vendedores')
        .then(vendedores => {
            vendedorSelect.innerHTML = '<option value="">Seleccione un vendedor</option>';
            vendedores.forEach(vendedor => {
                const option = document.createElement('option');
                option.value = vendedor.id;
                option.textContent = vendedor.nombre_usuario;
                vendedorSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error cargando vendedores:', error);
        });
}

// Inicializar tablas interactivas
function initializeDataTables() {
    const tables = document.querySelectorAll('.data-table');

    tables.forEach(table => {
        // Funcionalidad de ordenamiento
        const headers = table.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                const column = this.dataset.sort;
                const order = this.dataset.order === 'asc' ? 'desc' : 'asc';
                this.dataset.order = order;

                sortTable(table, column, order);
            });
        });

        // Funcionalidad de búsqueda en tabla
        const searchInput = document.querySelector(`#${table.id}-search`);
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                filterTable(table, this.value);
            });
        }
    });
}

// Ordenar tabla
function sortTable(table, column, order) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.sort((a, b) => {
        const aValue = a.querySelector(`td[data-${column}]`)?.textContent || '';
        const bValue = b.querySelector(`td[data-${column}]`)?.textContent || '';

        let comparison = 0;
        if (aValue < bValue) comparison = -1;
        if (aValue > bValue) comparison = 1;

        return order === 'asc' ? comparison : -comparison;
    });

    rows.forEach(row => tbody.appendChild(row));
}

// Filtrar tabla
function filterTable(table, query) {
    const rows = table.querySelectorAll('tbody tr');

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const show = text.includes(query.toLowerCase());
        row.style.display = show ? '' : 'none';
    });
}

// Inicializar reportes
function initializeReports() {
    // Gráficos de ventas
    const salesChart = document.getElementById('sales-chart');
    if (salesChart) {
        loadSalesData();
    }

    // Filtros de fecha
    const dateFilters = document.querySelectorAll('.date-filter');
    dateFilters.forEach(filter => {
        filter.addEventListener('change', function() {
            updateReports();
        });
    });
}

// Cargar datos de ventas para gráficos
function loadSalesData() {
    Utils.ajax('/negocio/api/ventas/data')
        .then(data => {
            renderSalesChart(data);
        })
        .catch(error => {
            console.error('Error cargando datos de ventas:', error);
        });
}

// Renderizar gráfico de ventas (simplificado)
function renderSalesChart(data) {
    const canvas = document.getElementById('sales-chart');
    if (!canvas) return;

    // Crear gráfico simple con SVG
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '300');

    // Implementación básica de gráfico de barras
    const maxValue = Math.max(...data.map(d => d.total));
    const barWidth = canvas.offsetWidth / data.length;

    data.forEach((item, index) => {
        const barHeight = (item.total / maxValue) * 250;
        const x = index * barWidth;
        const y = 280 - barHeight;

        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x + 5);
        rect.setAttribute('y', y);
        rect.setAttribute('width', barWidth - 10);
        rect.setAttribute('height', barHeight);
        rect.setAttribute('fill', '#1A2238');

        svg.appendChild(rect);
    });

    canvas.appendChild(svg);
}

// Actualizar reportes
function updateReports() {
    const startDate = document.getElementById('start-date')?.value;
    const endDate = document.getElementById('end-date')?.value;

    const params = new URLSearchParams();
    if (startDate) params.append('start', startDate);
    if (endDate) params.append('end', endDate);

    Utils.ajax(`/negocio/api/reportes?${params}`)
        .then(data => {
            updateReportsDisplay(data);
        })
        .catch(error => {
            console.error('Error actualizando reportes:', error);
        });
}

// Actualizar display de reportes
function updateReportsDisplay(data) {
    // Actualizar estadísticas
    const statsElements = document.querySelectorAll('[data-stat]');
    statsElements.forEach(element => {
        const stat = element.dataset.stat;
        if (data[stat] !== undefined) {
            element.textContent = data[stat];
        }
    });

    // Actualizar tablas
    updateReportsTable('top-products', data.topProducts);
    updateReportsTable('sales-by-date', data.salesByDate);
}

// Actualizar tabla de reportes
function updateReportsTable(tableId, data) {
    const tbody = document.querySelector(`#${tableId} tbody`);
    if (!tbody) return;

    tbody.innerHTML = '';

    data.forEach(item => {
        const row = document.createElement('tr');
        Object.values(item).forEach(value => {
            const cell = document.createElement('td');
            cell.textContent = value;
            row.appendChild(cell);
        });
        tbody.appendChild(row);
    });
}

// Inicializar funcionalidades de exportación
function initializeExportFeatures() {
    const exportButtons = document.querySelectorAll('.export-btn');

    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const type = this.dataset.type;
            const format = this.dataset.format || 'csv';

            exportData(type, format);
        });
    });
}

// Exportar datos
function exportData(type, format) {
    const url = `/negocio/reportes/export/${type}`;

    // Crear enlace temporal para descarga
    const link = document.createElement('a');
    link.href = url;
    link.download = `reporte_${type}_${Date.now()}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    Utils.showNotification('Exportación iniciada', 'info');
}

// Funcionalidad de eliminación con confirmación
document.addEventListener('click', function(e) {
    if (e.target.matches('[data-action="delete"]')) {
        e.preventDefault();

        const itemType = e.target.dataset.type || 'elemento';
        const itemName = e.target.dataset.name || '';

        if (Utils.confirm(`¿Está seguro de que desea eliminar ${itemType} "${itemName}"?`)) {
            const url = e.target.dataset.url || e.target.href;

            Utils.ajax(url, { method: 'DELETE' })
                .then(() => {
                    Utils.showNotification('Elemento eliminado exitosamente', 'success');
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                })
                .catch(error => {
                    Utils.showNotification('Error al eliminar elemento', 'error');
                });
        }
    }
});
