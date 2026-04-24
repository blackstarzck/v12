import {
  Alert,
  Button,
  Card,
  Col,
  Flex,
  Input,
  List,
  Radio,
  Row,
  Space,
  Tag,
  Typography,
} from 'antd';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '../components/shared/PageHeader';
import { writingGuides } from '../data/mockData';
import { useWritingStore } from '../stores/useWritingStore';
import type { WritingType } from '../types/domain';

const topics = ['환경', '교육', '건강', '교통', '문화생활', '온라인 학습'];

export function WritingSetupPage() {
  const navigate = useNavigate();
  const { selectedType, selectedTopic, selectWritingType, setTopic } = useWritingStore();
  const cta = selectedType ? `${selectedType}번 문제 생성하기` : '문제 유형을 먼저 선택해주세요';

  return (
    <>
      <PageHeader
        title="쓰기 집중 연습 설정"
        description="TOPIK 쓰기 유형과 주제를 고른 뒤 답안 작성 화면으로 이동합니다."
      />

      <Row gutter={[16, 16]} align="top">
        <Col xs={24} lg={16}>
          <Card>
            <Space direction="vertical" size={20} style={{ width: '100%' }}>
              <div>
                <Typography.Title level={4}>쓰기 유형</Typography.Title>
                <Radio.Group value={selectedType} onChange={(event) => selectWritingType(event.target.value as WritingType)}>
                  <Space direction="vertical" size={10}>
                    {(Object.keys(writingGuides) as WritingType[]).map((type) => (
                      <Radio key={type} value={type}>
                        <Flex vertical gap={2}>
                          <Typography.Text strong>
                            {type}번 {writingGuides[type].title}
                          </Typography.Text>
                          <Typography.Text type="secondary">
                            {writingGuides[type].prompt}
                          </Typography.Text>
                        </Flex>
                      </Radio>
                    ))}
                  </Space>
                </Radio.Group>
              </div>

              <div>
                <Typography.Title level={4}>주제 선택</Typography.Title>
                <Input.Search
                  aria-label="쓰기 주제 검색"
                  placeholder="주제를 검색해주세요"
                  onSearch={(value) => value && setTopic(value)}
                />
                <Space wrap style={{ marginTop: 12 }}>
                  {topics.map((topic) => (
                    <Tag.CheckableTag
                      key={topic}
                      checked={selectedTopic === topic}
                      onChange={() => setTopic(topic)}
                    >
                      {topic}
                    </Tag.CheckableTag>
                  ))}
                </Space>
              </div>

              <Button
                type="primary"
                size="large"
                disabled={!selectedType}
                onClick={() => selectedType && navigate(`/writing/${selectedType}`)}
              >
                {cta}
              </Button>
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <Alert
              showIcon
              type={selectedType ? 'success' : 'warning'}
              message={selectedType ? `${selectedType}번 유형을 선택했습니다` : '생성 전 필수 선택'}
              description={
                selectedType
                  ? `${writingGuides[selectedType].title} 화면에서 자동 저장과 제출 확인을 사용할 수 있습니다.`
                  : '쓰기 유형을 선택하면 생성 버튼이 활성화됩니다.'
              }
            />

            <Card title="연습 방식">
              <List
                size="small"
                dataSource={[
                  '문제 지문과 답안 입력 영역을 한눈에 확인합니다.',
                  '답안을 입력하면 초안이 자동 저장됩니다.',
                  '제출 전 확인 창으로 실수 제출을 막습니다.',
                ]}
                renderItem={(item) => (
                  <List.Item>
                    <Typography.Text type="secondary">{item}</Typography.Text>
                  </List.Item>
                )}
              />
            </Card>
          </Space>
        </Col>
      </Row>
    </>
  );
}
