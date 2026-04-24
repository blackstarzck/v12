import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/app/AppShell';
import { BoardPage } from './pages/BoardPage';
import { HomePage } from './pages/HomePage';
import { LibraryPage } from './pages/LibraryPage';
import { MockExamPage } from './pages/MockExamPage';
import { PracticeCreatePage } from './pages/PracticeCreatePage';
import { PracticeSolvePage } from './pages/PracticeSolvePage';
import { ProfileSettingsPage } from './pages/ProfileSettingsPage';
import { VocabularyPage } from './pages/VocabularyPage';
import { WritingFeedbackDetailPage } from './pages/WritingFeedbackDetailPage';
import { WritingFeedbackListPage } from './pages/WritingFeedbackListPage';
import { WritingPracticePage } from './pages/WritingPracticePage';
import { WritingSetupPage } from './pages/WritingSetupPage';

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/home-v2" element={<HomePage variant="writing" />} />
        <Route path="/practice/create" element={<PracticeCreatePage />} />
        <Route path="/practice/solve" element={<PracticeSolvePage />} />
        <Route path="/writing/setup" element={<WritingSetupPage />} />
        <Route path="/writing/51" element={<WritingPracticePage type="51" />} />
        <Route path="/writing/52" element={<WritingPracticePage type="52" />} />
        <Route path="/writing/53" element={<WritingPracticePage type="53" />} />
        <Route path="/writing/54" element={<WritingPracticePage type="54" />} />
        <Route path="/writing/feedback" element={<WritingFeedbackListPage />} />
        <Route path="/writing/feedback/:id" element={<WritingFeedbackDetailPage />} />
        <Route path="/mock/results" element={<MockExamPage />} />
        <Route path="/mock/exam" element={<MockExamPage mode="exam" />} />
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/vocabulary" element={<VocabularyPage />} />
        <Route path="/board" element={<BoardPage />} />
        <Route path="/profile" element={<ProfileSettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
