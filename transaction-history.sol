// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TransactionHistory {
    // Cấu trúc thông tin người dùng
    struct User {
        string fullName;
        string accountNumber;
        string bankName;
    }

    // Cấu trúc thông tin giao dịch
    struct Transaction {
        bytes32 transactionId;      // Mã giao dịch unique
        User sender;                // Thông tin người gửi
        User receiver;              // Thông tin người nhận
        uint256 amount;             // Số tiền
        string currency;            // Loại tiền tệ
        uint256 fee;                // Phí giao dịch
        uint256 timestamp;          // Thời gian giao dịch
        string note;                // Nội dung chuyển tiền
        string paymentMethod;       // Phương thức thanh toán
        TransactionStatus status;   // Trạng thái giao dịch
        string signature;           // Chữ ký số
        string qrCode;              // Mã QR
    }

    // Enum cho trạng thái giao dịch
    enum TransactionStatus { PROCESSING, SUCCESS, FAILED }

    // Mapping để lưu trữ giao dịch theo mã giao dịch
    mapping(bytes32 => Transaction) public transactions;
    
    // Array để lưu trữ tất cả các mã giao dịch
    bytes32[] public transactionIds;

    // Event được emit khi có giao dịch mới
    event NewTransaction(
        bytes32 indexed transactionId,
        address indexed creator,
        uint256 timestamp
    );

    // Hàm tạo giao dịch mới
    function createTransaction(
        string memory senderName,
        string memory senderAccount,
        string memory senderBank,
        string memory receiverName,
        string memory receiverAccount,
        string memory receiverBank,
        uint256 amount,
        string memory currency,
        uint256 fee,
        string memory note,
        string memory paymentMethod,
        string memory signature,
        string memory qrCode
    ) public returns (bytes32) {
        // Tạo mã giao dịch unique bằng keccak256
        bytes32 transactionId = keccak256(
            abi.encodePacked(
                block.timestamp,
                msg.sender,
                senderAccount,
                receiverAccount
            )
        );

        // Tạo đối tượng giao dịch mới
        Transaction storage newTx = transactions[transactionId];
        
        // Thiết lập thông tin người gửi
        newTx.sender = User(senderName, senderAccount, senderBank);
        
        // Thiết lập thông tin người nhận
        newTx.receiver = User(receiverName, receiverAccount, receiverBank);
        
        // Thiết lập thông tin giao dịch
        newTx.transactionId = transactionId;
        newTx.amount = amount;
        newTx.currency = currency;
        newTx.fee = fee;
        newTx.timestamp = block.timestamp;
        newTx.note = note;
        newTx.paymentMethod = paymentMethod;
        newTx.status = TransactionStatus.PROCESSING;
        newTx.signature = signature;
        newTx.qrCode = qrCode;

        // Thêm mã giao dịch vào array
        transactionIds.push(transactionId);

        // Emit event
        emit NewTransaction(transactionId, msg.sender, block.timestamp);

        return transactionId;
    }

    // Hàm cập nhật trạng thái giao dịch
    function updateTransactionStatus(bytes32 transactionId, TransactionStatus newStatus) public {
        require(transactions[transactionId].timestamp != 0, "Transaction does not exist");
        transactions[transactionId].status = newStatus;
    }

    // Hàm lấy thông tin giao dịch
    function getTransaction(bytes32 transactionId) public view returns (
        User memory sender,
        User memory receiver,
        uint256 amount,
        string memory currency,
        uint256 fee,
        uint256 timestamp,
        string memory note,
        string memory paymentMethod,
        TransactionStatus status,
        string memory signature,
        string memory qrCode
    ) {
        Transaction storage tx = transactions[transactionId];
        require(tx.timestamp != 0, "Transaction does not exist");
        
        return (
            tx.sender,
            tx.receiver,
            tx.amount,
            tx.currency,
            tx.fee,
            tx.timestamp,
            tx.note,
            tx.paymentMethod,
            tx.status,
            tx.signature,
            tx.qrCode
        );
    }

    // Hàm lấy số lượng giao dịch
    function getTransactionCount() public view returns (uint256) {
        return transactionIds.length;
    }

    // Hàm lấy mã giao dịch theo index
    function getTransactionIdByIndex(uint256 index) public view returns (bytes32) {
        require(index < transactionIds.length, "Index out of bounds");
        return transactionIds[index];
    }
}
