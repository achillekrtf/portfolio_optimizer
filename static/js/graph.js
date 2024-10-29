// Données pour le graphique des poids du portefeuille
        const labels = {{ labels|tojson }};
        const sizes = {{ sizes|tojson }};

        // Render pie chart for portfolio weights
        const ctxWeight = document.getElementById('myChart').getContext('2d');
        const weightChart = new Chart(ctxWeight, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Poids du Portefeuille',
                    data: sizes,
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.2)',
                        'rgba(153, 102, 255, 0.2)',
                        'rgba(255, 159, 64, 0.2)',
                        'rgba(255, 99, 132, 0.2)',
                        'rgba(54, 162, 235, 0.2)'
                    ],
                    borderColor: [
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)',
                        'rgba(255, 159, 64, 1)',
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.raw.toFixed(2) + '%';
                            }
                        }
                    }
                }
            }
        });

