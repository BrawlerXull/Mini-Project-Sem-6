'use client';
import React, { useState, useRef } from "react";
import { FileText, Upload, Loader2, Volume2, ChevronDown, ChevronUp, Play, Pause } from 'lucide-react';
import ReactMarkdown from "react-markdown";
import removeMarkdown from 'remove-markdown';

const PDFSummarizer = () => {
  const [file, setFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [summary, setSummary] = useState('');
  const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);
  const [audioUrl, setAudioUrl] = useState('');
  const [isPlaying, setIsPlaying] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [expandedQuestions, setExpandedQuestions] = useState({});
  const fileInputRef = useRef(null);
  const audioRef = useRef(null);
  const [isOpen, setIsOpen] = useState(false);
  const [selected, setSelected] = useState("Llama")

  

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      // Reset states when a new file is uploaded
      setSummary('');
      setAudioUrl('');
      setQuestions([]);
      setExpandedQuestions({});
    }
  };
  
  const handleProcessPDF = async () => {
    if (!file) return;
  
    setIsProcessing(true);
  
    const formData = new FormData();
    formData.append("file", file);
    formData.append("model", selected);
  
    try {
      // Step 1: Get the summary
      const summaryResponse = await fetch("http://localhost:5000/summarize", {
        method: "POST",
        body: formData,
      });
  
      if (!summaryResponse.ok) {
        throw new Error("Failed to process PDF for summary");
      }
  
      const summaryData = await summaryResponse.json();
      console.log("Summary:", summaryData.summary);
  
      // Step 2: Get the questions
      const questionsResponse = await fetch("http://localhost:5000/generate_questions", {
          method: "POST",
          body: formData,
      });

      if (!questionsResponse.ok) {
          throw new Error("Failed to process PDF for questions");
      }

      const questionsData = await questionsResponse.json();
      console.log("Questions:", questionsData.questions);

      // Ensure that the response has the expected 'questions' structure
      const questionsArray = Array.isArray(questionsData.questions) ? questionsData.questions : [];

      // If questions are not in the expected format, handle this scenario (optional)
      if (questionsArray.length === 0) {
          console.error("No valid questions received");
          setQuestions([]); // Set questions to empty if no valid questions
          return;
      }

      console.log("Questions array:", questionsArray);

  
      // Set the state for summary and questions
      setSummary(summaryData.summary);
      setQuestions(questionsArray);
  
    } catch (error) {
      console.error("Error:", error);
      setSummary("Failed to generate summary. Please try again.");
      setQuestions([]);
    } finally {
      setIsProcessing(false);
    }
  };
  
  const handleSelect = (option) => {
    setSelected(option);
    setIsOpen(false);
  };
  

  const generateAudio = async () => {
    if (!summary) return;
  
    let plainText = removeMarkdown(summary);  // 👈 Strip Markdown here
    setIsGeneratingAudio(true);
    console.log(plainText)
    plainText = summary
    .replace(/\*\*(.*?)\*\*/g, '$1')  // remove **bold**
    .replace(/\*(.*?)\*/g, '$1')      // remove *italic*
    .replace(/`{1,3}(.*?)`{1,3}/g, '$1') // remove inline code
    .replace(/#+\s?(.*)/g, '$1');     // remove headings
  
    console.log(plainText)
  
  
    try {
      const response = await fetch('https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB', {
        method: 'POST',
        headers: {
          'xi-api-key': 'sk_28a2e09326180461b123644ec0d2e36aa55b1eb74645729d',
          'Content-Type': 'application/json',
          'Accept': 'audio/mpeg',
        },
        body: JSON.stringify({
          text: plainText,
          voice_settings: {
            stability: 0.75,
            similarity_boost: 0.75
          }
        }),
      });
  
      if (!response.ok) {
        throw new Error('Failed to generate audio');
      }
  
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      setAudioUrl(audioUrl);
    } catch (error) {
      console.error('Audio generation error:', error);
    } finally {
      setIsGeneratingAudio(false);
    }
  };
  

  const toggleQuestion = (index) => {
    setExpandedQuestions(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const toggleAudioPlayback = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const triggerFileInput = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div className="font-inter bg-white min-h-screen relative">
      {/* Header */}
      <header className="bg-pink-50 border-b border-pink-100 py-4 px-6">
        <div className="max-w-6xl mx-auto flex items-center">
          <h1 className="text-3xl font-bold text-pink-500">PDF Summarizer</h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Left Column - Upload Section */}
          <div className="md:col-span-1">
            <div className="bg-pink-50 border border-pink-100 rounded-lg p-6">
              <div className="mb-6 text-center">
                <FileText size={40} className="mx-auto text-pink-400" />
                <h2 className="text-xl font-semibold mt-3 text-gray-800">Upload PDF</h2>
                <p className="text-gray-600 mt-2 text-sm">
                  Upload a PDF to generate a summary and key questions
                </p>
                <div className="relative inline-block text-left w-full">
      <div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="inline-flex justify-between w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none"
        >
          {selected}
          <svg
            className="w-5 h-5 ml-2 -mr-1 text-gray-400"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M5.23 7.21a.75.75 0 011.06.02L10 11.084l3.71-3.854a.75.75 0 111.08 1.04l-4.25 4.417a.75.75 0 01-1.08 0L5.21 8.27a.75.75 0 01.02-1.06z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div>

      {isOpen && (
        <div className="absolute z-10 mt-2 w-full bg-white border border-gray-200 rounded-md shadow-lg">
          <ul className="py-1 text-sm text-gray-700">
            {["Llama", "Custom"].map((option) => (
              <li
                key={option}
                onClick={() => handleSelect(option)}
                className="block px-4 py-2 cursor-pointer hover:bg-gray-100"
              >
                {option}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
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
                    <span className="truncate max-w-[200px] text-sm">{file.name}</span>
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
                  <Upload size={16} className="mr-2" />
                  Select PDF
                </button>
              ) : !summary ? (
                <button
                  onClick={handleProcessPDF}
                  disabled={isProcessing}
                  className={`w-full ${isProcessing ? 'bg-pink-300' : 'bg-pink-500 hover:bg-pink-600'} text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center justify-center`}
                >
                  {isProcessing ? (
                    <>
                      <Loader2 size={16} className="mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    'Generate Summary'
                  )}
                </button>
              ) : (
                <div className="space-y-3">
                  <button
                    onClick={triggerFileInput}
                    className="w-full border border-pink-300 text-pink-500 hover:bg-pink-50 font-medium py-2 px-4 rounded-md transition-colors flex items-center justify-center"
                  >
                    <Upload size={16} className="mr-2" />
                    Upload New PDF
                  </button>
                  
                  {!audioUrl ? (
                    <button
                      onClick={generateAudio}
                      disabled={isGeneratingAudio}
                      className={`w-full ${isGeneratingAudio ? 'bg-pink-300' : 'bg-pink-500 hover:bg-pink-600'} text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center justify-center`}
                    >
                      {isGeneratingAudio ? (
                        <>
                          <Loader2 size={16} className="mr-2 animate-spin" />
                          Generating Audio...
                        </>
                      ) : (
                        <>
                          <Volume2 size={16} className="mr-2" />
                          Generate Audio
                        </>
                      )}
                    </button>
                  ) : (
                    <div className="flex items-center justify-center bg-pink-100 rounded-md p-2">
                      <button
                        onClick={toggleAudioPlayback}
                        className="flex items-center justify-center text-pink-600 hover:text-pink-700"
                      >
                        {isPlaying ? (
                          <Pause size={20} />
                        ) : (
                          <Play size={20} />
                        )}
                      </button>
                      <div className="ml-2 text-sm text-gray-600">
                        {isPlaying ? 'Pause Audio' : 'Play Audio'}
                      </div>
                      {/* Hidden audio element */}
                      <audio
                        ref={audioRef}
                        src={audioUrl}
                        onEnded={() => setIsPlaying(false)}
                        className="hidden"
                      />
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
          
          {/* Right Column - Summary and Questions */}
          <div className="md:col-span-2">
            {isProcessing ? (
              <div className="bg-white border border-pink-100 rounded-lg p-8 flex flex-col items-center justify-center min-h-[400px]">
                <Loader2 size={40} className="text-pink-500 animate-spin mb-4" />
                <h3 className="text-xl font-medium text-gray-700">Analyzing PDF...</h3>
                <p className="text-gray-500 mt-2 text-center">
                  Our AI is reading through your document and generating a comprehensive summary and key questions.
                </p>
              </div>
            ) : summary ? (
              <div className="space-y-6">
                {/* Summary Section */}
                <div className="bg-white border border-pink-100 rounded-lg p-6">
                  <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
                    <span className="bg-pink-100 text-pink-500 rounded-full p-1 mr-2">
                      <FileText size={18} />
                    </span>
                    Document Summary
                  </h3>
                  <div className="prose max-w-none prose-p:leading-relaxed prose-li:my-1 text-gray-700">
                    <ReactMarkdown>{summary}</ReactMarkdown>
                  </div>
                </div>
                
                {/* Questions Section */}
                <div className="space-y-3">
                  {questions.map((item, index) => (
                    <div 
                      key={index} 
                      className="border border-pink-100 rounded-lg overflow-hidden"
                    >
                      <button
                        onClick={() => toggleQuestion(index)}
                        className="w-full flex items-center justify-between bg-pink-50 p-4 text-left hover:bg-pink-100 transition-colors"
                      >
                        <span className="font-medium text-gray-800">{item.question}</span>
                        {expandedQuestions[index] ? (
                          <ChevronUp size={18} className="text-pink-500" />
                        ) : (
                          <ChevronDown size={18} className="text-pink-500" />
                        )}
                      </button>
                      
                      {expandedQuestions[index] && (
                        <div className="p-4 bg-white">
                          <p className="text-gray-700 font-medium">Answer:</p>
                          <p className="text-gray-600">{item.answer}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

              </div>
            ) : (
              <div className="bg-white border border-pink-100 rounded-lg p-8 flex flex-col items-center justify-center min-h-[400px] text-center">
                <FileText size={48} className="text-pink-200 mb-4" />
                <h3 className="text-xl font-medium text-gray-700">No Summary Available</h3>
                <p className="text-gray-500 mt-2 max-w-md">
                  Upload a PDF document and generate a summary to see the results here.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default PDFSummarizer;
