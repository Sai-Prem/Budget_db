window.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('budgetChart').getContext('2d');
    const chartData = {
        labels: {{ budgets|map(attribute='name')|list|tojson }},
        datasets: [{
            label: 'Budget Amount',
            data: {{ budgets|map(attribute='amount')|list|tojson }},
            backgroundColor: 'rgba(54, 162, 235, 0.3)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 2
        }]
    };
    new Chart(ctx, {
        type: 'bar',
        data: chartData,
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
});
function validateBudgetForm(form) {
    const amount = parseFloat(form.amount.value);
    if (isNaN(amount) || amount <= 0) {
        alert('Amount must be a positive number.');
        return false;
    }
    return true;
}
function validateTransactionForm(form) {
    const amount = parseFloat(form.amount.value);
    if (isNaN(amount) || amount <= 0) {
        alert('Amount must be a positive number.');
        return false;
    }
    return true;
}