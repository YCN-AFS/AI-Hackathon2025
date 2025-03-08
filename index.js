const Web3 = require('web3');
require('dotenv').config();

// Kết nối đến blockchain (ví dụ với Ganache local)
const web3 = new Web3('http://localhost:8545');

// ABI của smart contract (sẽ có sau khi compile contract)
const contractABI = require('./build/contracts/TransactionHistory.json').abi;
const contractAddress = 'YOUR_CONTRACT_ADDRESS'; // Địa chỉ sau khi deploy

// Tạo instance của contract
const contract = new web3.eth.Contract(contractABI, contractAddress);

// Hàm tạo giao dịch mới
async function createNewTransaction(
    senderName,
    senderAccount,
    senderBank,
    receiverName,
    receiverAccount,
    receiverBank,
    amount,
    currency,
    fee,
    note,
    paymentMethod,
    signature,
    qrCode
) {
    try {
        const accounts = await web3.eth.getAccounts();
        const result = await contract.methods.createTransaction(
            senderName,
            senderAccount,
            senderBank,
            receiverName,
            receiverAccount,
            receiverBank,
            amount,
            currency,
            fee,
            note,
            paymentMethod,
            signature,
            qrCode
        ).send({ from: accounts[0] });

        console.log('Giao dịch đã được tạo:', result);
        return result;
    } catch (error) {
        console.error('Lỗi khi tạo giao dịch:', error);
        throw error;
    }
}

// Hàm lấy thông tin giao dịch
async function getTransactionInfo(transactionId) {
    try {
        const result = await contract.methods.getTransaction(transactionId).call();
        console.log('Thông tin giao dịch:', result);
        return result;
    } catch (error) {
        console.error('Lỗi khi lấy thông tin giao dịch:', error);
        throw error;
    }
}

// Ví dụ sử dụng
async function main() {
    try {
        // Tạo giao dịch mới
        const newTx = await createNewTransaction(
            "Nguyen Van A",
            "123456789",
            "VietcomBank",
            "Tran Thi B",
            "987654321",
            "TPBank",
            web3.utils.toWei("1", "ether"), // 1 ETH
            "VND",
            web3.utils.toWei("0.001", "ether"), // Phí
            "Chuyển tiền",
            "Bank Transfer",
            "signature123",
            "qr123"
        );

        // Lấy số lượng giao dịch
        const count = await contract.methods.getTransactionCount().call();
        console.log('Tổng số giao dịch:', count);

        // Lấy ID giao dịch cuối cùng
        const lastTxId = await contract.methods.getTransactionIdByIndex(count - 1).call();
        
        // Lấy thông tin giao dịch
        const txInfo = await getTransactionInfo(lastTxId);
        console.log('Chi tiết giao dịch vừa tạo:', txInfo);

    } catch (error) {
        console.error('Lỗi:', error);
    }
}

main(); 