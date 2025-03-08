const TransactionHistory = artifacts.require("TransactionHistory");

module.exports = function(deployer) {
  deployer.deploy(TransactionHistory);
}; 