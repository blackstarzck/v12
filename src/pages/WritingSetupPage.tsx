import {
  Alert,
  Button,
  Card,
  Input,
  Radio,
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
  const cta = selectedType ? `${selectedType}번 문제 생성하기` : '문제 유형을 먼저 선택하세요';

  return (
    <>
      <PageHeader
        title="쓰기 집중 연습 설정"
        description="TOPIK 쓰기 유형과 주제를 고른 뒤 답안 작성 화면으로 이동합니다."
      />
      <div className="form-grid">
        <Card>
          <Space direction="vertical" size={20} style={{ width: '100%' }}>
            <div>
              <Typography.Title level={4}>쓰기 유형</Typography.Title>
              <Radio.Group
                value={selectedType}
                onChange={(event) => selectWritingType(event.target.value as WritingType)}
                style={{ width: '100%' }}
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  {(Object.keys(writingGuides) as WritingType[]).map((type) => (
                    <Radio key={type} value={type} className="answer-option">
                      <Typography.Text strong>{type}번 · {writingGuides[type].title}</Typography.Text>
                      <br />
                      <Typography.Text type="secondary">
                        {writingGuides[type].prompt}
                      </Typography.Text>
                    </Radio>
                  ))}
                </Space>
              </Radio.Group>
            </div>
            <div>
              <Typography.Title level={4}>주제 선택</Typography.Title>
              <Input.Search
                aria-label="쓰기 주제 검색"
                placeholder="주제를 검색하세요…"
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
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Alert
            showIcon
            type={selectedType ? 'success' : 'warning'}
            message={selectedType ? `${selectedType}번 유형이 선택되었습니다` : '생성 전 필수 선택'}
            description={
              selectedType
                ? `${writingGuides[selectedType].title} 화면에서 자동 저장과 제출 확인을 사용할 수 있습니다.`
                : '쓰기 유형을 선택하면 생성 버튼이 활성화됩니다.'
            }
          />
          <Card title="연습 방식">
            <ul className="compact-list">
              <li>문제 지문과 답안 입력 영역을 나란히 확인합니다.</li>
              <li>답안은 입력할 때마다 자동 저장됩니다.</li>
              <li>제출 전 확인 창으로 실수 제출을 막습니다.</li>
            </ul>
          </Card>
        </Space>
      </div>
    </>
  );
}
