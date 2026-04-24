import { Button, Card, Input, List, Space, Table, Tabs, Tag, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '../components/shared/PageHeader';
import { noticeItems } from '../data/mockData';

export function BoardPage() {
  const navigate = useNavigate();

  return (
    <>
      <PageHeader
        title="게시판"
        description="공지사항과 이벤트를 구분해 확인합니다."
      />
      <Card>
        <Tabs
          items={[
            {
              key: 'notice',
              label: '공지사항',
              children: (
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Input.Search aria-label="공지 제목 검색" placeholder="공지 제목 검색…" />
                  <Table
                    rowKey="id"
                    dataSource={noticeItems}
                    columns={[
                      {
                        title: '구분',
                        dataIndex: 'category',
                        render: (value) => <Tag color={value === '중요' ? 'error' : 'processing'}>{value}</Tag>,
                      },
                      {
                        title: '제목',
                        dataIndex: 'title',
                        render: (value) => (
                          <Typography.Text strong>
                            <Button type="link" onClick={() => navigate('/board')}>
                              {value}
                            </Button>
                          </Typography.Text>
                        ),
                      },
                      { title: '작성자', dataIndex: 'author', responsive: ['md'] },
                      { title: '작성일', dataIndex: 'date', responsive: ['lg'] },
                      { title: '조회', dataIndex: 'views', responsive: ['lg'] },
                    ]}
                    scroll={{ x: 760 }}
                  />
                </Space>
              ),
            },
            {
              key: 'event',
              label: '이벤트',
              children: (
                <List
                  dataSource={[
                    {
                      title: '4월 쓰기 챌린지',
                      description: '쓰기 답안 5회 제출 시 AI 피드백 이용권을 추가 제공합니다.',
                      status: '진행중',
                    },
                    {
                      title: 'TOPIK 시험 직전 점검',
                      description: '시험 전날까지 모의고사 결과를 제출하면 약점 리포트를 받을 수 있습니다.',
                      status: '진행중',
                    },
                  ]}
                  renderItem={(item) => (
                    <List.Item>
                      <List.Item.Meta
                        title={
                          <Space>
                            <Typography.Text strong>{item.title}</Typography.Text>
                            <Tag color="success">{item.status}</Tag>
                          </Space>
                        }
                        description={item.description}
                      />
                    </List.Item>
                  )}
                />
              ),
            },
          ]}
        />
      </Card>
    </>
  );
}
