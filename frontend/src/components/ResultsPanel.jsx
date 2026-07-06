import React, { useState } from 'react'
import { ClipboardList, CheckSquare, HelpCircle, FileText, ScrollText, Sparkles } from 'lucide-react'
import ResultsSkeleton from './Skeleton/ResultsSkeleton'
import { useAppStore } from '../store/useAppStore'

const TABS = [
  { key: 'summary', label: 'Summary', icon: FileText },
  { key: 'action_items', label: 'Action items', icon: CheckSquare },
  { key: 'key_decisions', label: 'Decisions', icon: ClipboardList },
  { key: 'questions', label: 'Open questions', icon: HelpCircle },
  { key: 'transcript', label: 'Transcript', icon: ScrollText },
]

const renderContent = (value) => {
  if (!value) return <p className="opacity-50 text-sm">Nothing here yet.</p>

  if (Array.isArray(value)) {
    return (
      <ul className="space-y-2">
        {value.map((item, i) => (
          <li key={i} className="flex gap-2 text-sm leading-relaxed">
            <span className="text-primary mt-0.5">›</span>
            <span>{typeof item === 'string' ? item : JSON.stringify(item)}</span>
          </li>
        ))}
      </ul>
    )
  }

  return <p className="text-sm leading-relaxed whitespace-pre-wrap">{value}</p>
}

const ResultsPanel = () => {
  const { session, isProcessing } = useAppStore()
  const [activeTab, setActiveTab] = useState('summary')

  if (isProcessing) return <ResultsSkeleton />

  if (!session) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center p-10 opacity-60">
        <Sparkles size={32} className="text-primary" />
        <p className="max-w-sm text-sm">
          Paste a YouTube URL or upload a video/audio file on the left to generate a
          summary, action items, key decisions, and open questions — then chat with it.
        </p>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="px-6 pt-5 pb-3 border-b border-base-300">
        <p className="text-xs uppercase tracking-wide opacity-50 mb-1">Meeting / video</p>
        <h2 className="font-display font-semibold text-xl">{session.title}</h2>
      </div>

      <div className="tabs tabs-bordered px-6 pt-3 shrink-0 overflow-x-auto flex-nowrap">
        {TABS.map(({ key, label, icon: Icon }) => (
          <a
            key={key}
            className={`tab gap-1.5 whitespace-nowrap ${activeTab === key ? 'tab-active font-medium' : ''}`}
            onClick={() => setActiveTab(key)}
          >
            <Icon size={14} /> {label}
          </a>
        ))}
      </div>

      <div className="flex-1 overflow-auto p-6">
        {renderContent(session[activeTab])}
      </div>
    </div>
  )
}

export default ResultsPanel
