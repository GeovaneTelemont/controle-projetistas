document.addEventListener('DOMContentLoaded', function() {
    // Focar no campo de data quando carregar
    const filterDate = document.getElementById('filterDate');
    if (filterDate && !filterDate.value) {
        // Definir data atual como padrão
        const today = new Date().toISOString().split('T')[0];
        filterDate.value = today;
    }
    
    // Adicionar máscara de data (opcional)
    if (filterDate) {
        filterDate.addEventListener('change', function() {
            if (this.value) {
                // Formatar a data para exibição
                const date = new Date(this.value);
                const formattedDate = date.toLocaleDateString('pt-BR');
                console.log('Filtrando por data:', formattedDate);
            }
        });
    }
    
    // Submissão automática do formulário (opcional)
    const dateFilterForm = document.getElementById('dateFilterForm');
    if (dateFilterForm && filterDate) {
        filterDate.addEventListener('change', function() {
            if (this.value) {
                dateFilterForm.submit();
            }
        });
    }
});