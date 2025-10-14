/**
 * Autostock - JavaScript para SuperAdministrador
 * Funcionalidades específicas del rol de superadministrador
 */

document.addEventListener('DOMContentLoaded', function() {
    // Funcionalidad de gestión de negocios
    initializeBusinessManagement();

    // Funcionalidad de gestión de planes
    initializePlanManagement();

    // Funcionalidad de backups
    initializeBackupFeatures();

    // Funcionalidad de métricas globales
    initializeGlobalMetrics();
});

// Inicializar gestión de negocios
function initializeBusinessManagement() {
    // Formulario de creación/edición de negocio
    const businessForm = document.getElementById('business-form');
    if (businessForm) {
        businessForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const data = Object.fromEntries(formData);

            // Validaciones
            if (!data.nombre_negocio || !data.propietario) {
                Utils.showNotification('Nombre del negocio y propietario son requeridos', 'error');
                return;
            }

            const method = data.id ? 'PUT' : 'POST';
            const url = data.id ? `/superadmin/negocios/${data.id}` : '/superadmin/negocios';

            Utils.ajax(url, {
                method: method,
                data: data
            })
            .then(response => {
                Utils.showNotification('Negocio guardado exitosamente', 'success');
                setTimeout(() => {
                    window.location.href = '/superadmin/negocios';
                }, 1000);
            })
            .catch(error => {
                Utils.showNotification('Error al guardar negocio', 'error');
            });
        });
    }

    // Acciones rápidas en lista de negocios
    const actionButtons = document.querySelectorAll('.business-action');
    actionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();

            const action = this.dataset.action;
            const businessId = this.dataset.businessId;
            const businessName = this.dataset.businessName;

            handleBusinessAction(action, businessId, businessName);
        });
    });

    // Filtros de búsqueda
    const searchInput = document.getElementById('business-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterBusinesses(this.value);
        });
    }

    // Filtros por estado
    const statusFilters = document.querySelectorAll('.status-filter');
    statusFilters.forEach(filter => {
        filter.addEventListener('change', function() {
            filterBusinessesByStatus(this.value);
        });
    });
}

// Manejar acciones de negocio
function handleBusinessAction(action, businessId, businessName) {
    switch(action) {
        case 'activate':
            if (Utils.confirm(`¿Activar suscripción de ${businessName}?`)) {
                changeBusinessStatus(businessId, 'activo');
            }
            break;

        case 'suspend':
            if (Utils.confirm(`¿Suspender suscripción de ${businessName}?`)) {
                changeBusinessStatus(businessId, 'suspendido');
            }
            break;

        case 'reset-password':
            if (Utils.confirm(`¿Restablecer contraseña del administrador de ${businessName}?`)) {
                resetAdminPassword(businessId);
            }
            break;

        case 'delete':
            if (Utils.confirm(`¿Eliminar definitivamente ${businessName}? Esta acción no se puede deshacer.`)) {
                deleteBusiness(businessId);
            }
            break;
    }
}

// Cambiar estado de negocio
function changeBusinessStatus(businessId, status) {
    Utils.ajax(`/superadmin/negocios/${businessId}/estado`, {
        method: 'POST',
        data: { estado: status }
    })
    .then(() => {
        Utils.showNotification('Estado actualizado exitosamente', 'success');
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    })
    .catch(error => {
        Utils.showNotification('Error al actualizar estado', 'error');
    });
}

// Restablecer contraseña de administrador
function resetAdminPassword(businessId) {
    Utils.ajax(`/superadmin/negocios/${businessId}/reset-password`, {
        method: 'POST'
    })
    .then(() => {
        Utils.showNotification('Contraseña restablecida. Nueva contraseña: admin123', 'success');
    })
    .catch(error => {
        Utils.showNotification('Error al restablecer contraseña', 'error');
    });
}

// Eliminar negocio
function deleteBusiness(businessId) {
    Utils.ajax(`/superadmin/negocios/${businessId}`, {
        method: 'DELETE'
    })
    .then(() => {
        Utils.showNotification('Negocio eliminado exitosamente', 'success');
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    })
    .catch(error => {
        Utils.showNotification('Error al eliminar negocio', 'error');
    });
}

// Filtrar negocios
function filterBusinesses(query) {
    const rows = document.querySelectorAll('.business-row');

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const show = text.includes(query.toLowerCase());
        row.style.display = show ? '' : 'none';
    });
}

// Filtrar por estado
function filterBusinessesByStatus(status) {
    const rows = document.querySelectorAll('.business-row');

    rows.forEach(row => {
        if (status === 'all') {
            row.style.display = '';
        } else {
            const rowStatus = row.dataset.status;
            const show = rowStatus === status;
            row.style.display = show ? '' : 'none';
        }
    });
}

// Inicializar gestión de planes
function initializePlanManagement() {
    const planForm = document.getElementById('plan-form');
    if (planForm) {
        planForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const data = Object.fromEntries(formData);

            // Validaciones
            if (!data.nombre_plan || !data.precio || !data.duracion_dias) {
                Utils.showNotification('Todos los campos son requeridos', 'error');
                return;
            }

            if (parseFloat(data.precio) <= 0) {
                Utils.showNotification('El precio debe ser mayor a 0', 'error');
                return;
            }

            if (parseInt(data.duracion_dias) <= 0) {
                Utils.showNotification('La duración debe ser mayor a 0', 'error');
                return;
            }

            const method = data.id ? 'PUT' : 'POST';
            const url = data.id ? `/superadmin/planes/${data.id}` : '/superadmin/planes';

            Utils.ajax(url, {
                method: method,
                data: data
            })
            .then(response => {
                Utils.showNotification('Plan guardado exitosamente', 'success');
                setTimeout(() => {
                    window.location.href = '/superadmin/planes';
                }, 1000);
            })
            .catch(error => {
                Utils.showNotification('Error al guardar plan', 'error');
            });
        });
    }

    // Edición inline de planes
    const editableCells = document.querySelectorAll('.editable-cell');
    editableCells.forEach(cell => {
        cell.addEventListener('dblclick', function() {
            makeCellEditable(this);
        });
    });
}

// Hacer celda editable
function makeCellEditable(cell) {
    const currentValue = cell.textContent;
    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentValue;
    input.className = 'inline-edit';

    input.addEventListener('blur', function() {
        saveCellEdit(cell, this.value);
    });

    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            this.blur();
        }
    });

    cell.textContent = '';
    cell.appendChild(input);
    input.focus();
    input.select();
}

// Guardar edición de celda
function saveCellEdit(cell, newValue) {
    const planId = cell.dataset.planId;
    const field = cell.dataset.field;

    Utils.ajax(`/superadmin/planes/${planId}`, {
        method: 'PUT',
        data: { [field]: newValue }
    })
    .then(() => {
        cell.textContent = newValue;
        Utils.showNotification('Campo actualizado', 'success');
    })
    .catch(error => {
        cell.textContent = cell.dataset.originalValue;
        Utils.showNotification('Error al actualizar campo', 'error');
    });
}

// Inicializar funcionalidades de backup
function initializeBackupFeatures() {
    const backupButtons = document.querySelectorAll('.backup-btn');

    backupButtons.forEach(button => {
        button.addEventListener('click', function() {
            const type = this.dataset.type;

            if (Utils.confirm(`¿Generar backup de ${type}?`)) {
                generateBackup(type);
            }
        });
    });

    // Programar backups automáticos
    const scheduleForm = document.getElementById('backup-schedule-form');
    if (scheduleForm) {
        scheduleForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const data = Object.fromEntries(formData);

            Utils.ajax('/superadmin/backups/schedule', {
                method: 'POST',
                data: data
            })
            .then(() => {
                Utils.showNotification('Programación de backup guardada', 'success');
            })
            .catch(error => {
                Utils.showNotification('Error al programar backup', 'error');
            });
        });
    }
}

// Generar backup
function generateBackup(type) {
    Utils.showNotification('Generando backup...', 'info');

    // Crear enlace de descarga
    const link = document.createElement('a');
    link.href = `/superadmin/backups/download/${type}`;
    link.download = `backup_${type}_${Date.now()}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    Utils.showNotification('Backup generado exitosamente', 'success');
}

// Inicializar métricas globales
function initializeGlobalMetrics() {
    // Actualizar métricas en tiempo real
    const metricsContainer = document.getElementById('global-metrics');
    if (metricsContainer) {
        loadGlobalMetrics();

        // Actualizar cada 5 minutos
        setInterval(loadGlobalMetrics, 300000);
    }

    // Gráficos de crecimiento
    const growthChart = document.getElementById('growth-chart');
    if (growthChart) {
        loadGrowthData();
    }
}

// Cargar métricas globales
function loadGlobalMetrics() {
    Utils.ajax('/superadmin/api/metrics')
        .then(data => {
            updateMetricsDisplay(data);
        })
        .catch(error => {
            console.error('Error cargando métricas:', error);
        });
}

// Actualizar display de métricas
function updateMetricsDisplay(data) {
    const metrics = [
        { id: 'total-businesses', value: data.totalNegocios },
        { id: 'active-businesses', value: data.negociosActivos },
        { id: 'total-users', value: data.totalUsuarios },
        { id: 'total-revenue', value: Utils.formatCurrency(data.totalVentas) },
        { id: 'monthly-revenue', value: Utils.formatCurrency(data.ventasMes) },
        { id: 'growth-rate', value: `${data.tasaCrecimiento || 0}%` }
    ];

    metrics.forEach(metric => {
        const element = document.getElementById(metric.id);
        if (element) {
            element.textContent = metric.value;
        }
    });
}

// Cargar datos de crecimiento
function loadGrowthData() {
    Utils.ajax('/superadmin/api/growth-data')
        .then(data => {
            renderGrowthChart(data);
        })
        .catch(error => {
            console.error('Error cargando datos de crecimiento:', error);
        });
}

// Renderizar gráfico de crecimiento
function renderGrowthChart(data) {
    const canvas = document.getElementById('growth-chart');
    if (!canvas || !data) return;

    // Implementación simplificada de gráfico de línea
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '200');

    if (data.length > 1) {
        const maxValue = Math.max(...data.map(d => d.value));
        const width = canvas.offsetWidth;
        const height = 180;

        let pathData = '';
        data.forEach((point, index) => {
            const x = (index / (data.length - 1)) * width;
            const y = height - (point.value / maxValue) * height;

            if (index === 0) {
                pathData += `M ${x} ${y}`;
            } else {
                pathData += ` L ${x} ${y}`;
            }
        });

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', pathData);
        path.setAttribute('stroke', '#3AB795');
        path.setAttribute('stroke-width', '3');
        path.setAttribute('fill', 'none');

        svg.appendChild(path);
    }

    canvas.appendChild(svg);
}

// Funcionalidad de búsqueda global
const globalSearch = document.getElementById('global-search');
if (globalSearch) {
    globalSearch.addEventListener('input', function() {
        const query = this.value.trim();
        if (query.length >= 3) {
            searchGlobal(query);
        }
    });
}

// Búsqueda global
function searchGlobal(query) {
    Utils.ajax(`/superadmin/api/search?q=${encodeURIComponent(query)}`)
        .then(results => {
            displaySearchResults(results);
        })
        .catch(error => {
            console.error('Error en búsqueda:', error);
        });
}

// Mostrar resultados de búsqueda
function displaySearchResults(results) {
    const container = document.getElementById('search-results');
    if (!container) return;

    container.innerHTML = '';

    if (results.businesses?.length > 0) {
        const section = document.createElement('div');
        section.innerHTML = '<h4>Negocios</h4>';
        results.businesses.forEach(business => {
            const item = document.createElement('div');
            item.innerHTML = `<a href="/superadmin/negocios/${business.id}">${business.nombre}</a>`;
            section.appendChild(item);
        });
        container.appendChild(section);
    }

    container.style.display = results.businesses?.length > 0 ? 'block' : 'none';
}
