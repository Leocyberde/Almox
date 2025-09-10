/**
 * Autocomplete functionality for product search
 * Sistema de Controle de Estoque
 */

class ProductAutocomplete {
    constructor(inputElement, resultsContainer, options = {}) {
        this.input = inputElement;
        this.results = resultsContainer;
        this.options = {
            minLength: 2,
            delay: 300,
            maxResults: 10,
            apiEndpoint: '/api/products/search',
            ...options
        };
        
        this.searchTimeout = null;
        this.selectedIndex = -1;
        this.currentResults = [];
        
        this.init();
    }
    
    init() {
        this.input.addEventListener('input', this.handleInput.bind(this));
        this.input.addEventListener('keydown', this.handleKeydown.bind(this));
        this.input.addEventListener('focus', this.handleFocus.bind(this));
        
        // Hide results when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.results.contains(e.target)) {
                this.hideResults();
            }
        });
    }
    
    handleInput(e) {
        const query = e.target.value.trim();
        
        clearTimeout(this.searchTimeout);
        
        if (query.length < this.options.minLength) {
            this.hideResults();
            this.clearSelection();
            return;
        }
        
        this.searchTimeout = setTimeout(() => {
            this.search(query);
        }, this.options.delay);
    }
    
    handleKeydown(e) {
        if (!this.isVisible()) return;
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectNext();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.selectPrevious();
                break;
            case 'Enter':
                e.preventDefault();
                if (this.selectedIndex >= 0) {
                    this.selectItem(this.currentResults[this.selectedIndex]);
                }
                break;
            case 'Escape':
                this.hideResults();
                this.input.blur();
                break;
        }
    }
    
    handleFocus(e) {
        const query = e.target.value.trim();
        if (query.length >= this.options.minLength && this.currentResults.length > 0) {
            this.showResults();
        }
    }
    
    async search(query) {
        try {
            const response = await fetch(`${this.options.apiEndpoint}?q=${encodeURIComponent(query)}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const products = await response.json();
            this.currentResults = products.slice(0, this.options.maxResults);
            this.displayResults(this.currentResults);
        } catch (error) {
            console.error('Search error:', error);
            this.displayError('Erro ao buscar produtos. Tente novamente.');
        }
    }
    
    displayResults(products) {
        if (products.length === 0) {
            this.displayEmpty();
            return;
        }
        
        const resultsHtml = products.map((product, index) => this.createResultItem(product, index)).join('');
        this.results.innerHTML = resultsHtml;
        this.selectedIndex = -1;
        this.showResults();
        
        // Add click handlers
        this.results.querySelectorAll('.autocomplete-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                this.selectItem(products[index]);
            });
        });
    }
    
    createResultItem(product, index) {
        const stockClass = product.quantity > 0 ? 'success' : 'danger';
        const stockText = product.quantity > 0 ? `${product.quantity} ${product.unit}` : 'Sem estoque';
        
        return `
            <div class="autocomplete-item p-3 border-bottom" data-index="${index}" style="cursor: pointer;">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="fw-bold text-primary">${this.escapeHtml(product.code)}</div>
                        <div class="text-truncate">${this.escapeHtml(product.name)}</div>
                        <small class="text-muted">
                            ${product.supplier_reference ? this.escapeHtml(product.supplier_reference) + ' - ' : ''}
                            ${this.escapeHtml(product.supplier_name)}
                            <br>
                            <i class="fas fa-map-marker-alt"></i> ${this.escapeHtml(product.location)}
                        </small>
                    </div>
                    <div class="text-end ms-2">
                        <span class="badge bg-${stockClass}">${stockText}</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    displayEmpty() {
        this.results.innerHTML = `
            <div class="p-3 text-muted text-center">
                <i class="fas fa-search"></i> Nenhum produto encontrado
            </div>
        `;
        this.showResults();
    }
    
    displayError(message) {
        this.results.innerHTML = `
            <div class="p-3 text-danger text-center">
                <i class="fas fa-exclamation-triangle"></i> ${this.escapeHtml(message)}
            </div>
        `;
        this.showResults();
    }
    
    selectNext() {
        if (this.selectedIndex < this.currentResults.length - 1) {
            this.selectedIndex++;
            this.updateSelection();
        }
    }
    
    selectPrevious() {
        if (this.selectedIndex > 0) {
            this.selectedIndex--;
            this.updateSelection();
        }
    }
    
    updateSelection() {
        // Remove previous selection
        this.results.querySelectorAll('.autocomplete-item').forEach(item => {
            item.classList.remove('bg-primary', 'text-white');
        });
        
        // Add current selection
        if (this.selectedIndex >= 0) {
            const selectedItem = this.results.querySelector(`[data-index="${this.selectedIndex}"]`);
            if (selectedItem) {
                selectedItem.classList.add('bg-primary', 'text-white');
                selectedItem.scrollIntoView({ block: 'nearest' });
            }
        }
    }
    
    selectItem(product) {
        this.hideResults();
        
        // Trigger custom event with selected product
        const event = new CustomEvent('productSelected', {
            detail: { product }
        });
        this.input.dispatchEvent(event);
    }
    
    clearSelection() {
        this.selectedIndex = -1;
        this.currentResults = [];
        
        // Trigger custom event for clearing selection
        const event = new CustomEvent('productCleared');
        this.input.dispatchEvent(event);
    }
    
    showResults() {
        this.results.style.display = 'block';
        this.results.classList.add('fade-in');
    }
    
    hideResults() {
        this.results.style.display = 'none';
        this.results.classList.remove('fade-in');
    }
    
    isVisible() {
        return this.results.style.display === 'block';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Public methods
    clear() {
        this.input.value = '';
        this.hideResults();
        this.clearSelection();
    }
    
    setValue(value) {
        this.input.value = value;
    }
    
    focus() {
        this.input.focus();
    }
    
    destroy() {
        clearTimeout(this.searchTimeout);
        this.hideResults();
    }
}

// Global utility functions for common autocomplete scenarios
window.ProductAutocomplete = ProductAutocomplete;

// Initialize autocomplete for product search inputs when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const productSearchInputs = document.querySelectorAll('[data-autocomplete="products"]');
    
    productSearchInputs.forEach(input => {
        const resultsContainer = input.nextElementSibling;
        if (resultsContainer && resultsContainer.classList.contains('autocomplete-results')) {
            new ProductAutocomplete(input, resultsContainer);
        }
    });
});

// Utility function to format currency
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Utility function to format numbers
function formatNumber(value, decimals = 2) {
    return new Intl.NumberFormat('pt-BR', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value);
}

// Utility function to debounce function calls
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Utility function to show loading state
function showLoading(element, text = 'Carregando...') {
    const originalContent = element.innerHTML;
    element.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status"></span>
        ${text}
    `;
    element.disabled = true;
    
    return () => {
        element.innerHTML = originalContent;
        element.disabled = false;
    };
}

// Utility function to show toast notifications
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
    }
    
    const toastId = `toast-${Date.now()}`;
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    document.getElementById('toast-container').insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Form validation utilities
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        }
    });
    
    return isValid;
}

// Add real-time validation to forms
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form[data-validate="true"]');
    
    forms.forEach(form => {
        const submitBtn = form.querySelector('button[type="submit"]');
        const requiredFields = form.querySelectorAll('[required]');
        
        function updateSubmitButton() {
            const isValid = validateForm(form);
            if (submitBtn) {
                submitBtn.disabled = !isValid;
            }
        }
        
        requiredFields.forEach(field => {
            field.addEventListener('input', updateSubmitButton);
            field.addEventListener('blur', updateSubmitButton);
        });
        
        // Initial validation
        updateSubmitButton();
    });
});

// Confirmation dialogs
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Enhanced confirmation for delete actions
function confirmDelete(itemName, callback) {
    const message = `Tem certeza que deseja excluir "${itemName}"?\n\nEsta ação não pode ser desfeita.`;
    confirmAction(message, callback);
}
