import { useCallback, useEffect, useState } from 'react'
import { Activity, ArrowRight, Mountain, RefreshCw } from 'lucide-react'
import { ChallengeCard } from '../components/ChallengeCard'
import { getChallenges, type Challenge } from '../services/challenges'

type RequestState = 'loading' | 'success' | 'error'

export function ChallengesPage() {
  const [challenges, setChallenges] = useState<Challenge[]>([])
  const [requestState, setRequestState] = useState<RequestState>('loading')
  const [requestVersion, setRequestVersion] = useState(0)

  const retry = useCallback(() => {
    setRequestState('loading')
    setRequestVersion((version) => version + 1)
  }, [])

  useEffect(() => {
    const controller = new AbortController()

    getChallenges(controller.signal)
      .then((data) => {
        setChallenges(data)
        setRequestState('success')
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        setRequestState('error')
      })

    return () => controller.abort()
  }, [requestVersion])

  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href="/" aria-label="Run for Tibet home">
          <span className="brand__mark">
            <Mountain size={20} strokeWidth={2} aria-hidden="true" />
          </span>
          <span>Run for Tibet</span>
        </a>
        <a className="docs-link" href="http://localhost:8000/docs">
          API docs <ArrowRight size={16} aria-hidden="true" />
        </a>
      </header>

      <main>
        <section className="hero" aria-labelledby="hero-title">
          <img
            className="hero__image"
            src="/tibet-panorama.jpg"
            alt="Snow-covered mountains rising above the Tibetan plateau"
          />
          <div className="hero__overlay" />
          <div className="hero__content">
            <p className="eyebrow">Virtual distance challenge</p>
            <h1 id="hero-title">Run for Tibet</h1>
            <p className="hero__lede">
              Choose your distance. Run on your own days. Carry every kilometre
              toward one shared finish line.
            </p>
          </div>
          <div className="hero__distances" aria-label="Challenge distances">
            <div><strong>50</strong><span>kilometres</span></div>
            <div><strong>100</strong><span>kilometres</span></div>
          </div>
          <a
            className="photo-credit"
            href="https://commons.wikimedia.org/wiki/File:Tibet_Panorama.jpg"
            target="_blank"
            rel="noreferrer"
          >
            Photo: Wikimedia Commons
          </a>
        </section>

        <section className="challenge-section" aria-labelledby="challenge-heading">
          <div className="section-heading">
            <div>
              <p className="eyebrow eyebrow--dark">Challenge calendar</p>
              <h2 id="challenge-heading">Find your next finish line</h2>
            </div>
            {requestState === 'success' && challenges.length > 0 && (
              <span className="challenge-count">
                {challenges.length} {challenges.length === 1 ? 'challenge' : 'challenges'}
              </span>
            )}
          </div>

          {requestState === 'loading' && (
            <div className="state-panel" role="status">
              <span className="spinner" aria-hidden="true" />
              <p>Loading challenges...</p>
            </div>
          )}

          {requestState === 'error' && (
            <div className="state-panel state-panel--error" role="alert">
              <Activity size={28} aria-hidden="true" />
              <h3>Challenges are out of reach</h3>
              <p>The API did not respond. Check the backend and try again.</p>
              <button type="button" onClick={retry}>
                <RefreshCw size={16} aria-hidden="true" /> Retry
              </button>
            </div>
          )}

          {requestState === 'success' && challenges.length === 0 && (
            <div className="state-panel">
              <Mountain size={30} aria-hidden="true" />
              <h3>The trail opens soon</h3>
              <p>No challenges have been published yet.</p>
            </div>
          )}

          {requestState === 'success' && challenges.length > 0 && (
            <div className="challenge-grid">
              {challenges.map((challenge) => (
                <ChallengeCard key={challenge.id} challenge={challenge} />
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
