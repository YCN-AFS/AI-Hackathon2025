// Giữ nguyên code JavaScript cũ nhưng thay đổi các hàm để gọi API

async function createTransaction() {
    const transaction = {
        sender: {
            fullName: document.getElementById('senderName').value,
            accountNumber: document.getElementById('senderAccount').value,
            bankName: document.getElementById('senderBank').value
        },
        receiver: {
            fullName: document.getElementById('receiverName').value,
            accountNumber: document.getElementById('receiverAccount').value,
            bankName: document.getElementById('receiverBank').value
        },
        amount: parseFloat(document.getElementById('amount').value),
        currency: document.getElementById('currency').value,
        fee: parseFloat(document.getElementById('fee').value),
        note: document.getElementById('note').value,
        paymentMethod: document.getElementById('paymentMethod').value
    };

    try {
        const response = await fetch('/api/transactions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(transaction)
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const result = await response.json();
        alert('Giao dịch đã được tạo thành công!');
        document.getElementById('transactionForm').reset();
        loadTransactions();
    } catch (error) {
        alert('Lỗi khi tạo giao dịch: ' + error.message);
    }
}

async function loadTransactions() {
    try {
        const response = await fetch('/api/transactions');
        const transactions = await response.json();
        displayTransactions(transactions);
    } catch (error) {
        console.error('Lỗi khi tải giao dịch:', error);
    }
} 