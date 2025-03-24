;

import React from "react";
import Sidebar from "../../components/side-bar";


interface InnerPageLayoutProps {
  children: React.ReactNode;
}

const InnerPageLayout: React.FC<InnerPageLayoutProps> = ({ children }) => {
  return <Sidebar>{children}</Sidebar>;
};

export default InnerPageLayout;
