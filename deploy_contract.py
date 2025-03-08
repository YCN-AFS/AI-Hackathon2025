from web3 import Web3
from solcx import install_solc, compile_source, get_installed_solc_versions
import time

# Cài đặt và set version solc
def setup_solc():
    try:
        print("Đang kiểm tra Solidity compiler...")
        # Cài đặt solc version 0.8.0
        print("Đang cài đặt Solidity compiler v0.8.0...")
        install_solc('0.8.0', show_progress=True)
        time.sleep(2)  # Đợi một chút để đảm bảo cài đặt hoàn tất
        
        # Set version mặc định
        from solcx import set_solc_version
        set_solc_version('0.8.0')
        
        print("Solidity compiler đã được cài đặt thành công!")
        return True
    except Exception as e:
        print(f"Lỗi khi cài đặt solc: {str(e)}")
        return False

# Kết nối đến blockchain (ví dụ: local Ganache)
def setup_web3():
    try:
        w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
        if not w3.is_connected():
            print("Không thể kết nối đến blockchain. Hãy đảm bảo Ganache đang chạy.")
            return None
        return w3
    except Exception as e:
        print(f"Lỗi khi kết nối blockchain: {str(e)}")
        return None

# Đọc và compile contract
def compile_contract():
    try:
        with open('TransactionHistory.sol', 'r', encoding='utf-8') as file:
            contract_source = file.read()

        print("Đang biên dịch contract...")
        compiled_sol = compile_source(
            contract_source,
            output_values=['abi', 'bin']
        )
        
        contract_id, contract_interface = compiled_sol.popitem()
        return contract_interface['abi'], contract_interface['bin']
    except Exception as e:
        print(f"Lỗi khi compile contract: {str(e)}")
        return None, None

# Deploy contract
def deploy_contract(w3, abi, bytecode):
    if not abi or not bytecode:
        print("Không có ABI hoặc bytecode để deploy")
        return None
        
    try:
        # Lấy account để deploy
        account = w3.eth.accounts[0]
        
        # Tạo contract instance
        Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        
        print("Đang ước tính gas...")
        # Ước tính gas
        gas_estimate = Contract.constructor().estimate_gas()
        
        print("Đang deploy contract...")
        # Deploy contract
        tx_hash = Contract.constructor().transact({
            'from': account,
            'gas': gas_estimate
        })
        
        # Đợi transaction được xác nhận
        print("Đang đợi xác nhận...")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Lấy địa chỉ contract
        contract_address = tx_receipt['contractAddress']
        
        print(f'Contract đã được deploy thành công!')
        print(f'Địa chỉ contract: {contract_address}')
        
        # Lưu thông tin vào file
        save_contract_info(contract_address, abi)
        
        return contract_address
        
    except Exception as e:
        print(f'Lỗi khi deploy contract: {str(e)}')
        return None

def save_contract_info(address, abi):
    try:
        import json
        contract_info = {
            'address': address,
            'abi': abi
        }
        with open('contract_info.json', 'w', encoding='utf-8') as f:
            json.dump(contract_info, f, indent=2)
        print("Đã lưu thông tin contract vào contract_info.json")
    except Exception as e:
        print(f"Lỗi khi lưu thông tin contract: {str(e)}")

if __name__ == "__main__":
    print("Bắt đầu quá trình deploy contract...")
    
    # Cài đặt solc
    if not setup_solc():
        print("Không thể tiếp tục vì lỗi cài đặt Solidity compiler")
        exit(1)
    
    # Kết nối blockchain
    w3 = setup_web3()
    if not w3:
        print("Không thể tiếp tục vì lỗi kết nối blockchain")
        exit(1)
        
    print("Đã kết nối đến blockchain!")
    print(f"Account có sẵn: {w3.eth.accounts[0]}")
    
    # Compile contract
    abi, bytecode = compile_contract()
    if not abi or not bytecode:
        print("Không thể tiếp tục vì lỗi compile contract")
        exit(1)
        
    print("Contract đã được biên dịch thành công!")
    
    # Deploy contract
    contract_address = deploy_contract(w3, abi, bytecode)
    
    if contract_address:
        print("\nBạn có thể sử dụng địa chỉ này trong file blockchain_api.py")
        print(f"CONTRACT_ADDRESS = '{contract_address}'")
    else:
        print("Deploy contract không thành công") 