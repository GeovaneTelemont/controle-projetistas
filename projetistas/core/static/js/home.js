document.addEventListener('DOMContentLoaded', function() {
            // Sistema de Filtros e Ordenação para a tabela de produções
            // (apenas quando o usuário estiver logado)
            {% if user.is_authenticated %}
            const globalSearch = document.getElementById('globalSearch');
            const clearFilters = document.getElementById('clearFilters');
            const resultCount = document.getElementById('resultCount');
            const tableBody = document.getElementById('tableBody');
            const rows = Array.from(tableBody.querySelectorAll('tr[data-producao-id]'));
            const filterInputs = document.querySelectorAll('.filter-input, .filter-select');
            const sortIcons = document.querySelectorAll('.sort-icon');
            
            let currentSortColumn = -1;
            let currentSortDirection = 'asc';
            
            // Inicializar contador
            updateResultCount();
            
            // Função para atualizar contador
            function updateResultCount() {
                const visibleRows = rows.filter(row => row.style.display !== 'none');
                const badge = resultCount.querySelector('.filter-badge');
                badge.textContent = visibleRows.length;
            }
            
            // Função para aplicar filtros
            function applyFilters() {
                const globalSearchTerm = globalSearch.value.toLowerCase();
                const columnFilters = {};
                
                // Coletar filtros de coluna
                filterInputs.forEach(input => {
                    const columnIndex = parseInt(input.getAttribute('data-column'));
                    columnFilters[columnIndex] = input.value.toLowerCase();
                });
                
                rows.forEach(row => {
                    const collapseRow = row.nextElementSibling;
                    
                    let shouldShow = true;
                    
                    // Aplicar filtro global
                    if (globalSearchTerm) {
                        let rowMatches = false;
                        for (let i = 0; i < row.cells.length - 1; i++) {
                            const cellText = row.cells[i].textContent.toLowerCase();
                            if (cellText.includes(globalSearchTerm)) {
                                rowMatches = true;
                                break;
                            }
                        }
                        if (!rowMatches) {
                            shouldShow = false;
                        }
                    }
                    
                    // Aplicar filtros de coluna
                    for (const [columnIndex, filterValue] of Object.entries(columnFilters)) {
                        if (filterValue && shouldShow) {
                            const cell = row.cells[columnIndex];
                            let cellText = cell.textContent.toLowerCase();
                            
                            // Para células com elementos internos
                            if (cell.querySelector('.status-badge')) {
                                cellText = cell.querySelector('.status-badge').textContent.toLowerCase();
                            } else if (cell.querySelector('.badge')) {
                                cellText = cell.querySelector('.badge').textContent.toLowerCase();
                            }
                            
                            if (!cellText.includes(filterValue)) {
                                shouldShow = false;
                                break;
                            }
                        }
                    }
                    
                    // Mostrar/ocultar linha principal e sua linha de histórico
                    row.style.display = shouldShow ? '' : 'none';
                    if (collapseRow && collapseRow.classList.contains('collapse-row')) {
                        collapseRow.style.display = shouldShow ? '' : 'none';
                    }
                });
                
                updateResultCount();
            }
            
            // Função para exportar dados filtrados
            window.exportFilteredData = function() {
                const visibleRows = rows.filter(row => row.style.display !== 'none');
                
                if (visibleRows.length === 0) {
                    alert('Não há dados para exportar!');
                    return;
                }
                
                // Criar array de dados
                const data = [];
                
                // Cabeçalhos
                data.push([
                    'DC/ID', 'Projetista', 'Tipo de Projeto', 'Categoria', 
                    'Status', 'Metragem (m)', 'Data', 'Observações'
                ]);
                
                // Dados das linhas visíveis
                visibleRows.forEach(row => {
                    const cells = row.cells;
                    data.push([
                        cells[0].textContent.trim(),
                        cells[1].textContent.trim(),
                        cells[2].textContent.trim(),
                        cells[3].querySelector('.badge') ? cells[3].querySelector('.badge').textContent.trim() : cells[3].textContent.trim(),
                        cells[4].querySelector('.status-badge') ? cells[4].querySelector('.status-badge').textContent.trim() : cells[4].textContent.trim(),
                        cells[5].textContent.trim().replace('m', ''),
                        cells[6].textContent.trim(),
                        ''
                    ]);
                });
                
                // Criar planilha
                const ws = XLSX.utils.aoa_to_sheet(data);
                const wb = XLSX.utils.book_new();
                XLSX.utils.book_append_sheet(wb, ws, "Relatório");
                
                // Gerar arquivo Excel
                const fileName = `relatorio_producao_filtrado_${new Date().toISOString().split('T')[0]}.xlsx`;
                XLSX.writeFile(wb, fileName);
            };
            
            // Função para exportar todos os dados
            window.exportToExcel = function() {
                // Criar array de dados
                const data = [];
                
                // Cabeçalhos
                data.push([
                    'DC/ID', 'Projetista', 'Tipo de Projeto', 'Categoria', 
                    'Status', 'Metragem de Cabo (m)', 'Data', 'Motivo/Observação',
                    'Data de Início', 'Data de Conclusão', 'Data de Cancelamento'
                ]);
                
                // Dados completos (do contexto Django)
                {% for producao in producoes %}
                data.push([
                    '{{ producao.dc_id }}',
                    '{{ producao.projetista.username|default:"-" }}',
                    '{{ producao.tipo_projeto.nome|default:"-" }}',
                    '{{ producao.categoria.nome|default:"-" }}',
                    '{{ producao.get_status_display|default:"-" }}',
                    '{{ producao.metragem_cabo|default:"0.00" }}',
                    '{{ producao.data|date:"d/m/Y" }}',
                    '{{ producao.motivo_status|default:"-" }}',
                    '{{ producao.data_inicio|date:"d/m/Y H:i"|default:"-" }}',
                    '{{ producao.data_conclusao|date:"d/m/Y H:i"|default:"-" }}',
                    '{{ producao.data_cancelamento|date:"d/m/Y H:i"|default:"-" }}'
                ]);
                {% endfor %}
                
                // Criar planilha
                const ws = XLSX.utils.aoa_to_sheet(data);
                const wb = XLSX.utils.book_new();
                XLSX.utils.book_append_sheet(wb, ws, "Relatório Geral");
                
                // Gerar arquivo Excel
                const fileName = `relatorio_geral_${new Date().toISOString().split('T')[0]}.xlsx`;
                XLSX.writeFile(wb, fileName);
            };
            
            // Event listeners
            if (globalSearch) {
                globalSearch.addEventListener('input', applyFilters);
            }
            
            if (filterInputs.length > 0) {
                filterInputs.forEach(input => {
                    input.addEventListener('input', applyFilters);
                });
            }
            
            if (clearFilters) {
                clearFilters.addEventListener('click', function() {
                    globalSearch.value = '';
                    filterInputs.forEach(input => {
                        if (input.type === 'text' || input.type === 'date') {
                            input.value = '';
                        } else if (input.tagName === 'SELECT') {
                            input.selectedIndex = 0;
                        }
                    });
                    
                    applyFilters();
                });
            }
            
            // Configurar datas padrão para os filtros do gráfico
            const hoje = new Date();
            const umMesAtras = new Date();
            umMesAtras.setMonth(umMesAtras.getMonth() - 1);
            
            // Formatar datas para o input date (YYYY-MM-DD)
            function formatarDataParaInput(data) {
                return data.toISOString().split('T')[0];
            }
            
            // Se não houver data de início, preencher com 1 mês atrás
            const dataInicioInput = document.getElementById('dataInicio');
            if (dataInicioInput && !dataInicioInput.value) {
                dataInicioInput.value = formatarDataParaInput(umMesAtras);
            }
            
            // Se não houver data de fim, preencher com hoje
            const dataFimInput = document.getElementById('dataFim');
            if (dataFimInput && !dataFimInput.value) {
                dataFimInput.value = formatarDataParaInput(hoje);
            }
            {% endif %}
            
            // Gráfico de Produção por Projetista
            const producaoCtx = document.getElementById('producaoChart');
            if (producaoCtx) {
                // Verificar se há dados do gráfico
                {% if dados_grafico and tipos_projeto %}
                    // Preparar dados manualmente para evitar problemas com JSON
                    const tiposProjeto = [{% for tipo in tipos_projeto %}'{{ tipo }}',{% endfor %}];
                    const projetistas = [{% for dados in dados_grafico %}'{{ dados.projetista }}',{% endfor %}];
                    
                    // Cores para os projetistas
                    const cores = [
                        'rgba(54, 162, 235, 0.8)',   // Azul
                        'rgba(255, 99, 132, 0.8)',   // Vermelho
                        'rgba(75, 192, 192, 0.8)',   // Verde
                        'rgba(255, 206, 86, 0.8)',   // Amarelo
                        'rgba(153, 102, 255, 0.8)',  // Roxo
                        'rgba(255, 159, 64, 0.8)',   // Laranja
                        'rgba(201, 203, 207, 0.8)',  // Cinza
                    ];
                    
                    // Criar datasets manualmente
                    const datasets = [];
                    {% for dados in dados_grafico %}
                    datasets.push({
                        label: '{{ dados.projetista }}',
                        data: [
                            {% for tipo in tipos_projeto %}
                            {{ dados|default:0 }},
                            {% endfor %}
                        ],
                        backgroundColor: cores[{{ forloop.counter0 }} % cores.length],
                        borderColor: cores[{{ forloop.counter0 }} % cores.length].replace('0.8', '1'),
                        borderWidth: 2
                    });
                    {% endfor %}
                    
                    // Criar o gráfico
                    new Chart(producaoCtx, {
                        type: 'bar',
                        data: {
                            labels: tiposProjeto,
                            datasets: datasets
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                x: {
                                    title: {
                                        display: true,
                                        text: 'Tipos de Projeto',
                                        font: {
                                            size: 14,
                                            weight: 'bold'
                                        }
                                    },
                                    ticks: {
                                        maxRotation: 45,
                                        minRotation: 0
                                    }
                                },
                                y: {
                                    beginAtZero: true,
                                    title: {
                                        display: true,
                                        text: 'Quantidade de Projetos',
                                        font: {
                                            size: 14,
                                            weight: 'bold'
                                        }
                                    },
                                    ticks: {
                                        precision: 0,
                                        stepSize: 1
                                    }
                                }
                            },
                            plugins: {
                                legend: {
                                    position: 'top',
                                    labels: {
                                        font: {
                                            size: 12
                                        },
                                        padding: 20
                                    }
                                },
                                tooltip: {
                                    mode: 'index',
                                    intersect: false,
                                    callbacks: {
                                        label: function(context) {
                                            return `${context.dataset.label}: ${context.parsed.y} projeto(s)`;
                                        }
                                    }
                                }
                            }
                        }
                    });
                {% endif %}
            }
        });