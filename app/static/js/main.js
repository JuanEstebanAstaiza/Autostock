/**
 * Autostock - JavaScript Principal
 * Utilidades comunes y funcionalidades base
 */

// Utilidades generales
const Utils = {
    // Mostrar mensajes de notificación
    showNotification: function(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        // Estilos para la notificación
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '1rem',
            borderRadius: '4px',
            color: 'white',
            fontWeight: '500',
            zIndex: '1000',
            maxWidth: '300px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            opacity: '0',
            transition: 'opacity 0.3s ease'
        });

        // Colores según tipo
        const colors = {
            success: '#3AB795',
            error: '#dc3545',
            warning: '#F6AE2D',
            info: '#1A2238'
        };
        notification.style.backgroundColor = colors[type] || colors.info;

        document.body.appendChild(notification);

        // Animación de entrada
        setTimeout(() => {
            notification.style.opacity = '1';
        }, 10);

        // Auto-remover
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, duration);
    },

    // Confirmar acciones
    confirm: function(message) {
        return window.confirm(message);
    },

    // Formatear moneda
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },

    // Formatear fecha
    formatDate: function(date) {
        return new Intl.DateTimeFormat('es-ES', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    },

    // Validar formulario básico
    validateForm: function(form) {
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!input.value.trim()) {
                input.style.borderColor = '#dc3545';
                isValid = false;
            } else {
                input.style.borderColor = '#E0E3E7';
            }
        });

        return isValid;
    },

    // AJAX helper
    ajax: function(url, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const config = { ...defaultOptions, ...options };

        if (config.data) {
            config.body = JSON.stringify(config.data);
        }

        return fetch(url, config)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .catch(error => {
                console.error('AJAX Error:', error);
                Utils.showNotification('Error de conexión', 'error');
                throw error;
            });
    },

    // Cargar datos dinámicamente
    loadData: function(url, targetElement, callback) {
        Utils.ajax(url)
            .then(data => {
                if (callback) {
                    callback(data, targetElement);
                }
            })
            .catch(error => {
                targetElement.innerHTML = '<p>Error al cargar datos</p>';
            });
    }
};

// Función para cerrar modales
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Función para abrir modales
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

// Función para cerrar modal desde elemento (usada por modal-close)
function closeCurrentModal(element) {
    const modal = element.closest('.modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    // Funcionalidad de modales - agregar event listeners a botones de cerrar
    const modalCloseButtons = document.querySelectorAll('.modal-close');
    modalCloseButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            closeCurrentModal(this);
        });

        // También agregar onclick directo por compatibilidad
        button.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            closeCurrentModal(this);
        };
    });

    // Cerrar modal al hacer click fuera del contenido
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
    });

    // Validación de formularios
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!Utils.validateForm(form)) {
                e.preventDefault();
                Utils.showNotification('Por favor complete todos los campos requeridos', 'warning');
            }
        });
    });

    // Navegación móvil
    const nav = document.querySelector('.dashboard-nav');
    if (nav) {
        // Scroll suave en navegación horizontal
        nav.addEventListener('wheel', function(e) {
            if (e.deltaY > 0) {
                nav.scrollLeft += 50;
            } else {
                nav.scrollLeft -= 50;
            }
            e.preventDefault();
        });
    }

    // Botones de eliminación con confirmación
    const deleteButtons = document.querySelectorAll('[data-action="delete"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.dataset.confirmMessage || '¿Está seguro de que desea eliminar este elemento?';
            if (!Utils.confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Auto-ocultar mensajes de éxito/error después de tiempo
    const alerts = document.querySelectorAll('.alert, .error-message, .success-message');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 300);
        }, 5000);
    });
});

// Funcionalidad de búsqueda en tiempo real
function setupSearch(searchInput, targetContainer, searchUrl) {
    let searchTimeout;

    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();

        searchTimeout = setTimeout(() => {
            if (query.length >= 2) {
                Utils.loadData(`${searchUrl}?q=${encodeURIComponent(query)}`, targetContainer, function(data) {
                    // Callback para manejar resultados de búsqueda
                    if (window.handleSearchResults) {
                        window.handleSearchResults(data, targetContainer);
                    }
                });
            }
        }, 300);
    });
}

// Exportar utilidades globalmente
window.Utils = Utils;
window.setupSearch = setupSearch;
