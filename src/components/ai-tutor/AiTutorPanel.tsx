import {
  BellOutlined,
  BookOutlined,
  CustomerServiceOutlined,
  MessageOutlined,
  SearchOutlined,
  SendOutlined,
} from '@ant-design/icons';
import {
  Button,
  Drawer,
  Empty,
  Input,
  List,
  Space,
  Tabs,
  Tag,
  Typography,
} from 'antd';
import { useState } from 'react';
import { useAiTutorStore, type AiTutorTab } from '../../stores/useAiTutorStore';

const quickActions = [
  { label: '단어 검색', icon: <SearchOutlined />, message: '증가하다의 예문을 알려줘.' },
  { label: '문장 교정', icon: <BookOutlined />, message: '이 문장을 TOPIK 쓰기 답안답게 고쳐줘.' },
  { label: 'Q&A', icon: <MessageOutlined />, message: '쓰기 53번에서 도입은 어떻게 써야 해?' },
  { label: '1:1 문의', icon: <CustomerServiceOutlined />, message: '학습 기록 저장이 궁금해.' },
];

export function AiTutorPanel() {
  const { open, activeTab, messages, closePanel, setTab, sendMessage } = useAiTutorStore();
  const [draft, setDraft] = useState('');

  const submitMessage = (content: string) => {
    const trimmed = content.trim();
    if (!trimmed) return;
    sendMessage(trimmed);
    setDraft('');
  };

  return (
    <Drawer
      title="AI 튜터"
      placement="right"
      width={380}
      open={open}
      onClose={closePanel}
      styles={{ body: { padding: 0 } }}
    >
      <Tabs
        activeKey={activeTab}
        onChange={(key) => setTab(key as AiTutorTab)}
        items={[
          {
            key: 'home',
            label: '홈',
            children: (
              <div style={{ padding: 20 }}>
                <Typography.Title level={4} style={{ marginTop: 0 }}>
                  지금 화면에서 바로 물어보세요
                </Typography.Title>
                <Typography.Paragraph type="secondary">
                  단어 뜻, 문장 교정, 쓰기 구조처럼 학습 중 막힌 부분을 현재 흐름 안에서 확인할 수 있습니다.
                </Typography.Paragraph>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {quickActions.map((action) => (
                    <Button
                      key={action.label}
                      icon={action.icon}
                      block
                      onClick={() => submitMessage(action.message)}
                    >
                      {action.label}
                    </Button>
                  ))}
                </Space>
              </div>
            ),
          },
          {
            key: 'chat',
            label: '채팅',
            children: (
              <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100dvh - 120px)' }}>
                <List
                  style={{ flex: 1, overflow: 'auto', padding: '0 20px' }}
                  dataSource={messages}
                  renderItem={(item) => (
                    <List.Item>
                      <List.Item.Meta
                        title={item.role === 'assistant' ? 'AI 튜터' : '나'}
                        description={item.content}
                      />
                    </List.Item>
                  )}
                />
                <Space.Compact style={{ padding: 20 }}>
                  <Input
                    aria-label="AI 튜터에게 보낼 메시지"
                    value={draft}
                    placeholder="질문을 입력하세요…"
                    onChange={(event) => setDraft(event.target.value)}
                    onPressEnter={() => submitMessage(draft)}
                  />
                  <Button
                    type="primary"
                    aria-label="메시지 전송"
                    icon={<SendOutlined />}
                    disabled={!draft.trim()}
                    onClick={() => submitMessage(draft)}
                  />
                </Space.Compact>
              </div>
            ),
          },
          {
            key: 'notifications',
            label: '알림',
            children: (
              <div style={{ padding: 20 }}>
                <List
                  dataSource={[
                    '오늘 쓰기 53번 구조 연습을 1회 완료하면 주간 목표가 채워집니다.',
                    '지난 피드백에서 수치 비교 표현을 다시 복습해 보세요.',
                  ]}
                  locale={{ emptyText: <Empty description="새 알림이 없습니다" /> }}
                  renderItem={(item) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={<BellOutlined />}
                        title={<Tag color="processing">학습 알림</Tag>}
                        description={item}
                      />
                    </List.Item>
                  )}
                />
              </div>
            ),
          },
        ]}
      />
    </Drawer>
  );
}
