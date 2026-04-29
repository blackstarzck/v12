import {
  Alert,
  App as AntdApp,
  Button,
  Card,
  Col,
  Collapse,
  Input,
  List,
  Progress,
  Row,
  Space,
  Tabs,
  Tag,
  Typography,
} from 'antd';
import { SaveOutlined, SendOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppModal } from '../components/shared/AppModal';
import { PageHeader } from '../components/shared/PageHeader';
import { writingGuides } from '../data/mockData';
import { useWritingStore } from '../stores/useWritingStore';
import type { WritingType } from '../types/domain';

interface WritingPracticePageProps {
  type: WritingType;
}

export function WritingPracticePage({ type }: WritingPracticePageProps) {
  const navigate = useNavigate();
  const { message } = AntdApp.useApp();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const { selectedTopic, drafts, autosavedAt, updateDraft, markSubmitted } =
    useWritingStore();
  const guide = writingGuides[type];
  const draft = drafts[type];
  const minLength = type === '53' || type === '54' ? 120 : 30;
  const canSubmit = draft.trim().length >= minLength;
  const progress = Math.min(100, Math.round((draft.trim().length / minLength) * 100));

  const submitAnswer = () => {
    markSubmitted(type);
    setConfirmOpen(false);
    message.success('답안을 제출했습니다. 피드백 보관함에서 결과를 확인하세요.');
    navigate('/writing/feedback');
  };

  return (
    <>
      <PageHeader
        title={`${type}번 쓰기 연습`}
        description={`${guide.title} 답안을 작성합니다. 주제: ${selectedTopic ?? '추천 주제'}`}
        extra={<Tag color="processing">자동 저장 {autosavedAt ?? '대기 중'}</Tag>}
      />

      <Row gutter={[16, 16]} align="top">
        <Col xs={24} lg={16}>
          <Card>
            <Space direction="vertical" size={18} style={{ width: '100%' }}>
              <Alert type="info" showIcon message={guide.prompt} />
              <Tabs
                items={guide.tabs.map((tab) => ({
                  key: tab,
                  label: tab,
                  children: (
                    <Typography.Paragraph type="secondary">
                      {tab} 단계에서 요구하는 정보를 먼저 한 문장으로 정리한 뒤 답안에 반영하세요.
                    </Typography.Paragraph>
                  ),
                }))}
              />
              <Input.TextArea
                className="writing-editor"
                aria-label={`${type}번 쓰기 답안 입력`}
                value={draft}
                placeholder="답안을 입력해주세요."
                showCount
                onChange={(event) => updateDraft(type, event.target.value)}
              />
              <Space wrap>
                <Button icon={<SaveOutlined />}>초안 저장</Button>
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  disabled={!canSubmit}
                  onClick={() => setConfirmOpen(true)}
                >
                  제출하기
                </Button>
              </Space>
              {!canSubmit && (
                <Alert
                  type="warning"
                  showIcon
                  message={`최소 ${minLength}자 이상 작성하면 제출할 수 있습니다`}
                />
              )}
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <Card title="작성 상태">
              <Progress percent={progress} />
              <Typography.Text type="secondary">
                현재 {draft.trim().length}자를 작성했습니다.
              </Typography.Text>
            </Card>

            <Card title="추천 자료">
              <Collapse
                defaultActiveKey={['expressions']}
                items={[
                  {
                    key: 'expressions',
                    label: '추천 표현',
                    children: (
                      <List
                        size="small"
                        dataSource={[
                          '이 자료에서 보이는 흐름을 보여 주는 표현',
                          '반면에 수치가 감소하는 경향을 보이는 표현',
                          '이를 통해 두 대상의 차이를 설명하는 표현',
                        ]}
                        renderItem={(item) => (
                          <List.Item>
                            <Typography.Text type="secondary">{item}</Typography.Text>
                          </List.Item>
                        )}
                      />
                    ),
                  },
                  {
                    key: 'vocabulary',
                    label: '핵심 어휘',
                    children: (
                      <Space wrap>
                        <Tag>증가하다</Tag>
                        <Tag>감소하다</Tag>
                        <Tag>비율</Tag>
                        <Tag>경향</Tag>
                      </Space>
                    ),
                  },
                  {
                    key: 'sample',
                    label: '답안 구조 예시',
                    children: <Typography.Paragraph>{guide.sample}</Typography.Paragraph>,
                  },
                ]}
              />
            </Card>
          </Space>
        </Col>
      </Row>

      <AppModal
        title="답안을 제출할까요?"
        open={confirmOpen}
        okText="제출하기"
        cancelText="계속 작성하기"
        onOk={submitAnswer}
        onCancel={() => setConfirmOpen(false)}
      >
        제출 후에는 피드백 생성 단계로 이동합니다. 현재 답안은 보관함에도 저장됩니다.
      </AppModal>
    </>
  );
}
