import { Button, Card, Empty, List, Radio, Space, Tag, Typography } from 'antd';
import { useState } from 'react';
import { PageHeader } from '../components/shared/PageHeader';
import { vocabularyItems } from '../data/mockData';

export function VocabularyPage() {
  const [view, setView] = useState<'card' | 'list'>('card');
  const reviewWords = vocabularyItems.filter((item) => item.status === 'Review');

  return (
    <>
      <PageHeader
        title="단어장"
        description="저장한 단어의 뜻과 예문을 확인하고 암기 완료 처리합니다."
        extra={<Tag color="success">저장 단어 {vocabularyItems.length}개</Tag>}
      />
      <Space direction="vertical" size={16} style={{ width: '100%' }}>
        <Radio.Group
          aria-label="단어장 보기 방식"
          value={view}
          onChange={(event) => setView(event.target.value)}
        >
          <Radio.Button value="card">카드 보기</Radio.Button>
          <Radio.Button value="list">리스트 보기</Radio.Button>
        </Radio.Group>
        {reviewWords.length === 0 ? (
          <Empty description="복습할 단어가 없습니다">
            <Button>문제 풀이에서 단어 추가하기</Button>
          </Empty>
        ) : (
          <List
            grid={view === 'card' ? { gutter: 16, xs: 1, sm: 2, lg: 3 } : undefined}
            dataSource={reviewWords}
            renderItem={(item) => (
              <List.Item>
                <Card>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Tag>{item.level}</Tag>
                    <Typography.Title level={3} style={{ margin: 0 }}>
                      {item.word}
                    </Typography.Title>
                    <Typography.Text strong>{item.meaning}</Typography.Text>
                    <Typography.Paragraph type="secondary">{item.example}</Typography.Paragraph>
                    <Button block>암기 완료! 목록에서 제거</Button>
                  </Space>
                </Card>
              </List.Item>
            )}
          />
        )}
      </Space>
    </>
  );
}
