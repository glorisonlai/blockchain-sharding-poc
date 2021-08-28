import React, { useState, useEffect } from "react";
import axios from "axios";
import Segment from "./components/segment";
import "./App.css";
import explanationMarkdown from "./components/explanation.md"; // Needed to get absolute filename
import MarkdownParser from "./components/markdown";
import forge from "node-forge";
import dotenv from "dotenv";
dotenv.config();

type Shard = {
  id: number;
  validatedResults: boolean[];
};

type TransactionResult = {
  success: boolean;
  type: string;
  time: number;
  shards: Shard[];
  balance: number;
  errorMsg?: string;
};

type UserResponse = {
  user: string;
  balance: number;
  privKey: string;
  pubKey: string;
};

type TransactionForm = {
  shards: number;
  transactionAmount: number;
  payee: string;
} & UserResponse;

enum TransactionEnum {
  serial = "Serial",
  parallel = "Shard",
}

const App = () => {
  const CryptoApp = () => {
    const [loading, setLoading] = useState(true);
    const [transactionRes, setTransactionRes] = useState<TransactionResult>({
      success: false,
      type: "None",
      time: 0,
      shards: [],
      balance: 0,
    });
    const [transactionForm, setTransactionForm] = useState<TransactionForm>({
      user: "",
      balance: 0,
      privKey: "",
      pubKey: "",
      shards: 10,
      transactionAmount: 0,
      payee: "",
    });
    const serverUrl =
      process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

    useEffect(() => {
      const initializeKeys = async () => {
        const res = await axios.get(`${serverUrl}/get-user`);
        const data: UserResponse[] = res.data;
        setLoading(false);
      };

      initializeKeys();
    }, []);

    const signTransaction = (transaction: string, privKeyPEM: string) => {
      const md = forge.md.sha256.create();
      md.update(transaction, "utf8");
      const privKey = forge.pki.privateKeyFromPem(privKeyPEM);
      return Buffer.from(forge.util.binary.raw.decode(privKey.sign(md)));
    };

    const sendMoney = async (sequential: boolean, userKey: number) => {
      if (loading) return;
      if (userKey < 0 || userKey >= transactionForm.users.length) return;
      setLoading(true);
      const serializedTransaction = `${transactionForm.transactionAmount}:${transactionForm.user}:${transactionForm.pubKey}:${transactionForm.payee}`;
      const signature = signTransaction(
        serializedTransaction,
        transactionForm.privKey
      );
      console.log(signature);
      const { data } = await axios.post(
        `${serverUrl}/${sequential ? "normal" : "shard"}`,
        {
          transaction: serializedTransaction,
          signature,
        }
      );
      const res: TransactionResult = {
        success: data.success,
        type: data.type,
        time: data.time,
        shards: data.shards,
        balance: data.balance,
        errorMsg: data.errorMsg,
      };
      setTransactionForm((transactionForm) => ({
        ...transactionForm,
        ...{ balance: res.balance, transactionAmount: 0 },
      }));
      setTransactionRes(res);
      setLoading(false);
    };

    return (
      <div>
        <Segment>
          <h2>Balance: {transactionForm.balance}BTC</h2>
          <form>
            <label>Public Key: </label>
            <input
              id="pubKey"
              value={transactionForm.pubKey}
              onChange={(e) =>
                setTransactionForm((transactionForm) => ({
                  ...transactionForm,
                  pubKey: e.target.value,
                }))
              }
              type="text"
            />
            <br />
            <label>Private Key: </label>
            <input
              id="privKey"
              value={transactionForm.privKey}
              onChange={(e) =>
                setTransactionForm((transactionForm) => ({
                  ...transactionForm,
                  privKey: e.target.value,
                }))
              }
              type="text"
            />
          </form>
        </Segment>
        <Segment>
          <form>
            <label>Amount: </label>
            <input
              id="transactionAmount"
              value={transactionForm.transactionAmount}
              onChange={(e) =>
                setTransactionForm((transactionForm) => ({
                  ...transactionForm,
                  transactionAmount: parseInt(e.target.value),
                }))
              }
              type="number"
            />
            <br />
            <label>Shards (Max 10): </label>
            <input
              id="numShards"
              value={transactionForm.shards}
              onChange={(e) =>
                setTransactionForm((transactionForm) => ({
                  ...transactionForm,
                  shards: Math.min(parseInt(e.target.value), 10),
                }))
              }
              type="number"
            />
          </form>
          <br />
          <button
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            onClick={() => sendMoney(true, 0)}
          >
            Sequential
          </button>
          <button
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            onClick={() => sendMoney(false, 0)}
          >
            Sharding
          </button>
        </Segment>
      </div>
    );
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Sharding POC</h1>
      </header>
      <CryptoApp />
      <MarkdownParser filename={explanationMarkdown}></MarkdownParser>
    </div>
  );
};

export default App;
