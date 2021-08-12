import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import Segment from "./components/segment";
import "./App.css";
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
};

const App = () => {
  const [loading, setLoading] = useState(true);
  const [transactionRes, setTransactionRes] = useState<TransactionResult>({
    success: false,
    type: "None",
    time: 0,
    shards: [],
  });
  const publicKey = useRef("");
  const privKey = useRef("");
  const transactionAmount = useRef(0);
  const serverUrl =
    process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

  useEffect(() => {
    const initializeKeys = async () => {
      const { data } = await axios.get(`${serverUrl}/api/get-user`);
      publicKey.current = data.publicKey;
      privKey.current = data.privKey;
      setLoading(false);
    };

    initializeKeys();
  }, []);

  const validate = async (sequential: boolean) => {
    if (loading) return;
    setLoading(true);
    const { data } = await axios.post(
      `${serverUrl}/api/${sequential ? "normal" : "shard"}`,
      { publicKey, privKey, transactionAmount }
    );
    setTransactionRes(data.result);
    setLoading(false);
  };

  console.log(transactionRes);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Sharding POC</h1>
      </header>
      <button onClick={() => validate(true)}>Sequential</button>
      <button onClick={() => validate(false)}>Sharding</button>
    </div>
  );
};

export default App;
