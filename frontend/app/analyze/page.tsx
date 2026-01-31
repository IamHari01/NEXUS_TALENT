'use client'
import { useState } from 'react'
import { analyzeProfile } from '@/lib/api'


export default function Analyze() {
    const [resume, setResume] = useState('')
    const [result, setResult] = useState(null)


    const run = async () => {
        const res = await analyzeProfile(resume)
        setResult(res)
    }


    return (
        <div className="p-6">
            <textarea onChange={e => setResume(e.target.value)} />
            <button onClick={run}>Analyze</button>
            {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
        </div>
    )
}