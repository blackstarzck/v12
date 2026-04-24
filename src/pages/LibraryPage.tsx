import { Alert, Button, Card, Empty, Input, List, Select, Space, Tag, Typography } from 'antd';
import { PageHeader } from '../components/shared/PageHeader';

const savedProblems = [
  {
    id: 'p-1',
    title: '읽기 34번 중심 내용',
    meta: 'TOPIK II · 읽기 · 약점',
  },
  {
    id: 'p-2',
    title: '듣기 12번 대화 의도',
    meta: 'TOPIK I · 듣기 · 북마크',
  },
];

export function LibraryPage() {
  return (
    <>
      <PageHeader
        title="내 서재"
        description="저장한 문제를 조건별로 찾고 복습 바구니에 담습니다."
      />
      <Space direction="vertical" size={16} style={{ width: '100%' }}>
        <Alert
          type="info"
          showIcon
          message="취약 문항 공략"
          description="쓰기와 읽기에서 자주 틀린 유형을 먼저 복습하도록 정렬했습니다."
          action={<Button>전체 무작위 복습</Button>}
        />
        <Card>
          <Space wrap style={{ marginBottom: 16 }}>
            <Input.Search aria-label="저장 문제 검색" placeholder="문제 제목 검색…" />
            <Select
              aria-label="TOPIK 단계 필터"
              defaultValue="all"
              style={{ width: 160 }}
              options={[
                { value: 'all', label: '전체 단계' },
                { value: 'topik1', label: 'TOPIK I' },
                { value: 'topik2', label: 'TOPIK II' },
              ]}
            />
            <Select
              aria-label="영역 필터"
              defaultValue="all"
              style={{ width: 160 }}
              options={[
                { value: 'all', label: '전체 영역' },
                { value: 'reading', label: '읽기' },
                { value: 'listening', label: '듣기' },
                { value: 'writing', label: '쓰기' },
              ]}
            />
          </Space>
          <List
            dataSource={savedProblems}
            locale={{ emptyText: <Empty description="저장한 문제가 없습니다" /> }}
            renderItem={(item) => (
              <List.Item actions={[<Button key="review">풀기 시작</Button>, <Button key="basket">바구니 담기</Button>]}>
                <List.Item.Meta
                  title={<Typography.Text strong>{item.title}</Typography.Text>}
                  description={item.meta}
                />
                <Tag color="processing">복습 추천</Tag>
              </List.Item>
            )}
          />
        </Card>
      </Space>
    </>
  );
}
