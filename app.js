// Khai báo biến global
let web3;
let contract;

// Mảng lưu trữ các giao dịch
let transactions = [];

// Hàm khởi tạo Web3 và Contract
async function initWeb3() {
    // Kiểm tra MetaMask
    if (window.ethereum) {
        try {
            // Yêu cầu quyền truy cập tài khoản
            await window.ethereum.request({ method: 'eth_requestAccounts' });
            web3 = new Web3(window.ethereum);
            await initContract();
            console.log('MetaMask đã được kết nối');
        } catch (error) {
            console.error('Người dùng từ chối kết nối:', error);
            alert('Vui lòng cho phép kết nối với MetaMask để sử dụng ứng dụng');
        }
    } else {
        console.error('Không tìm thấy MetaMask!');
        alert('Vui lòng cài đặt MetaMask để sử dụng ứng dụng');
    }
}

// Hàm khởi tạo Contract
async function initContract() {
    try {
        // Thay thế bằng ABI thật của bạn
        const contractABI = [
            // Paste ABI của smart contract vào đây
        ];
        // Thay thế bằng địa chỉ contract thật của bạn
        const contractAddress = 'YOUR_CONTRACT_ADDRESS';
        
        contract = new web3.eth.Contract(contractABI, contractAddress);
        console.log('Contract đã được khởi tạo');
    } catch (error) {
        console.error('Lỗi khởi tạo contract:', error);
    }
}

// Hàm tải tất cả giao dịch
async function loadAllTransactions() {
    try {
        if (!contract) {
            alert('Đang kết nối với blockchain...');
            await initWeb3();
            if (!contract) return;
        }

        const count = await contract.methods.getTransactionCount().call();
        const tbody = document.getElementById('transactionList');
        tbody.innerHTML = '';

        for (let i = 0; i < count; i++) {
            const txId = await contract.methods.getTransactionIdByIndex(i).call();
            const transaction = await contract.methods.getTransaction(txId).call();
            
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${txId.substring(0, 10)}...</td>
                <td>${transaction.sender.fullName}</td>
                <td>${transaction.receiver.fullName}</td>
                <td>${web3.utils.fromWei(transaction.amount)} ${transaction.currency}</td>
                <td>${new Date(transaction.timestamp * 1000).toLocaleString()}</td>
                <td>${['PROCESSING', 'SUCCESS', 'FAILED'][transaction.status]}</td>
                <td><button onclick="showTransactionDetails('${txId}')">Xem chi tiết</button></td>
            `;
        }
    } catch (error) {
        console.error('Lỗi khi tải giao dịch:', error);
        alert('Không thể tải danh sách giao dịch: ' + error.message);
    }
}

// Hàm tìm kiếm giao dịch
async function searchTransaction() {
    try {
        if (!contract) {
            alert('Đang kết nối với blockchain...');
            await initWeb3();
            if (!contract) return;
        }

        const transactionId = document.getElementById('transactionId').value;
        if (!transactionId) {
            alert('Vui lòng nhập ID giao dịch');
            return;
        }

        const transaction = await contract.methods.getTransaction(transactionId).call();
        displaySingleTransaction(transaction, transactionId);
    } catch (error) {
        console.error('Lỗi khi tìm kiếm:', error);
        document.getElementById('singleTransaction').innerHTML = 
            `<p style="color: red;">Không tìm thấy giao dịch: ${error.message}</p>`;
    }
}

// Hàm hiển thị chi tiết một giao dịch
function displaySingleTransaction(transaction, transactionId) {
    const statusMap = ['PROCESSING', 'SUCCESS', 'FAILED'];
    const html = `
        <h3>Chi tiết giao dịch</h3>
        <table>
            <tr>
                <td><strong>ID Giao dịch:</strong></td>
                <td>${transactionId}</td>
            </tr>
            <tr>
                <td><strong>Người gửi:</strong></td>
                <td>${transaction.sender.fullName} (${transaction.sender.bankName})</td>
            </tr>
            <tr>
                <td><strong>Người nhận:</strong></td>
                <td>${transaction.receiver.fullName} (${transaction.receiver.bankName})</td>
            </tr>
            <tr>
                <td><strong>Số tiền:</strong></td>
                <td>${web3.utils.fromWei(transaction.amount)} ${transaction.currency}</td>
            </tr>
            <tr>
                <td><strong>Phí giao dịch:</strong></td>
                <td>${web3.utils.fromWei(transaction.fee)} ${transaction.currency}</td>
            </tr>
            <tr>
                <td><strong>Thời gian:</strong></td>
                <td>${new Date(transaction.timestamp * 1000).toLocaleString()}</td>
            </tr>
            <tr>
                <td><strong>Nội dung:</strong></td>
                <td>${transaction.note}</td>
            </tr>
            <tr>
                <td><strong>Phương thức:</strong></td>
                <td>${transaction.paymentMethod}</td>
            </tr>
            <tr>
                <td><strong>Trạng thái:</strong></td>
                <td>${statusMap[transaction.status]}</td>
            </tr>
        </table>
    `;
    document.getElementById('singleTransaction').innerHTML = html;
}

// Hàm xem chi tiết giao dịch
async function showTransactionDetails(transactionId) {
    try {
        const transaction = await contract.methods.getTransaction(transactionId).call();
        displaySingleTransaction(transaction, transactionId);
        document.getElementById('singleTransaction').scrollIntoView();
    } catch (error) {
        console.error('Lỗi khi tải chi tiết giao dịch:', error);
        alert('Không thể tải chi tiết giao dịch: ' + error.message);
    }
}

// Khởi tạo khi trang được load
document.addEventListener('DOMContentLoaded', () => {
    loadTransactions();
    setupFormHandler();
});

// Load giao dịch từ localStorage
function loadTransactions() {
    const savedTransactions = localStorage.getItem('transactions');
    if (savedTransactions) {
        transactions = JSON.parse(savedTransactions);
        displayTransactions();
    }
}

// Thiết lập form handler
function setupFormHandler() {
    const form = document.getElementById('transactionForm');
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        createTransaction();
    });
}

// Hàm tạo giao dịch mới
function createTransaction() {
    const transaction = {
        id: generateTransactionId(),
        timestamp: new Date(),
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
        amount: document.getElementById('amount').value,
        currency: document.getElementById('currency').value,
        fee: document.getElementById('fee').value,
        note: document.getElementById('note').value,
        paymentMethod: document.getElementById('paymentMethod').value,
        status: 'SUCCESS'
    };

    transactions.unshift(transaction);
    localStorage.setItem('transactions', JSON.stringify(transactions));
    displayTransactions();
    document.getElementById('transactionForm').reset();
    alert('Giao dịch đã được tạo thành công!');
}

// Hàm hiển thị danh sách giao dịch
function displayTransactions() {
    const tbody = document.getElementById('transactionList');
    tbody.innerHTML = '';

    transactions.forEach(tx => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td>${new Date(tx.timestamp).toLocaleString()}</td>
            <td>${tx.sender.fullName}</td>
            <td>${tx.receiver.fullName}</td>
            <td>${formatMoney(tx.amount, tx.currency)}</td>
            <td>${tx.status}</td>
            <td><button onclick="showTransactionDetails('${tx.id}')">Xem chi tiết</button></td>
        `;
    });
}

// Hàm hiển thị chi tiết giao dịch
function showTransactionDetails(transactionId) {
    const transaction = transactions.find(tx => tx.id === transactionId);
    if (!transaction) return;

    const details = `
        Chi tiết giao dịch:
        
        Thời gian: ${new Date(transaction.timestamp).toLocaleString()}
        
        NGƯỜI GỬI
        Họ tên: ${transaction.sender.fullName}
        Số tài khoản: ${transaction.sender.accountNumber}
        Ngân hàng: ${transaction.sender.bankName}
        
        NGƯỜI NHẬN
        Họ tên: ${transaction.receiver.fullName}
        Số tài khoản: ${transaction.receiver.accountNumber}
        Ngân hàng: ${transaction.receiver.bankName}
        
        THÔNG TIN GIAO DỊCH
        Số tiền: ${formatMoney(transaction.amount, transaction.currency)}
        Phí giao dịch: ${formatMoney(transaction.fee, transaction.currency)}
        Nội dung: ${transaction.note}
        Phương thức: ${transaction.paymentMethod}
        Trạng thái: ${transaction.status}
    `;

    alert(details);
}

// Hàm tạo ID giao dịch
function generateTransactionId() {
    return 'TX' + Date.now() + Math.random().toString(36).substr(2, 9);
}

// Hàm format tiền tệ
function formatMoney(amount, currency) {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: currency
    }).format(amount);
} 