import type {
  FeedbackRecord,
  NoticeItem,
  PracticeQuestion,
  SkillScore,
  VocabularyItem,
} from '../types/domain';

export const skillScores: SkillScore[] = [
  { name: '듣기', score: 78, prediction: '합격권 안정', status: 'strong' },
  { name: '읽기', score: 71, prediction: '세부 독해 보완', status: 'steady' },
  { name: '쓰기', score: 54, prediction: '53번 구조 연습 필요', status: 'weak' },
];

export const practiceQuestions: PracticeQuestion[] = [
  {
    id: 1,
    title: '읽기 34번 중심 내용 파악',
    passage:
      '최근 한국의 공공도서관은 책을 빌리는 공간을 넘어 지역 주민이 함께 배우고 교류하는 생활 문화 공간으로 변화하고 있다.',
    question: '이 글의 중심 내용으로 알맞은 것을 고르십시오.',
    options: [
      '공공도서관의 대출 규정이 엄격해지고 있다.',
      '공공도서관의 역할이 지역 문화 공간으로 넓어지고 있다.',
      '지역 주민은 도서관보다 온라인 강의를 선호한다.',
      '생활 문화 시설은 도서관과 분리되어야 한다.',
    ],
    answer: '공공도서관의 역할이 지역 문화 공간으로 넓어지고 있다.',
    explanation:
      '본문은 도서관이 책 대출 공간에서 학습과 교류 공간으로 변화하고 있다는 흐름을 설명합니다.',
  },
  {
    id: 2,
    title: '읽기 38번 세부 정보 확인',
    passage:
      '이번 한국어 말하기 대회는 예선 영상 심사 후 본선을 진행하며, 본선 참가자는 발표 자료를 행사 3일 전까지 제출해야 한다.',
    question: '본문과 같은 내용을 고르십시오.',
    options: [
      '본선 참가자는 발표 자료를 미리 제출해야 한다.',
      '대회 예선은 현장 발표로만 진행된다.',
      '발표 자료는 행사 당일 제출한다.',
      '영상 심사는 본선 이후에 진행된다.',
    ],
    answer: '본선 참가자는 발표 자료를 미리 제출해야 한다.',
    explanation:
      '행사 3일 전까지 제출해야 한다고 했으므로 본선 참가자는 자료를 미리 준비해야 합니다.',
  },
];

export const feedbackRecords: FeedbackRecord[] = [
  {
    id: 'fb-53-1',
    title: '환경 보호 실천 방법에 대한 그래프 설명',
    type: 'Writing 53',
    score: 63,
    total: 80,
    status: 'Feedback ready',
    date: '2026-04-21',
    words: 312,
    summary:
      '도입과 결론은 명확하지만 수치 비교 표현이 반복되어 전개 부분의 연결어를 보완하면 좋습니다.',
  },
  {
    id: 'fb-51-1',
    title: '동아리 모집 안내문 빈칸 쓰기',
    type: 'Writing 51',
    score: 28,
    total: 40,
    status: 'Needs review',
    date: '2026-04-19',
    words: 96,
    summary:
      '상황에 맞는 높임 표현은 좋지만 ㉡ 문장 끝맺음이 안내문 형식과 조금 어긋납니다.',
  },
  {
    id: 'draft-53-2',
    title: '청소년 독서 시간 변화',
    type: 'Writing 53',
    score: 0,
    total: 80,
    status: 'Draft',
    date: '2026-04-22',
    words: 184,
    summary: '자동 저장된 답안입니다. 전개 단락부터 이어서 작성할 수 있습니다.',
  },
];

export const vocabularyItems: VocabularyItem[] = [
  {
    id: 'v-1',
    word: '증가하다',
    meaning: '수나 양이 늘어나다',
    example: '온라인 수업 참여자가 꾸준히 증가하고 있다.',
    level: 'TOPIK II',
    status: 'Review',
  },
  {
    id: 'v-2',
    word: '반면에',
    meaning: '앞 내용과 대조되는 내용을 연결할 때 쓰는 표현',
    example: '도시 지역은 이용률이 높았다. 반면에 농촌 지역은 낮았다.',
    level: 'TOPIK II',
    status: 'Review',
  },
  {
    id: 'v-3',
    word: '참여',
    meaning: '어떤 일에 함께함',
    example: '학생들의 참여가 수업 분위기를 바꾸었다.',
    level: 'TOPIK I',
    status: 'Memorized',
  },
];

export const noticeItems: NoticeItem[] = [
  {
    id: 'n-1',
    category: '중요',
    title: 'TOPIK II 쓰기 집중반 신규 문제 유형 업데이트',
    author: 'TALKPIK 운영팀',
    date: '2026-04-22',
    views: 1284,
  },
  {
    id: 'n-2',
    category: '학습',
    title: '53번 도표 쓰기에서 자주 쓰는 비교 표현 안내',
    author: '콘텐츠팀',
    date: '2026-04-20',
    views: 842,
  },
  {
    id: 'n-3',
    category: '점검',
    title: 'AI 피드백 생성 속도 개선 작업 안내',
    author: '서비스 운영팀',
    date: '2026-04-18',
    views: 603,
  },
];

export const writingGuides = {
  '51': {
    title: '실용문 빈칸 쓰기',
    prompt:
      '다음은 한국어 동아리 모집 안내문입니다. ㉠과 ㉡에 들어갈 말을 상황에 맞게 쓰십시오.',
    tabs: ['㉠ 목적 설명', '㉡ 참여 안내'],
    sample:
      '㉠ 한국어 말하기 실력을 키우고 싶은 학생들을 위해\n㉡ 관심 있는 학생은 학생회관 2층으로 신청해 주시기 바랍니다.',
  },
  '52': {
    title: '설명문 연결 쓰기',
    prompt:
      '다음 글의 흐름에 맞게 빈칸에 들어갈 문장을 쓰십시오.',
    tabs: ['앞 문장 연결', '뒤 문장 연결'],
    sample: '이러한 이유로 공공시설 이용 교육이 함께 이루어져야 한다.',
  },
  '53': {
    title: '도표/그래프 설명 쓰기',
    prompt:
      '다음 그래프는 한국어 학습자의 복습 방법 변화를 나타낸 것입니다. 내용을 200~300자로 쓰십시오.',
    tabs: ['도입', '전개', '마무리'],
    sample:
      '이 그래프는 한국어 학습자들이 사용하는 복습 방법의 변화를 보여 준다. 2024년에는 교재 복습이 가장 높았으나 2026년에는 AI 피드백 활용 비율이 크게 증가했다. 이를 통해 학습자들이 개인화된 복습 방법을 더 선호하게 되었음을 알 수 있다.',
  },
  '54': {
    title: '의견문 쓰기',
    prompt:
      '온라인 한국어 수업의 장점과 한계에 대해 자신의 생각을 쓰십시오.',
    tabs: ['주장', '근거', '마무리'],
    sample:
      '온라인 수업은 시간과 장소의 제약을 줄여 주지만, 말하기 상호작용을 보완할 장치가 함께 필요하다.',
  },
} as const;
