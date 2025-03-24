'use client';

import React, { useState, useRef } from "react";
import { FileText, Send, Loader2, Upload } from 'lucide-react';

const RAGPage = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
  
    setIsProcessing(true);
  
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("http://localhost:5000/generate_data_store", {
        method: "POST",
        body: formData,
      });
  
      const data = await response.json();
      if (response.ok) {
        setIsReady(true);
      } else {
        console.error("Error:", data.error);
      }
    } catch (error) {
      console.error("Upload failed:", error);
    } finally {
      setIsProcessing(false);
    }
  };
  

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
  
    setMessages([...messages, { role: "user", content: input }]);
    setIsLoading(true);
  
    try {
      const response = await fetch("http://localhost:5000/query_data", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query_text: input }),
      });
  
      const data = await response.json();
      if (response.ok) {
        setMessages((prev) => [...prev, { role: "assistant", content: data.response.generated_prompt }]);
      } else {
        console.error("Error:", data.error);
      }
    } catch (error) {
      console.error("Query failed:", error);
    } finally {
      setIsLoading(false);
      setInput("");
    }
  };
  

  const triggerFileInput = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div className="font-inter bg-white min-h-screen relative">
      {/* Main Content */}
      <main className="max-w-6xl mx-auto p-6">
        {!isReady ? (
          <div className="flex flex-col items-center justify-center min-h-[70vh]">
            <div className="bg-pink-50 border border-pink-100 rounded-lg p-8 w-full max-w-lg text-center">
              <div className="mb-6">
                <FileText size={48} className="mx-auto text-pink-400" />
                <h2 className="text-2xl font-semibold mt-4 text-gray-800">Upload a PDF Document</h2>
                <p className="text-gray-600 mt-2">
                  Upload your PDF to ask questions and get insights using AI
                </p>
              </div>
              
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                ref={fileInputRef}
                className="hidden"
              />
              
              {file ? (
                <div className="mb-4">
                  <div className="flex items-center justify-between bg-white p-3 rounded border border-pink-200">
                    <span className="truncate max-w-[250px]">{file.name}</span>
                    <span className="text-xs text-gray-500">
                      {(file.size / (1024 * 1024)).toFixed(2)} MB
                    </span>
                  </div>
                </div>
              ) : null}
              
              {!file ? (
                <button
                  onClick={triggerFileInput}
                  className="w-full bg-pink-500 hover:bg-pink-600 text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center justify-center"
                >
                  <Upload size={18} className="mr-2" />
                  Select PDF
                </button>
              ) : isProcessing ? (
                <button
                  disabled
                  className="w-full bg-pink-300 text-white font-medium py-2 px-4 rounded-md flex items-center justify-center"
                >
                  <Loader2 size={18} className="mr-2 animate-spin" />
                  Processing...
                </button>
              ) : (
                <button
                  onClick={handleUpload}
                  className="w-full bg-pink-500 hover:bg-pink-600 text-white font-medium py-2 px-4 rounded-md transition-colors"
                >
                  Process Document
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="flex flex-col h-[90vh]">
            <div className="bg-pink-50 rounded-t-lg p-4 border border-pink-100">
              <div className="flex items-center">
                <FileText size={20} className="text-pink-500 mr-2" />
                <span className="font-medium">{file?.name}</span>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto border-l border-r border-pink-100 p-4 bg-white">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 mt-10">
                  <p>Ask questions about your document</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((message, index) => (
                    <div
                      key={index}
                      className={`flex ${
                        message.role === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg p-3 ${
                          message.role === 'user'
                            ? 'bg-pink-500 text-white'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {message.content}
                      </div>
                    </div>
                  ))}
                  
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 rounded-lg p-3 flex items-center">
                        <Loader2 size={18} className="animate-spin text-pink-500" />
                        <span className="ml-2 text-gray-600">Thinking...</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
            
            <div className="border border-pink-100 rounded-b-lg bg-white p-3">
              <form onSubmit={handleSubmit} className="flex items-center">
                <input
                  type="text"
                  value={input}
                  onChange={handleInputChange}
                  placeholder="Ask a question about your document..."
                  className="flex-1 border border-pink-200 rounded-l-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-pink-300"
                />
                <button
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  className={`bg-pink-500 ${
                    isLoading || !input.trim() ? 'opacity-50' : 'hover:bg-pink-600'
                  } text-white rounded-r-md py-2 px-4 flex items-center`}
                >
                  {isLoading ? (
                    <Loader2 size={18} className="animate-spin" />
                  ) : (
                    <Send size={18} />
                  )}
                </button>
              </form>
            </div>
          </div>
        )}
      </main>
      

    </div>
  );
};

export default RAGPage;
