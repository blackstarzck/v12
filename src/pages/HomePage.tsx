import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Flex,
  List,
  Progress,
  Row,
  Space,
  Statistic,
  Tag,
  Typography,
} from 'antd';
import { useNavigate } from 'react-router-dom';
import { feedbackRecords } from '../data/mockData';
import { PageHeader } from '../components/shared/PageHeader';
import { useLearningStore } from '../stores/useLearningStore';
import { useUserStore } from '../stores/useUserStore';

interface HomePageProps {
  variant?: 'main' | 'writing';
}

export function HomePage({ variant = 'main' }: HomePageProps) {
  const navigate = useNavigate();
  const { targetGrade, examDate } = useUserStore();
  const { weeklyHours, solvedQuestions, attendanceDays, xp, skillScores } =
    useLearningStore();
  const daysLeft = Math.max(
    0,
    Math.ceil((new Date(examDate).getTime() - Date.now()) / 86_400_000),
  );
  const latestFeedback = feedbackRecords.filter((record) => record.status !== 'Draft');

  return (
    <>
      <PageHeader
        title={variant === 'writing' ? '쓰기 집중 홈' : '오늘의 학습 대시보드'}
        description="현재 학습 상태, 약점, 이어서 할 일을 한 화면에서 확인합니다."
        extra={
          variant === 'writing' ? (
            <Button onClick={() => navigate('/')}>전체 대시보드로 돌아가기</Button>
          ) : (
            <Button onClick={() => navigate('/home-v2')}>쓰기 집중 홈 보기</Button>
          )
        }
      />

      <Row gutter={[16, 16]} align="top">
        <Col xs={24} xl={15}>
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <Card>
              <Space direction="vertical" size={20} style={{ width: '100%' }}>
                <Alert
                  showIcon
                  type="info"
                  message={`${targetGrade} 목표까지 ${daysLeft}일 남았습니다`}
                  description="오늘은 쓰기 53번 구조 연습과 읽기 세부 정보 문제를 이어서 풀면 목표 진도에 도달합니다."
                />
                <Row gutter={[12, 12]}>
                  <Col xs={24} md={8}>
                    <Statistic title="주간 학습 시간" value={weeklyHours} suffix="시간" />
                  </Col>
                  <Col xs={24} md={8}>
                    <Statistic title="푼 문제" value={solvedQuestions} suffix="문제" />
                  </Col>
                  <Col xs={24} md={8}>
                    <Statistic title="출석" value={attendanceDays} suffix="일" />
                  </Col>
                </Row>
                <div>
                  <Typography.Text strong>목표 경험치</Typography.Text>
                  <Progress percent={Math.round((xp / 1800) * 100)} status="active" />
                </div>
              </Space>
            </Card>

            <Row gutter={[12, 12]}>
              <Col xs={24} md={12}>
                <Card>
                  <Typography.Title level={4}>듣기/읽기 집중</Typography.Title>
                  <Typography.Paragraph type="secondary">
                    원하는 유형을 선택해 AI 문제를 생성하고 바로 풀이합니다.
                  </Typography.Paragraph>
                  <Button type="primary" block onClick={() => navigate('/practice/create')}>
                    AI 문제 생성 시작하기
                  </Button>
                </Card>
              </Col>
              <Col xs={24} md={12}>
                <Card>
                  <Typography.Title level={4}>쓰기 집중 연습</Typography.Title>
                  <Typography.Paragraph type="secondary">
                    51번부터 54번까지 유형과 주제를 고르고 답안을 작성합니다.
                  </Typography.Paragraph>
                  <Button type="primary" block onClick={() => navigate('/writing/setup')}>
                    쓰기 문제 생성하기
                  </Button>
                </Card>
              </Col>
              <Col xs={24} md={12}>
                <Card>
                  <Typography.Title level={4}>이어하기</Typography.Title>
                  <Typography.Paragraph type="secondary">
                    자동 저장된 51번 답안을 이어서 작성합니다.
                  </Typography.Paragraph>
                  <Button block onClick={() => navigate('/writing/51')}>
                    51번 답안 이어쓰기
                  </Button>
                </Card>
              </Col>
              <Col xs={24} md={12}>
                <Card>
                  <Typography.Title level={4}>WEAK POINT</Typography.Title>
                  <Typography.Paragraph type="secondary">
                    쓰기 53번 수치 비교와 마무리 문장을 집중 보완합니다.
                  </Typography.Paragraph>
                  <Button block onClick={() => navigate('/writing/53')}>
                    약점 공략 시작
                  </Button>
                </Card>
              </Col>
            </Row>
          </Space>
        </Col>

        <Col xs={24} xl={9}>
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <Card title="영역별 합격 예측">
              <Space direction="vertical" style={{ width: '100%' }}>
                {skillScores.map((skill) => (
                  <div key={skill.name}>
                    <Flex align="center" justify="space-between">
                      <Typography.Text strong>{skill.name}</Typography.Text>
                      <Tag
                        color={
                          skill.status === 'strong'
                            ? 'success'
                            : skill.status === 'weak'
                              ? 'warning'
                              : 'processing'
                        }
                      >
                        {skill.prediction}
                      </Tag>
                    </Flex>
                    <Progress percent={skill.score} size="small" />
                  </div>
                ))}
              </Space>
            </Card>

            <Card
              title="최근 쓰기 피드백"
              extra={
                <Button type="link" onClick={() => navigate('/writing/feedback')}>
                  전체 보기
                </Button>
              }
            >
              {latestFeedback.length === 0 ? (
                <Empty description="아직 완료된 피드백이 없습니다" />
              ) : (
                <List
                  dataSource={latestFeedback}
                  renderItem={(record) => (
                    <List.Item
                      actions={[
                        <Button
                          key="detail"
                          type="link"
                          onClick={() => navigate(`/writing/feedback/${record.id}`)}
                        >
                          상세
                        </Button>,
                      ]}
                    >
                      <List.Item.Meta
                        title={record.title}
                        description={`${record.type} · ${record.score}/${record.total}점 · ${record.date}`}
                      />
                    </List.Item>
                  )}
                />
              )}
            </Card>

            <Card title="소식">
              <List
                dataSource={[
                  '53번 도표 쓰기 신규 평가 기준이 추가됐습니다.',
                  '이번 주 모의고사 응시자는 평균 12점 상승했습니다.',
                ]}
                renderItem={(item) => <List.Item>{item}</List.Item>}
              />
            </Card>
          </Space>
        </Col>
      </Row>
    </>
  );
}
