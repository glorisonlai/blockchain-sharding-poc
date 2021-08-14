import React, { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";

const MarkdownParser = ({ filename }: { filename: string }) => {
  const [html, setHtml] = useState("");

  useEffect(() => {
    fetch(filename)
      .then((data) => data.text())
      .then((text) => setHtml(text));
  });
  return <ReactMarkdown children={html} />;
};

export default MarkdownParser;
