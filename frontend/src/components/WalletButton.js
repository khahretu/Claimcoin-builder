import React, { useState } from "react";
import { ethers } from "ethers";

const WalletButton = () => {
    const [walletAddress, setWalletAddress] = useState("");

    const connectWallet = async () => {
        if (window.ethereum) {
            try {
                const accounts = await window.ethereum.request({
                    method: "eth_requestAccounts",
                });
                setWalletAddress(accounts[0]);
            } catch (error) {
                console.error("Connection Failed:", error);
            }
        } else {
            alert("Please install a wallet like MetaMask.");
        }
    };

    return (
        <div>
            <button onClick={connectWallet}>Connect Wallet</button>
            {walletAddress ? <p>Connected: {walletAddress}</p> : <p>Not connected</p>}
        </div>
    );
};

export default WalletButton;