import { CalendarDays, Flag, Timer } from 'lucide-react'
import type { Challenge } from '../services/challenges'

interface ChallengeCardProps {
  challenge: Challenge
}

const dateFormatter = new Intl.DateTimeFormat('en', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
})

function getTiming(challenge: Challenge) {
  const now = Date.now()
  const start = new Date(challenge.starts_at).getTime()
  const end = new Date(challenge.ends_at).getTime()

  if (challenge.status === 'cancelled') return 'Cancelled'
  if (now < start) return 'Upcoming'
  if (now > end) return 'Finished'
  return 'In progress'
}

export function ChallengeCard({ challenge }: ChallengeCardProps) {
  const timing = getTiming(challenge)

  return (
    <article className="challenge-card">
      <div className="challenge-card__topline">
        <span className={`status status--${challenge.status}`}>
          {challenge.status}
        </span>
        <span className="timing">
          <Timer size={15} aria-hidden="true" />
          {timing}
        </span>
      </div>

      <div>
        <h2>{challenge.name}</h2>
        <p>{challenge.description ?? 'A shared distance challenge for Tibet.'}</p>
      </div>

      <dl className="challenge-dates">
        <div>
          <dt>
            <CalendarDays size={16} aria-hidden="true" /> Starts
          </dt>
          <dd>{dateFormatter.format(new Date(challenge.starts_at))}</dd>
        </div>
        <div>
          <dt>
            <Flag size={16} aria-hidden="true" /> Ends
          </dt>
          <dd>{dateFormatter.format(new Date(challenge.ends_at))}</dd>
        </div>
      </dl>

      <div className="distance-options" aria-label="Available distance targets">
        <span>50 km</span>
        <span>100 km</span>
      </div>
    </article>
  )
}
