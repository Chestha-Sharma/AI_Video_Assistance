import React, { useRef, useState } from 'react'
import { Link2, Upload, Languages, Loader2, Film } from 'lucide-react'
import { useAppStore } from '../store/useAppStore'

const Sidebar = () => {
  const [mode, setMode] = useState('url') // 'url' | 'file'
  const [url, setUrl] = useState('')
  const [file, setFile] = useState(null)
  const [translate, setTranslate] = useState(false)
  const fileInputRef = useRef(null)

  const { processSource, isProcessing, session, clearSession } = useAppStore()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (mode === 'url' && !url.trim()) return
    if (mode === 'file' && !file) return

    try {
      if (mode === 'url') {
        await processSource({ source: url.trim(), translate })
      } else {
        await processSource({ file, translate })
      }
    } catch {
      // toast handled in store
    }
  }

  return (
    <aside className="w-full lg:w-80 shrink-0 border-r border-base-300 flex flex-col bg-base-200/40">
      <div className="p-5 border-b border-base-300">
        <div className="flex items-center gap-2">
          <div className="size-9 rounded-xl bg-primary/15 flex items-center justify-center">
            <Film size={18} className="text-primary" />
          </div>
          <div>
            <h1 className="font-display font-semibold text-lg leading-tight">AI Video Assistance</h1>
            <p className="text-xs opacity-60">Transcribe · Summarize · Ask</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="p-5 space-y-4">
        <div className="tabs tabs-boxed bg-base-300/50 p-1">
          <a
            className={`tab flex-1 gap-1 ${mode === 'url' ? 'tab-active' : ''}`}
            onClick={() => setMode('url')}
          >
            <Link2 size={14} /> URL
          </a>
          <a
            className={`tab flex-1 gap-1 ${mode === 'file' ? 'tab-active' : ''}`}
            onClick={() => setMode('file')}
          >
            <Upload size={14} /> File
          </a>
        </div>

        {mode === 'url' ? (
          <div className="form-control">
            <label className="label py-1">
              <span className="label-text text-xs opacity-70">YouTube URL</span>
            </label>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://youtube.com/watch?v=..."
              className="input input-bordered input-sm w-full"
            />
          </div>
        ) : (
          <div className="form-control">
            <label className="label py-1">
              <span className="label-text text-xs opacity-70">Local video / audio file</span>
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*,video/*"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="file-input file-input-bordered file-input-sm w-full"
            />
            {file && <span className="text-xs opacity-60 mt-1 truncate">{file.name}</span>}
          </div>
        )}

        <label className="label cursor-pointer justify-start gap-2 py-1">
          <input
            type="checkbox"
            checked={translate}
            onChange={(e) => setTranslate(e.target.checked)}
            className="checkbox checkbox-primary checkbox-sm"
          />
          <span className="label-text text-sm flex items-center gap-1">
            <Languages size={14} /> Translate to English
          </span>
        </label>

        <button
          type="submit"
          disabled={isProcessing || (mode === 'url' ? !url.trim() : !file)}
          className="btn btn-primary btn-sm w-full"
        >
          {isProcessing ? (
            <>
              <Loader2 size={16} className="animate-spin" /> Processing...
            </>
          ) : (
            'Process video'
          )}
        </button>

        {session && (
          <button
            type="button"
            onClick={clearSession}
            className="btn btn-ghost btn-xs w-full opacity-60"
          >
            Clear & start over
          </button>
        )}
      </form>

      {session && (
        <div className="p-5 mt-auto border-t border-base-300 text-xs opacity-50">
          Session: <span className="font-mono">{session.session_id.slice(0, 8)}</span>
        </div>
      )}
    </aside>
  )
}

export default Sidebar
