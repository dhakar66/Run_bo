import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { ChallengesPage } from './pages/ChallengesPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="*" element={<ChallengesPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
