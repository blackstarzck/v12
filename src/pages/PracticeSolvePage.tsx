import {
  Alert,
  Button,
  Card,
  Empty,
  Progress,
  Radio,
  Space,
  Tag,
  Tooltip,
  Typography,
} from 'antd';
import {
  CheckCircleOutlined,
  LeftOutlined,
  RightOutlined,
  StarOutlined,
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { usePracticeStore } from '../stores/usePracticeStore';
import { PageHeader } from '../components/shared/PageHeader';

export function PracticeSolvePage() {
  const {
    questions,
    currentIndex,
    selectedAnswers,
    checkedAnswers,
    selectAnswer,
    checkAnswer,
    goToQuestion,
  } = usePracticeStore();
  const question = questions[currentIndex];

  if (!question) {
    return (
      <>
        <PageHeader title="문제 풀이" description="생성된 문제가 없습니다." />
        <Empty
          description="먼저 AI 맞춤 문제를 생성해 주세요."
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <Button type="primary">
            <Link to="/practice/create">문제 생성으로 이동</Link>
          </Button>
        </Empty>
      </>
    );
  }

  const selected = selectedAnswers[question.id];
  const checked = checkedAnswers[question.id];
  const isCorrect = selected === question.answer;

  return (
    <>
      <PageHeader
        title="문제 풀이"
        description="지문을 읽고 답을 선택한 뒤 정답과 해설을 확인합니다."
        extra={<Tag color="processing">{currentIndex + 1} / {questions.length}</Tag>}
      />
      <div className="solve-grid">
        <Card>
          <Space direction="vertical" size={20} style={{ width: '100%' }}>
            <Progress percent={Math.round(((currentIndex + 1) / questions.length) * 100)} />
            <Typography.Title level={3}>{question.title}</Typography.Title>
            <Alert type="info" message="지문" description={question.passage} />
            <Typography.Title level={4}>{question.question}</Typography.Title>
            <Radio.Group
              value={selected}
              onChange={(event) => selectAnswer(question.id, event.target.value)}
              style={{ width: '100%' }}
            >
              {question.options.map((option) => (
                <Radio key={option} value={option} className="answer-option">
                  {option}
                </Radio>
              ))}
            </Radio.Group>
            {checked && (
              <Alert
                showIcon
                type={isCorrect ? 'success' : 'error'}
                message={isCorrect ? '정답입니다' : '다시 확인이 필요합니다'}
                description={question.explanation}
              />
            )}
          </Space>
        </Card>
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Card title="풀이 조작">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button
                type="primary"
                icon={<CheckCircleOutlined />}
                disabled={!selected}
                onClick={() => checkAnswer(question.id)}
              >
                정답 확인
              </Button>
              <Space>
                <Button
                  icon={<LeftOutlined />}
                  disabled={currentIndex === 0}
                  onClick={() => goToQuestion(currentIndex - 1)}
                >
                  이전
                </Button>
                <Button
                  icon={<RightOutlined />}
                  disabled={currentIndex === questions.length - 1}
                  onClick={() => goToQuestion(currentIndex + 1)}
                >
                  다음
                </Button>
              </Space>
              <Tooltip title="북마크에 저장">
                <Button aria-label="현재 문제 북마크" icon={<StarOutlined />}>
                  북마크
                </Button>
              </Tooltip>
            </Space>
          </Card>
          <Card title="다음 학습">
            <Typography.Paragraph type="secondary">
              오답이면 해설을 읽고 같은 유형 문제를 한 번 더 생성해 보세요.
            </Typography.Paragraph>
            <Button block>
              <Link to="/practice/create">비슷한 문제 만들기</Link>
            </Button>
          </Card>
        </Space>
      </div>
    </>
  );
}
