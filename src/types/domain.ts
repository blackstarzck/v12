export type Locale = 'KO' | 'VI' | 'EN';

export type TopikLevel = 'TOPIK I' | 'TOPIK II';

export type PracticeArea = 'reading' | 'listening';

export type ProblemType = 'grammar' | 'main-idea' | 'detail' | 'audio';

export type WritingType = '51' | '52' | '53' | '54';

export type FeedbackStatus = 'Feedback ready' | 'Draft' | 'Needs review';

export interface SkillScore {
  name: string;
  score: number;
  prediction: string;
  status: 'strong' | 'steady' | 'weak';
}

export interface PracticeQuestion {
  id: number;
  title: string;
  passage: string;
  question: string;
  options: string[];
  answer: string;
  explanation: string;
}

export interface FeedbackRecord {
  id: string;
  title: string;
  type: `Writing ${WritingType}`;
  score: number;
  total: number;
  status: FeedbackStatus;
  date: string;
  words: number;
  summary: string;
}

export interface VocabularyItem {
  id: string;
  word: string;
  meaning: string;
  example: string;
  level: TopikLevel;
  status: 'Review' | 'Memorized';
}

export interface NoticeItem {
  id: string;
  category: string;
  title: string;
  author: string;
  date: string;
  views: number;
}
