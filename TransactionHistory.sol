// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TransactionHistory {
    // Cấu trúc thông tin người dùng
    struct User {
        string fullName;
        string accountNumber;
        string bankName;
    }

    // Cấu trúc thông tin giao dịch cơ bản
    struct TransactionBasic {
        bytes32 id;
        User sender;
        User receiver;
        uint256 amount;
        uint256 timestamp;
    }

    // Cấu trúc thông tin chi tiết giao dịch
    struct TransactionDetails {
        string currency;
        uint256 fee;
        string note;
        string paymentMethod;
        TransactionStatus status;
    }

    // Enum cho trạng thái giao dịch
    enum TransactionStatus { PROCESSING, SUCCESS, FAILED }

    // Tách thành 2 mapping để giảm độ sâu của stack
    mapping(bytes32 => TransactionBasic) public basicInfo;
    mapping(bytes32 => TransactionDetails) public details;
    
    // Array để lưu trữ tất cả các mã giao dịch
    bytes32[] public transactionIds;

    // Event được emit khi có giao dịch mới
    event NewTransaction(
        bytes32 indexed transactionId,
        string senderName,
        string receiverName,
        uint256 amount,
        uint256 timestamp
    );

    // Tách thành hai hàm để tránh Stack too deep
    function createTransaction(
        string memory senderName,
        string memory senderAccount,
        string memory senderBank,
        string memory receiverName,
        string memory receiverAccount,
        string memory receiverBank,
        uint256 amount
    ) public returns (bytes32) {
        bytes32 txId = keccak256(
            abi.encodePacked(
                block.timestamp,
                msg.sender,
                senderAccount,
                receiverAccount
            )
        );

        // Lưu thông tin cơ bản
        basicInfo[txId] = TransactionBasic({
            id: txId,
            sender: User(senderName, senderAccount, senderBank),
            receiver: User(receiverName, receiverAccount, receiverBank),
            amount: amount,
            timestamp: block.timestamp
        });

        // Khởi tạo details với giá trị mặc định
        details[txId] = TransactionDetails({
            currency: "",
            fee: 0,
            note: "",
            paymentMethod: "",
            status: TransactionStatus.PROCESSING
        });

        transactionIds.push(txId);

        // Emit event với đầy đủ thông tin
        emit NewTransaction(
            txId,
            senderName,
            receiverName,
            amount,
            block.timestamp
        );

        return txId;
    }

    // Hàm thứ hai để cập nhật thông tin bổ sung
    function updateTransactionDetails(
        bytes32 txId,
        string memory currency,
        uint256 fee,
        string memory note,
        string memory paymentMethod
    ) public {
        require(basicInfo[txId].timestamp != 0, "Transaction does not exist");
        
        details[txId].currency = currency;
        details[txId].fee = fee;
        details[txId].note = note;
        details[txId].paymentMethod = paymentMethod;
        details[txId].status = TransactionStatus.SUCCESS;
    }

    // Hàm cập nhật trạng thái giao dịch
    function updateTransactionStatus(bytes32 transactionId, TransactionStatus newStatus) public {
        require(basicInfo[transactionId].timestamp != 0, "Transaction does not exist");
        details[transactionId].status = newStatus;
    }

    // Hàm lấy thông tin giao dịch cơ bản
    function getBasicInfo(bytes32 txId) public view returns (
        string memory senderName,
        string memory senderAccount,
        string memory senderBank,
        string memory receiverName,
        string memory receiverAccount,
        string memory receiverBank,
        uint256 amount,
        uint256 timestamp
    ) {
        TransactionBasic storage basic = basicInfo[txId];
        require(basic.timestamp != 0, "Transaction does not exist");
        
        return (
            basic.sender.fullName,
            basic.sender.accountNumber,
            basic.sender.bankName,
            basic.receiver.fullName,
            basic.receiver.accountNumber,
            basic.receiver.bankName,
            basic.amount,
            basic.timestamp
        );
    }

    // Hàm lấy thông tin chi tiết giao dịch
    function getDetails(bytes32 txId) public view returns (
        string memory currency,
        uint256 fee,
        string memory note,
        string memory paymentMethod,
        TransactionStatus status
    ) {
        require(basicInfo[txId].timestamp != 0, "Transaction does not exist");
        TransactionDetails storage txDetails = details[txId];
        
        return (
            txDetails.currency,
            txDetails.fee,
            txDetails.note,
            txDetails.paymentMethod,
            txDetails.status
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