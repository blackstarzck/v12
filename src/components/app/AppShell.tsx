import {
  BookOutlined,
  EditOutlined,
  FileTextOutlined,
  HomeOutlined,
  MenuOutlined,
  MessageOutlined,
  ProfileOutlined,
  ReadOutlined,
  RobotOutlined,
  SettingOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import {
  Avatar,
  Button,
  Drawer,
  Grid,
  Layout,
  Menu,
  Segmented,
  Space,
  Tooltip,
  Typography,
} from 'antd';
import type { MenuProps } from 'antd';
import { useState, type ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAiTutorStore } from '../../stores/useAiTutorStore';
import { useThemeStore } from '../../stores/useThemeStore';
import { useUserStore } from '../../stores/useUserStore';
import type { Locale } from '../../types/domain';
import { AiTutorPanel } from '../ai-tutor/AiTutorPanel';
import { SettingsDrawer } from './SettingsDrawer';

const { Header, Content, Sider } = Layout;

const menuItems: NonNullable<MenuProps['items']> = [
  { key: '/', icon: <HomeOutlined />, label: <Link to="/">홈</Link> },
  {
    key: '/practice/create',
    icon: <ReadOutlined />,
    label: <Link to="/practice/create">AI 문제 생성</Link>,
  },
  {
    key: '/writing/setup',
    icon: <EditOutlined />,
    label: <Link to="/writing/setup">쓰기 집중 연습</Link>,
  },
  {
    key: '/writing/feedback',
    icon: <FileTextOutlined />,
    label: <Link to="/writing/feedback">쓰기 보관함</Link>,
  },
  {
    key: '/mock/results',
    icon: <TrophyOutlined />,
    label: <Link to="/mock/results">모의고사 결과</Link>,
  },
  {
    key: '/library',
    icon: <BookOutlined />,
    label: <Link to="/library">내 서재</Link>,
  },
  {
    key: '/vocabulary',
    icon: <ReadOutlined />,
    label: <Link to="/vocabulary">단어장</Link>,
  },
  {
    key: '/board',
    icon: <ProfileOutlined />,
    label: <Link to="/board">게시판</Link>,
  },
  {
    key: '/profile',
    icon: <SettingOutlined />,
    label: <Link to="/profile">프로필 설정</Link>,
  },
];

function selectedMenuKey(pathname: string) {
  if (pathname.startsWith('/writing/') && !pathname.startsWith('/writing/feedback')) {
    return '/writing/setup';
  }
  if (pathname.startsWith('/mock/')) {
    return '/mock/results';
  }

  const sortedKeys = menuItems
    .map((item) => String(item?.key))
    .filter(Boolean)
    .sort((a, b) => b.length - a.length);

  return sortedKeys.find((key) => key !== '/' && pathname.startsWith(key)) ?? '/';
}

function SidebarContent() {
  const location = useLocation();
  const { name, plan } = useUserStore();
  const appearance = useThemeStore((state) => state.appearance);

  return (
    <>
      <Link className="app-logo" to="/" aria-label="TALKPIK AI 홈으로 이동">
        <RobotOutlined aria-hidden />
        <span>TALKPIK AI</span>
      </Link>
      <Menu
        mode="inline"
        theme={appearance === 'dark' ? 'dark' : 'light'}
        selectedKeys={[selectedMenuKey(location.pathname)]}
        items={menuItems}
        style={{ borderInlineEnd: 0, padding: '8px 12px' }}
      />
      <div style={{ margin: 'auto 16px 16px', paddingTop: 16 }}>
        <Link to="/profile" aria-label="프로필 설정으로 이동">
          <Space>
            <Avatar style={{ backgroundColor: 'var(--app-brand)' }}>{name.slice(0, 1)}</Avatar>
            <span>
              <Typography.Text strong>{name} 님</Typography.Text>
              <br />
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                {plan}
              </Typography.Text>
            </span>
          </Space>
        </Link>
      </div>
    </>
  );
}

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const screens = Grid.useBreakpoint();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const { name, locale, setLocale } = useUserStore();
  const appearance = useThemeStore((state) => state.appearance);
  const { openPanel } = useAiTutorStore();
  const isMobile = !screens.lg;

  return (
    <Layout className="app-shell" hasSider={!isMobile}>
      <a className="skip-link" href="#main-content">
        본문으로 바로가기
      </a>
      {!isMobile && (
        <Sider width={256} className="app-sidebar" theme={appearance === 'dark' ? 'dark' : 'light'}>
          <div style={{ minHeight: '100%', display: 'flex', flexDirection: 'column' }}>
            <SidebarContent />
          </div>
        </Sider>
      )}
      <Layout>
        <Header className="app-header">
          <Space size={12}>
            {isMobile && (
              <Button
                aria-label="주요 메뉴 열기"
                icon={<MenuOutlined />}
                onClick={() => setMobileOpen(true)}
              />
            )}
            <div>
              <Typography.Text strong>{name} 님의 학습 공간</Typography.Text>
              <br />
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                오늘의 목표를 확인하고 바로 이어서 학습하세요.
              </Typography.Text>
            </div>
          </Space>
          <Space>
            <Segmented
              aria-label="화면 언어 선택"
              value={locale}
              options={['KO', 'VI', 'EN']}
              onChange={(value) => setLocale(value as Locale)}
            />
            <Tooltip title="화면 설정">
              <Button
                aria-label="화면 설정 열기"
                icon={<SettingOutlined />}
                onClick={() => setSettingsOpen(true)}
              />
            </Tooltip>
            <Tooltip title="AI 튜터 열기">
              <Button
                aria-label="AI 튜터 열기"
                icon={<MessageOutlined />}
                onClick={() => openPanel('home')}
              />
            </Tooltip>
          </Space>
        </Header>
        <Content id="main-content" className="app-content">
          {children}
        </Content>
      </Layout>
      <Drawer
        title="TALKPIK AI"
        placement="left"
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        width={288}
      >
        <SidebarContent />
      </Drawer>
      <SettingsDrawer open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <Tooltip title="AI 튜터">
        <Button
          type="primary"
          shape="circle"
          size="large"
          className="ai-float-button"
          aria-label="AI 튜터 열기"
          icon={<RobotOutlined />}
          onClick={() => openPanel('home')}
        />
      </Tooltip>
      <AiTutorPanel />
    </Layout>
  );
}
