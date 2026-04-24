import {
  Alert,
  Button,
  Card,
  Collapse,
  Descriptions,
  Progress,
  Result,
  Space,
  Statistic,
  Tabs,
  Tag,
  Typography,
} from 'antd';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { PageHeader } from '../components/shared/PageHeader';
import { feedbackRecords } from '../data/mockData';

export function WritingFeedbackDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const record = feedbackRecords.find((item) => item.id === id);

  if (!record) {
    return (
      <Result
        status="404"
        title="피드백을 찾을 수 없습니다"
        subTitle="목록으로 돌아가 다른 답안을 선택해 주세요."
        extra={
          <Button type="primary">
            <Link to="/writing/feedback">보관함으로 이동</Link>
          </Button>
        }
      />
    );
  }

  return (
    <>
      <PageHeader
        title={record.title}
        description="AI 총평, 단계별 분석, 다시 연습할 행동을 확인합니다."
        extra={
          <>
            <Button onClick={() => navigate('/writing/feedback')}>목록으로</Button>
            <Button type="primary" onClick={() => navigate(record.type.includes('53') ? '/writing/53' : '/writing/51')}>
              다시 풀기
            </Button>
          </>
        }
      />
      <div className="detail-grid">
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Card>
            <Space wrap size={24}>
              <Statistic title="점수" value={record.score} suffix={`/ ${record.total}`} />
              <Statistic title="작성 글자 수" value={record.words} suffix="자" />
              <Tag color={record.status === 'Needs review' ? 'warning' : 'success'}>
                {record.status}
              </Tag>
            </Space>
            <Progress
              percent={Math.round((record.score / record.total) * 100)}
              status={record.status === 'Needs review' ? 'exception' : 'active'}
              style={{ marginTop: 16 }}
            />
          </Card>
          <Alert
            type="info"
            showIcon
            message="AI 총평"
            description={record.summary}
          />
          <Card title="문제 지문">
            <Typography.Paragraph>
              한국어 학습자의 복습 방법 변화를 나타낸 그래프를 보고, 가장 두드러진 변화와 그 의미를 설명하십시오.
            </Typography.Paragraph>
          </Card>
          <Tabs
            items={[
              {
                key: 'structure',
                label: '구조 분석',
                children: (
                  <Collapse
                    defaultActiveKey={['intro']}
                    items={[
                      {
                        key: 'intro',
                        label: '도입',
                        children: '그래프가 무엇을 보여 주는지 첫 문장에서 명확히 제시했습니다.',
                      },
                      {
                        key: 'body',
                        label: '전개',
                        children:
                          '수치 비교는 가능하지만 증가와 감소 표현이 반복됩니다. “이에 비해”, “눈에 띄게” 같은 연결 표현을 추가해 보세요.',
                      },
                      {
                        key: 'closing',
                        label: '마무리',
                        children:
                          '결론은 적절하지만 학습자의 변화 원인을 한 문장 더 보완하면 설득력이 높아집니다.',
                      },
                    ]}
                  />
                ),
              },
              {
                key: 'correction',
                label: '상세 첨삭',
                children: (
                  <Alert
                    type="warning"
                    showIcon
                    message="문장 개선 제안"
                    description="“많이 증가했다”보다 “20%에서 45%로 두 배 이상 증가했다”처럼 수치를 함께 쓰면 더 정확합니다."
                  />
                ),
              },
            ]}
          />
        </Space>
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Card title="기본 정보">
            <Descriptions column={1} size="small">
              <Descriptions.Item label="문항">{record.type}</Descriptions.Item>
              <Descriptions.Item label="제출일">{record.date}</Descriptions.Item>
              <Descriptions.Item label="상위 수준">중상</Descriptions.Item>
            </Descriptions>
          </Card>
          <Card title="다음 행동">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button type="primary" block onClick={() => navigate('/writing/53')}>
                비슷한 주제로 다시 쓰기
              </Button>
              <Button block>PDF 저장</Button>
              <Button block>연습 대화 보기</Button>
              <Button danger block>
                피드백 신고하기
              </Button>
            </Space>
          </Card>
        </Space>
      </div>
    </>
  );
}
