import {
  Alert,
  App as AntdApp,
  Button,
  Card,
  Col,
  Flex,
  Form,
  Radio,
  Row,
  Select,
  Slider,
  Space,
  Tag,
  Typography,
} from 'antd';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '../components/shared/PageHeader';
import { usePracticeStore } from '../stores/usePracticeStore';
import type { PracticeArea, ProblemType, TopikLevel } from '../types/domain';

const problemTypes: Array<{ value: ProblemType; label: string; description: string }> = [
  {
    value: 'grammar',
    label: '문법과 표현',
    description: '문장 안에서 가장 적절한 표현을 고르는 유형입니다.',
  },
  {
    value: 'main-idea',
    label: '중심 내용',
    description: '지문의 핵심 주제와 말하는 의도를 파악합니다.',
  },
  {
    value: 'detail',
    label: '세부 정보',
    description: '본문과 일치하는 정보를 찾는 유형입니다.',
  },
  {
    value: 'audio',
    label: '듣기 대화',
    description: '대화 상황과 화자의 의도를 확인합니다.',
  },
];

export function PracticeCreatePage() {
  const navigate = useNavigate();
  const { message } = AntdApp.useApp();
  const {
    area,
    topikLevel,
    targetGrade,
    problemType,
    questionCount,
    isGenerating,
    setArea,
    setTopikLevel,
    setTargetGrade,
    setProblemType,
    setQuestionCount,
    setGenerating,
    startProblemSet,
  } = usePracticeStore();
  const selectedType = problemTypes.find((item) => item.value === problemType);
  const canGenerate = Boolean(area && problemType);

  const handleGenerate = () => {
    if (!canGenerate) {
      message.warning('문제 유형을 먼저 선택해주세요.');
      return;
    }

    setGenerating(true);
    window.setTimeout(() => {
      startProblemSet();
      setGenerating(false);
      message.success('AI 문제가 준비됐습니다. 첫 문제로 이동합니다.');
      navigate('/practice/solve');
    }, 700);
  };

  return (
    <>
      <PageHeader
        title="AI 맞춤 문제 생성"
        description="영역, TOPIK 단계, 목표 급수, 문제 유형을 선택하면 바로 문제 세트가 준비됩니다."
      />

      <Row gutter={[16, 16]} align="top">
        <Col xs={24} lg={16}>
          <Card>
            <Form layout="vertical" requiredMark="optional">
              <Form.Item label="학습 영역" required>
                <Radio.Group
                  value={area}
                  onChange={(event) => setArea(event.target.value as PracticeArea)}
                >
                  <Radio.Button value="reading">읽기</Radio.Button>
                  <Radio.Button value="listening">듣기</Radio.Button>
                </Radio.Group>
              </Form.Item>

              <Form.Item label="TOPIK 단계" required>
                <Select
                  value={topikLevel}
                  onChange={(value) => setTopikLevel(value as TopikLevel)}
                  options={[
                    { value: 'TOPIK I', label: 'TOPIK I' },
                    { value: 'TOPIK II', label: 'TOPIK II' },
                  ]}
                />
              </Form.Item>

              <Form.Item label="목표 급수" required>
                <Select
                  value={targetGrade}
                  onChange={setTargetGrade}
                  options={['2급', '3급', '4급', '5급', '6급'].map((grade) => ({
                    value: grade,
                    label: grade,
                  }))}
                />
              </Form.Item>

              <Form.Item label="문제 유형" required>
                <Radio.Group value={problemType} onChange={(event) => setProblemType(event.target.value as ProblemType)}>
                  <Space direction="vertical" size={10}>
                    {problemTypes.map((type) => (
                      <Radio key={type.value} value={type.value}>
                        <Flex vertical gap={2}>
                          <Typography.Text strong>{type.label}</Typography.Text>
                          <Typography.Text type="secondary">{type.description}</Typography.Text>
                        </Flex>
                      </Radio>
                    ))}
                  </Space>
                </Radio.Group>
              </Form.Item>

              <Form.Item label={`생성할 문제 수: ${questionCount}문제`}>
                <Slider min={3} max={10} value={questionCount} onChange={setQuestionCount} />
              </Form.Item>

              <Button
                type="primary"
                size="large"
                loading={isGenerating}
                disabled={!canGenerate}
                onClick={handleGenerate}
              >
                AI 문제 생성 시작하기
              </Button>
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <Alert
              type={canGenerate ? 'success' : 'warning'}
              showIcon
              message={canGenerate ? '생성 준비가 완료됐습니다' : '필수 선택이 아직 남아 있습니다'}
              description={
                canGenerate
                  ? '생성 후 문제 풀이 화면으로 바로 이동합니다.'
                  : '학습 영역과 문제 유형을 선택하면 생성 버튼이 활성화됩니다.'
              }
            />

            <Card title="선택한 유형 미리보기">
              {selectedType ? (
                <Space direction="vertical">
                  <Tag color="processing">{selectedType.label}</Tag>
                  <Typography.Paragraph>{selectedType.description}</Typography.Paragraph>
                  <Typography.Text type="secondary">
                    지문을 읽고 보기 중 가장 적절한 답을 고른 뒤 해설로 약점을 확인합니다.
                  </Typography.Text>
                </Space>
              ) : (
                <Typography.Text type="secondary">
                  문제 유형을 고르면 풀이 방식과 예시가 여기에 표시됩니다.
                </Typography.Text>
              )}
            </Card>
          </Space>
        </Col>
      </Row>
    </>
  );
}
