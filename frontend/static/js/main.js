/**
 * Script principal de HabitIQ
 * Maneja la interactividad del frontend
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('HabitIQ - Gestión de Hábitos cargado');
    
    // ===== FUNCIONALIDADES GLOBALES =====
    
    // Manejo de formularios de completación con AJAX
    initAjaxCompletionForms();
    
    // Manejo de tooltips
    initTooltips();
    
    // Animaciones de carga
    initLoadingStates();
    
    // Validación de formularios
    initFormValidation();
    
    // ===== FUNCIONES ESPECÍFICAS =====
    
    /**
     * Inicializar formularios AJAX para completar hábitos
     */
    function initAjaxCompletionForms() {
        const forms = document.querySelectorAll('.complete-form-ajax');
        
        forms.forEach(form => {
            form.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const button = this.querySelector('button');
                const habitCard = this.closest('.today-habit') || this.closest('.habit-card');
                
                // Mostrar estado de carga
                const originalHTML = button.innerHTML;
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                button.disabled = true;
                
                try {
                    const formData = new FormData(this);
                    
                    const response = await fetch(this.action, {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        // Alternar estado visual
                        toggleHabitCompletion(habitCard, button);
                        
                        // Mostrar notificación
                        showNotification('Estado actualizado correctamente', 'success');
                        
                        // Actualizar contadores si existen
                        updateCompletionCounters();
                    } else {
                        showNotification('Error al actualizar', 'error');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    showNotification('Error de conexión', 'error');
                } finally {
                    // Restaurar botón
                    button.innerHTML = originalHTML;
                    button.disabled = false;
                }
            });
        });
    }
    
    /**
     * Alternar estado visual de completación
     */
    function toggleHabitCompletion(element, button) {
        // Para tarjetas en dashboard
        if (element.classList.contains('today-habit')) {
            element.classList.toggle('completed');
            button.classList.toggle('checked');
        }
        
        // Para tarjetas en lista
        if (element.classList.contains('habit-card')) {
            const btnText = button.querySelector('span, i');
            if (btnText) {
                const isCompleted = button.classList.contains('btn-completed');
                
                if (isCompleted) {
                    button.classList.remove('btn-completed');
                    button.classList.add('btn-outline');
                    if (btnText.innerHTML.includes('Completado')) {
                        btnText.innerHTML = '<i class="far fa-circle"></i> Marcar como hecho';
                    }
                } else {
                    button.classList.remove('btn-outline');
                    button.classList.add('btn-completed');
                    if (btnText.innerHTML.includes('Marcar')) {
                        btnText.innerHTML = '<i class="fas fa-check-circle"></i> Completado';
                    }
                }
            }
        }
    }
    
    /**
     * Actualizar contadores de completación
     */
    function updateCompletionCounters() {
        const completedCount = document.querySelectorAll('.today-habit.completed').length;
        const totalCount = document.querySelectorAll('.today-habit').length;
        
        // Actualizar en dashboard si existe
        const counterElement = document.querySelector('.stat-card.completed h3');
        if (counterElement) {
            counterElement.textContent = completedCount;
        }
        
        // Actualizar porcentaje si existe
        const percentageElement = document.querySelector('.completion-percentage');
        if (percentageElement && totalCount > 0) {
            const percentage = Math.round((completedCount / totalCount) * 100);
            percentageElement.textContent = `${percentage}% completado`;
        }
    }
    
    /**
     * Mostrar notificación toast
     */
    function showNotification(message, type = 'info') {
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button class="notification-close">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Añadir al body
        document.body.appendChild(notification);
        
        // Mostrar con animación
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Configurar cierre
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        });
        
        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 5000);
    }
    
    /**
     * Inicializar tooltips
     */
    function initTooltips() {
        const tooltipElements = document.querySelectorAll('[title]');
        
        tooltipElements.forEach(element => {
            element.addEventListener('mouseenter', function(e) {
                const title = this.getAttribute('title');
                if (!title) return;
                
                // Crear tooltip
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                tooltip.textContent = title;
                
                // Posicionar
                const rect = this.getBoundingClientRect();
                tooltip.style.left = `${rect.left + rect.width / 2}px`;
                tooltip.style.top = `${rect.top - 10}px`;
                
                // Añadir y mostrar
                document.body.appendChild(tooltip);
                setTimeout(() => tooltip.classList.add('show'), 10);
                
                // Guardar referencia
                this.tooltip = tooltip;
                
                // Remover atributo temporalmente
                this.removeAttribute('title');
            });
            
            element.addEventListener('mouseleave', function() {
                if (this.tooltip) {
                    this.tooltip.classList.remove('show');
                    setTimeout(() => {
                        if (this.tooltip && this.tooltip.parentNode) {
                            this.tooltip.remove();
                        }
                    }, 300);
                }
                
                // Restaurar título
                const title = this.getAttribute('data-original-title') || this.dataset.originalTitle;
                if (title) {
                    this.setAttribute('title', title);
                }
            });
        });
    }
    
    /**
     * Inicializar estados de carga
     */
    function initLoadingStates() {
        // Agregar clase de carga a botones de formulario
        const submitButtons = document.querySelectorAll('form button[type="submit"]');
        
        submitButtons.forEach(button => {
            button.addEventListener('click', function() {
                const form = this.closest('form');
                if (form && form.checkValidity()) {
                    this.classList.add('loading');
                    this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
                }
            });
        });
    }
    
    /**
     * Validación de formularios
     */
    function initFormValidation() {
        const forms = document.querySelectorAll('.habit-form');
        
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                let isValid = true;
                
                // Validar campos requeridos
                const requiredFields = this.querySelectorAll('[required]');
                requiredFields.forEach(field => {
                    if (!field.value.trim()) {
                        isValid = false;
                        highlightError(field, 'Este campo es requerido');
                    } else {
                        clearError(field);
                    }
                });
                
                // Validar longitud máxima
                const maxLengthFields = this.querySelectorAll('[maxlength]');
                maxLengthFields.forEach(field => {
                    const maxLength = parseInt(field.getAttribute('maxlength'));
                    if (field.value.length > maxLength) {
                        isValid = false;
                        highlightError(field, `Máximo ${maxLength} caracteres`);
                    }
                });
                
                if (!isValid) {
                    e.preventDefault();
                    showNotification('Por favor, corrige los errores en el formulario', 'error');
                }
            });
            
            // Validación en tiempo real
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('blur', function() {
                    validateField(this);
                });
                
                input.addEventListener('input', function() {
                    clearError(this);
                });
            });
        });
        
        /**
         * Validar campo individual
         */
        function validateField(field) {
            if (field.hasAttribute('required') && !field.value.trim()) {
                highlightError(field, 'Este campo es requerido');
                return false;
            }
            
            if (field.hasAttribute('maxlength')) {
                const maxLength = parseInt(field.getAttribute('maxlength'));
                if (field.value.length > maxLength) {
                    highlightError(field, `Máximo ${maxLength} caracteres`);
                    return false;
                }
            }
            
            clearError(field);
            return true;
        }
        
        /**
         * Resaltar error en campo
         */
        function highlightError(field, message) {
            // Limpiar errores previos
            clearError(field);
            
            // Agregar clase de error
            field.classList.add('error');
            
            // Crear mensaje de error
            const errorDiv = document.createElement('div');
            errorDiv.className = 'field-error';
            errorDiv.textContent = message;
            
            // Insertar después del campo
            field.parentNode.appendChild(errorDiv);
        }
        
        /**
         * Limpiar error de campo
         */
        function clearError(field) {
            field.classList.remove('error');
            
            const errorDiv = field.parentNode.querySelector('.field-error');
            if (errorDiv) {
                errorDiv.remove();
            }
        }
    }
    
    // ===== FUNCIONALIDADES ADICIONALES =====
    
    /**
     * Confirmación para acciones destructivas
     */
    const deleteForms = document.querySelectorAll('.delete-form');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('¿Estás seguro de que quieres eliminar este hábito?')) {
                e.preventDefault();
            }
        });
    });
    
    /**
     * Filtrado de hábitos por categoría
     */
    const categoryFilters = document.querySelectorAll('.category-filter');
    if (categoryFilters.length > 0) {
        categoryFilters.forEach(filter => {
            filter.addEventListener('click', function(e) {
                e.preventDefault();
                
                const category = this.dataset.category;
                const habitCards = document.querySelectorAll('.habit-card');
                
                habitCards.forEach(card => {
                    if (category === 'all' || card.dataset.category === category) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
                
                // Actualizar filtro activo
                categoryFilters.forEach(f => f.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }
    
    /**
     * Búsqueda de hábitos
     */
    const searchInput = document.querySelector('#habit-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const habitCards = document.querySelectorAll('.habit-card');
            
            habitCards.forEach(card => {
                const habitName = card.querySelector('h3').textContent.toLowerCase();
                const habitDesc = card.querySelector('.habit-description')?.textContent.toLowerCase() || '';
                
                if (habitName.includes(searchTerm) || habitDesc.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
    
    // ===== ESTILOS DINÁMICOS PARA NOTIFICACIONES =====
    
    const style = document.createElement('style');
    style.textContent = `
        .notification {
            position: fixed;
            top: 100px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            background: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 15px;
            transform: translateX(150%);
            transition: transform 0.3s ease;
            z-index: 9999;
            max-width: 350px;
        }
        
        .notification.show {
            transform: translateX(0);
        }
        
        .notification-success {
            border-left: 4px solid #4cc9f0;
        }
        
        .notification-error {
            border-left: 4px solid #f94144;
        }
        
        .notification-close {
            background: none;
            border: none;
            color: #666;
            cursor: pointer;
            padding: 4px;
            font-size: 12px;
        }
        
        .tooltip {
            position: fixed;
            background: #333;
            color: white;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 12px;
            white-space: nowrap;
            pointer-events: none;
            z-index: 10000;
            opacity: 0;
            transform: translate(-50%, -100%);
            transition: opacity 0.2s;
        }
        
        .tooltip.show {
            opacity: 1;
        }
        
        .tooltip:after {
            content: '';
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border: 5px solid transparent;
            border-top-color: #333;
        }
        
        .field-error {
            color: #f94144;
            font-size: 12px;
            margin-top: 4px;
        }
        
        .error {
            border-color: #f94144 !important;
        }
        
        .loading {
            opacity: 0.7;
            cursor: not-allowed;
        }
    `;
    
    document.head.appendChild(style);
    
    // ===== INICIALIZACIÓN DE COMPONENTES ESPECÍFICOS =====
    
    // Actualizar fecha y hora en tiempo real (si hay elemento para ello)
    const dateTimeElement = document.querySelector('.current-datetime');
    if (dateTimeElement) {
        function updateDateTime() {
            const now = new Date();
            const options = { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            };
            dateTimeElement.textContent = now.toLocaleDateString('es-ES', options);
        }
        
        updateDateTime();
        setInterval(updateDateTime, 60000); // Actualizar cada minuto
    }
    
    // ===== EVENT LISTENERS GLOBALES =====
    
    // Cerrar flash messages al hacer clic
    document.addEventListener('click', function(e) {
        if (e.target.closest('.flash-close')) {
            const flashMessage = e.target.closest('.flash-message');
            if (flashMessage) {
                flashMessage.style.opacity = '0';
                setTimeout(() => {
                    flashMessage.remove();
                }, 300);
            }
        }
    });
    
    // Mejorar accesibilidad de formularios
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        // Enfocar primer campo con error al enviar
        form.addEventListener('invalid', function(e) {
            e.preventDefault();
            const invalidField = form.querySelector(':invalid');
            if (invalidField) {
                invalidField.focus();
            }
        }, true);
    });
});

/**
 * Función para exportar datos (futura implementación)
 */
function exportHabitsData(format = 'json') {
    console.log(`Exportando datos en formato ${format}...`);
    // Implementación futura
    showNotification('Exportación de datos - Próximamente', 'info');
}

/**
 * Función para importar datos (futura implementación)
 */
function importHabitsData() {
    console.log('Importando datos...');
    // Implementación futura
    showNotification('Importación de datos - Próximamente', 'info');
}