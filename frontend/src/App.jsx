import React from 'react'
import { Toaster } from 'react-hot-toast'
import Sidebar from './components/Sidebar'
import ResultsPanel from './components/ResultsPanel'
import ChatContainer from './components/ChatContainer'

function App() {
  return (
    <div className="h-screen w-screen flex flex-col lg:flex-row overflow-hidden bg-base-100 text-base-content">
      <Sidebar />
      <ResultsPanel />
      <ChatContainer />
      <Toaster position="top-center" toastOptions={{ duration: 3000 }} />
    </div>
  )
}

export default App
