import React, { useState, useRef, useEffect } from "react";
import Segment from "./segment";

const Balance = ({ balance }: { balance: number }) => {
  return (
    <Segment>
      <h2>Balance: {balance}BTC</h2>
    </Segment>
  );
};

export default Balance;
