 // Adicionar placeholders aos campos
        document.addEventListener('DOMContentLoaded', function() {
            // Adicionar placeholders
            const fields = {
                'id_first_name': 'Digite seu nome',
                'id_last_name': 'Digite seu sobrenome', 
                'id_username': 'Escolha um nome de usuário',
                'id_email': 'seu@email.com',
                'id_password1': 'Crie uma senha segura',
                'id_password2': 'Repita a senha'
            };
            
            for (const [id, placeholder] of Object.entries(fields)) {
                const field = document.getElementById(id);
                if (field) {
                    field.placeholder = placeholder;
                }
            }
            
            // Adicionar validação em tempo real
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                form.addEventListener('submit', function(event) {
                    if (!form.checkValidity()) {
                        event.preventDefault();
                        event.stopPropagation();
                    }
                    form.classList.add('was-validated');
                });
            });
        });