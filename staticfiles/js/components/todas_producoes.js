document.addEventListener('DOMContentLoaded', function() {
    // Filtros rápidos por status
    const quickFilterButtons = document.querySelectorAll('[data-filter]');
    quickFilterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remover classe active de todos os botões
            quickFilterButtons.forEach(btn => btn.classList.remove('active'));
            
            // Adicionar classe active ao botão clicado
            this.classList.add('active');
            
            const filter = this.dataset.filter;
            applyAllFilters();
        });
    });
    
    // Elementos de filtro
    const filterId = document.querySelector('#filterId');
    const filterProjetista = document.querySelector('#filterProjetista');
    const filterTipo = document.querySelector('#filterTipo');
    const filterStatus = document.querySelector('#filterStatus');
    const filterObservacoes = document.querySelector('#filterObservacoes');
    const filterStartDate = document.querySelector('#filterStartDate');
    const filterEndDate = document.querySelector('#filterEndDate');
    const resetFiltersBtn = document.querySelector('#resetFilters');
    
    // Adicionar eventos aos filtros
    if (filterId) filterId.addEventListener('input', applyAllFilters);
    if (filterProjetista) filterProjetista.addEventListener('input', applyAllFilters);
    if (filterTipo) filterTipo.addEventListener('change', applyAllFilters);
    if (filterStatus) filterStatus.addEventListener('change', applyAllFilters);
    if (filterObservacoes) filterObservacoes.addEventListener('input', applyAllFilters);
    if (filterStartDate) filterStartDate.addEventListener('change', applyAllFilters);
    if (filterEndDate) filterEndDate.addEventListener('change', applyAllFilters);
    
    // Botão para limpar todos os filtros
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', function() {
            // Limpar valores dos filtros
            if (filterId) filterId.value = '';
            if (filterProjetista) filterProjetista.value = '';
            if (filterTipo) filterTipo.value = '';
            if (filterStatus) filterStatus.value = '';
            if (filterObservacoes) filterObservacoes.value = '';
            if (filterStartDate) filterStartDate.value = '';
            if (filterEndDate) filterEndDate.value = '';
            
            // Resetar filtros rápidos para "Todas"
            quickFilterButtons.forEach(btn => {
                btn.classList.remove('active');
                if (btn.dataset.filter === 'all') {
                    btn.classList.add('active');
                }
            });
            
            // Aplicar filtros (que mostrará todas as linhas)
            applyAllFilters();
        });
    }
    
    // Função principal para aplicar todos os filtros
    function applyAllFilters() {
        const rows = document.querySelectorAll('.production-row');
        
        // Obter valores dos filtros
        const idFilter = filterId ? filterId.value.trim().toLowerCase() : '';
        const projetistaFilter = filterProjetista ? filterProjetista.value.trim().toLowerCase() : '';
        const tipoFilter = filterTipo ? filterTipo.value.trim().toLowerCase() : '';
        const statusFilter = filterStatus ? filterStatus.value.trim().toLowerCase() : '';
        const observacoesFilter = filterObservacoes ? filterObservacoes.value.trim().toLowerCase() : '';
        const startDateFilter = filterStartDate ? filterStartDate.value : '';
        const endDateFilter = filterEndDate ? filterEndDate.value : '';
        
        // Obter filtro rápido ativo
        const activeQuickFilter = document.querySelector('.quick-filters .btn.active');
        const quickFilter = activeQuickFilter ? activeQuickFilter.dataset.filter : 'all';
        
        // Contador de linhas visíveis
        let visibleCount = 0;
        
        rows.forEach(row => {
            let showRow = true;
            
            // Filtro por ID
            if (idFilter) {
                const dcId = row.dataset.dcId || '';
                if (!dcId.includes(idFilter)) {
                    showRow = false;
                }
            }
            
            // Filtro por Projetista
            if (showRow && projetistaFilter) {
                const projetista = row.dataset.projetista || '';
                if (!projetista.includes(projetistaFilter)) {
                    showRow = false;
                }
            }
            
            // Filtro por Tipo
            if (showRow && tipoFilter) {
                const tipo = row.dataset.tipo || '';
                if (tipo !== tipoFilter) {
                    showRow = false;
                }
            }
            
            // Filtro por Status (select)
            if (showRow && statusFilter) {
                const statusDisplay = row.dataset.statusDisplay || '';
                if (statusDisplay.toLowerCase() !== statusFilter) {
                    showRow = false;
                }
            }
            
            // Filtro rápido por status
            if (showRow && quickFilter !== 'all') {
                const rowStatus = row.dataset.status || '';
                if (rowStatus !== quickFilter) {
                    showRow = false;
                }
            }
            
            // Filtro por Data
            if (showRow && (startDateFilter || endDateFilter)) {
                const dataInicio = row.dataset.dataInicio || '';
                
                if (startDateFilter && dataInicio < startDateFilter) {
                    showRow = false;
                }
                
                if (endDateFilter && dataInicio > endDateFilter) {
                    showRow = false;
                }
            }
            
            // Filtro por Observações
            if (showRow && observacoesFilter) {
                const observacoes = row.dataset.observacoes || '';
                if (!observacoes.includes(observacoesFilter)) {
                    showRow = false;
                }
            }
            
            // Aplicar visibilidade
            row.style.display = showRow ? '' : 'none';
            
            // Esconder/mostrar linha de histórico correspondente
            const historicoRow = row.nextElementSibling;
            if (historicoRow && historicoRow.classList.contains('historico-row')) {
                historicoRow.style.display = showRow ? '' : 'none';
            }
            
            if (showRow) visibleCount++;
        });
        
        // Atualizar contador no badge "Todas"
        const todasBadge = document.querySelector('#count-all');
        if (todasBadge) {
            todasBadge.textContent = visibleCount;
        }
        
        // Mostrar mensagem se não houver resultados
        const emptyState = document.querySelector('.empty-state');
        const tbody = document.getElementById('tableBody');
        const existingNoResults = tbody.querySelector('.no-results-row');
        
        if (visibleCount === 0 && !emptyState) {
            if (!existingNoResults) {
                const noResultsRow = document.createElement('tr');
                noResultsRow.className = 'no-results-row';
                noResultsRow.innerHTML = `
                    <td colspan="7" class="text-center py-5">
                        <div class="empty-state">
                            <i class="fas fa-search fa-3x text-muted mb-3"></i>
                            <h4 class="mt-3">Nenhum resultado encontrado</h4>
                            <p class="text-muted mb-0">Tente ajustar seus filtros.</p>
                        </div>
                    </td>
                `;
                tbody.appendChild(noResultsRow);
            }
        } else if (existingNoResults) {
            existingNoResults.remove();
        }
    }
    
    // Ordenação da tabela
    const sortIcons = document.querySelectorAll('.sort-icon');
    let currentSortColumn = null;
    let currentSortDirection = 'asc';
    
    sortIcons.forEach(icon => {
        icon.addEventListener('click', function() {
            const column = parseInt(this.dataset.column);
            sortTable(column);
        });
    });
    
    function sortTable(column) {
        const tbody = document.getElementById('tableBody');
        const rows = Array.from(tbody.querySelectorAll('.production-row'));
        
        // Determinar direção da ordenação
        if (currentSortColumn === column) {
            currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            currentSortColumn = column;
            currentSortDirection = 'asc';
        }
        
        // Ordenar as linhas
        rows.sort((a, b) => {
            let aValue, bValue;
            
            // Obter valores baseados na coluna
            switch(column) {
                case 0: // ID
                    aValue = a.dataset.dcId || '';
                    bValue = b.dataset.dcId || '';
                    break;
                case 1: // Projetista
                    aValue = a.dataset.projetista || '';
                    bValue = b.dataset.projetista || '';
                    break;
                case 2: // Tipo
                    aValue = a.dataset.tipo || '';
                    bValue = b.dataset.tipo || '';
                    break;
                case 3: // Status
                    aValue = a.dataset.statusDisplay || '';
                    bValue = b.dataset.statusDisplay || '';
                    break;
                case 5: // Observações
                    aValue = a.dataset.observacoes || '';
                    bValue = b.dataset.observacoes || '';
                    break;
                default:
                    return 0;
            }
            
            // Comparar valores
            let comparison = 0;
            if (aValue < bValue) comparison = -1;
            if (aValue > bValue) comparison = 1;
            
            // Aplicar direção
            return currentSortDirection === 'asc' ? comparison : -comparison;
        });
        
        // Reordenar as linhas no DOM incluindo as linhas de histórico
        rows.forEach(row => {
            const historicoRow = row.nextElementSibling;
            tbody.appendChild(row);
            if (historicoRow && historicoRow.classList.contains('historico-row')) {
                tbody.appendChild(historicoRow);
            }
        });
        
        // Atualizar ícones de ordenação
        sortIcons.forEach(icon => {
            icon.className = 'fas fa-sort sort-icon ms-auto';
            if (parseInt(icon.dataset.column) === column) {
                icon.className = currentSortDirection === 'asc' 
                    ? 'fas fa-sort-up sort-icon ms-auto' 
                    : 'fas fa-sort-down sort-icon ms-auto';
            }
        });
    }
    
    // Inicializar tooltips do Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Aplicar filtros na carga inicial
    applyAllFilters();
});