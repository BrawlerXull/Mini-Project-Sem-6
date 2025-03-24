"use client";
import React, { useState } from "react";
import Link from "next/link";


import React from "react";
import { ArrowRight, Check, Mic, Heart, AlertCircle } from "lucide-react";
import Link from "next/link";



import Image from "next/image";
import Navbar from "../../../components/navbar";

const Navbar = () => {
  return (
    <>
    <header className="fixed w-full bg-transparent backdrop-blur-sm z-50 border-b border-pink-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          {/* Logo Section */}
          <Link href="/" className="flex items-center space-x-2 animate-fadeIn">
            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-pink-400 to-pink-600">
              Atmos
            </span>
          </Link>
        </div>
      </div>
    </header>

    {isMenuOpen && (
      <div className="md:hidden fixed inset-0 z-50 bg-transparent backdrop-blur-sm">
        <div className="p-4">
          <div className="flex justify-end">
            <button
              onClick={() => setIsMenuOpen(false)}
              className="p-2 text-gray-600 hover:text-pink-500"
            >
              ✕
            </button>
          </div>
          <nav className="flex flex-col space-y-4 p-4">
            <Link
              href="/dashboard"
              className="text-gray-600 font-medium hover:text-pink-500 transition-colors"
              onClick={() => setIsMenuOpen(false)}
            >
              Dashboard
            </Link>
            <Link
              href="/health"
              className="text-gray-600 font-medium hover:text-pink-500 transition-colors"
              onClick={() => setIsMenuOpen(false)}
            >
              Diagnose
            </Link>
          </nav>
        </div>
      </div>
    )}
  </>
  );
};

export default Navbar;
