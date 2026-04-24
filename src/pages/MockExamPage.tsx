import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Drawer,
  Flex,
  Grid,
  Modal,
  Progress,
  Radio,
  Row,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
} from 'antd';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '../components/shared/PageHeader';

interface MockExamPageProps {
  mode?: 'results' | 'exam';
}

const examHistory = [
  { id: 'e-1', date: '2026-04-18', type: 'TOPIK II 실전', score: 181, total: 300, duration: '96분' },
  { id: 'e-2', date: '2026-04-06', type: '쓰기 집중', score: 62, total: 100, duration: '42분' },
  { id: 'e-3', date: '2026-03-29', type: 'TOPIK II 실전', score: 166, total: 300, duration: '102분' },
];

function OmrContent({ answers, setAnswers }: { answers: Record<number, string>; setAnswers: (next: Record<number, string>) => void }) {
  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      {Array.from({ length: 10 }, (_, index) => index + 1).map((number) => (
        <Flex key={number} align="center" justify="space-between">
          <Typography.Text>{number}번</Typography.Text>
          <Radio.Group
            size="small"
            value={answers[number]}
            onChange={(event) => setAnswers({ ...answers, [number]: event.target.value })}
          >
            {['1', '2', '3', '4'].map((option) => (
              <Radio.Button key={option} value={option}>
                {option}
              </Radio.Button>
            ))}
          </Radio.Group>
        </Flex>
      ))}
    </Space>
  );
}

export function MockExamPage({ mode = 'results' }: MockExamPageProps) {
  const navigate = useNavigate();
  const screens = Grid.useBreakpoint();
  const [answers, setAnswers] = useState<Record<number, string>>({ 1: '2' });
  const [omrOpen, setOmrOpen] = useState(false);
  const [endOpen, setEndOpen] = useState(false);

  if (mode === 'exam') {
    const answered = Object.keys(answers).length;

    return (
      <>
        <PageHeader
          title="실전 모의고사 풀이"
          description="타이머, 문제, OMR 답안지를 확인하며 실제 시험처럼 풀이합니다."
          extra={
            <>
              <Button onClick={() => setOmrOpen(true)}>답안지 OMR</Button>
              <Button danger onClick={() => setEndOpen(true)}>
                시험 종료
              </Button>
            </>
          }
        />
        <Row gutter={[16, 16]} align="top">
          <Col xs={24} lg={16}>
            <Card>
              <Space direction="vertical" size={18} style={{ width: '100%' }}>
                <Alert
                  type="warning"
                  showIcon
                  message="남은 시간 42:18"
                  description="듣기 영역 6번 문제를 풀고 있습니다. 오디오 재생 후 답을 선택하세요."
                />
                <Progress percent={36} />
                <Typography.Title level={3}>6번. 여자가 이어서 할 행동을 고르십시오.</Typography.Title>
                <Alert
                  type="info"
                  message="오디오 재생 영역"
                  description={<Progress percent={58} size="small" />}
                />
                <Radio.Group value={answers[6]} onChange={(event) => setAnswers({ ...answers, 6: event.target.value })}>
                  <Space direction="vertical" size={10}>
                    {[
                      '자료를 다시 인쇄한다.',
                      '회의 장소를 확인한다.',
                      '발표 순서를 바꾼다.',
                      '담당자에게 전화를 건다.',
                    ].map((option, index) => (
                      <Radio key={option} value={String(index + 1)}>
                        {option}
                      </Radio>
                    ))}
                  </Space>
                </Radio.Group>
                <Space>
                  <Button>이전 문제</Button>
                  <Button type="primary">다음 문제</Button>
                </Space>
              </Space>
            </Card>
          </Col>
          {screens.lg && (
            <Col xs={24} lg={8}>
              <Card title={`OMR 답안지 · ${answered}/10문항`}>
                <OmrContent answers={answers} setAnswers={setAnswers} />
              </Card>
            </Col>
          )}
        </Row>
        {!screens.lg && (
          <Drawer
            title={`OMR 답안지 · ${answered}/10문항`}
            placement="bottom"
            open={omrOpen}
            onClose={() => setOmrOpen(false)}
            height="75dvh"
          >
            <OmrContent answers={answers} setAnswers={setAnswers} />
          </Drawer>
        )}
        <Modal
          title="시험을 종료할까요?"
          open={endOpen}
          okText="종료하고 결과 보기"
          cancelText="계속 풀기"
          onCancel={() => setEndOpen(false)}
          onOk={() => navigate('/mock/results')}
        >
          종료하면 현재 OMR 답안 상태로 채점 결과 화면으로 이동합니다.
        </Modal>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="모의고사 결과"
        description="최근 성적과 영역별 점수를 비교하고 새 모의고사를 시작합니다."
        extra={
          <Button type="primary" onClick={() => navigate('/mock/exam')}>
            새 모의고사 응시
          </Button>
        }
      />
      <Space direction="vertical" size={16} style={{ width: '100%' }}>
        <Row gutter={[12, 12]}>
          <Col xs={24} md={8}>
            <Card>
              <Statistic title="최근 등급" value="5급 예상" />
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card>
              <Statistic title="평균 점수" value={176} suffix="/ 300" />
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card>
              <Statistic title="응시 횟수" value={8} suffix="회" />
            </Card>
          </Col>
        </Row>
        <Card title="영역별 점수">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Descriptions column={{ xs: 1, md: 3 }}>
              <Descriptions.Item label="듣기">76/100</Descriptions.Item>
              <Descriptions.Item label="읽기">69/100</Descriptions.Item>
              <Descriptions.Item label="쓰기">36/100</Descriptions.Item>
            </Descriptions>
            <Alert
              type="info"
              showIcon
              message="쓰기 점수가 등급 상승의 핵심입니다"
              description="다음 시험 전까지 53번 전개 단락 연습을 3회 완료하는 것을 추천합니다."
            />
          </Space>
        </Card>
        <Card title="응시 기록">
          <Table
            rowKey="id"
            dataSource={examHistory}
            columns={[
              { title: '응시일', dataIndex: 'date' },
              { title: '시험', dataIndex: 'type' },
              {
                title: '점수',
                render: (_, record) => `${record.score}/${record.total}`,
              },
              { title: '소요 시간', dataIndex: 'duration' },
              {
                title: '상태',
                render: () => <Tag color="success">성적표 준비</Tag>,
              },
            ]}
            scroll={{ x: 720 }}
          />
        </Card>
      </Space>
    </>
  );
}
