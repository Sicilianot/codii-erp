// Funciones de utilidad
const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN'
    }).format(amount);
};

const formatDate = (date) => {
    return new Intl.DateTimeFormat('es-MX', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    }).format(new Date(date));
};

const formatDateTime = (date) => {
    return new Intl.DateTimeFormat('es-MX', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(date));
};

// Inicialización de DataTables
const initDataTables = () => {
    $('.datatable').DataTable({
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/es-MX.json'
        },
        responsive: true,
        dom: 'Bfrtip',
        buttons: [
            'copy', 'csv', 'excel', 'pdf', 'print'
        ]
    });
};

// Inicialización de Select2
const initSelect2 = () => {
    $('.select2').select2({
        theme: 'bootstrap-5',
        language: 'es'
    });
};

// Inicialización de Tooltips
const initTooltips = () => {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
};

// Inicialización de Popovers
const initPopovers = () => {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
};

// Manejo de formularios
const handleFormSubmit = (formId, successCallback) => {
    $(`#${formId}`).on('submit', function(e) {
        e.preventDefault();
        
        const form = $(this);
        const submitButton = form.find('button[type="submit"]');
        const originalText = submitButton.html();
        
        submitButton.prop('disabled', true)
            .html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...');
        
        $.ajax({
            url: form.attr('action'),
            method: form.attr('method'),
            data: form.serialize(),
            success: function(response) {
                if (successCallback) {
                    successCallback(response);
                }
            },
            error: function(xhr) {
                const errorMessage = xhr.responseJSON?.message || 'Ha ocurrido un error';
                showAlert('error', errorMessage);
            },
            complete: function() {
                submitButton.prop('disabled', false).html(originalText);
            }
        });
    });
};

// Mostrar alertas
const showAlert = (type, message) => {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    $('#alertContainer').html(alertHtml);
    
    setTimeout(() => {
        $('.alert').alert('close');
    }, 5000);
};

// Confirmación de acciones
const confirmAction = (message, callback) => {
    if (confirm(message)) {
        callback();
    }
};

// Cálculo de totales
const calculateTotal = (items) => {
    return items.reduce((total, item) => {
        return total + (item.quantity * item.price);
    }, 0);
};

// Validación de formularios
const validateForm = (formId) => {
    const form = document.getElementById(formId);
    if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
    }
    form.classList.add('was-validated');
};

// Inicialización al cargar el documento
$(document).ready(function() {
    initDataTables();
    initSelect2();
    initTooltips();
    initPopovers();
    
    // Manejo de mensajes flash
    const flashMessage = $('#flashMessage');
    if (flashMessage.length) {
        setTimeout(() => {
            flashMessage.alert('close');
        }, 5000);
    }
    
    // Manejo de modales
    $('.modal').on('shown.bs.modal', function() {
        $(this).find('[autofocus]').focus();
    });
    
    // Manejo de tabs
    $('a[data-bs-toggle="tab"]').on('shown.bs.tab', function(e) {
        const target = $(e.target).attr('href');
        $(target).find('.select2').select2('destroy').select2({
            theme: 'bootstrap-5',
            language: 'es'
        });
    });
}); 