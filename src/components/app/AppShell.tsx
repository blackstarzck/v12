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
  theme,
  Tooltip,
  Typography,
} from 'antd';
import type { MenuProps } from 'antd';
import { useState, type ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAiTutorStore } from '../../stores/useAiTutorStore';
import { useThemeStore } from '../../stores/useThemeStore';
import { useUserStore } from '../../stores/useUserStore';
import type { Locale } from '../../types/domain';
import { AiTutorPanel } from '../ai-tutor/AiTutorPanel';
import { SettingsDrawer } from './SettingsDrawer';

const { Header, Content, Sider } = Layout;

const menuItems: NonNullable<MenuProps['items']> = [
  { key: '/', icon: <HomeOutlined />, label: '홈' },
  { key: '/practice/create', icon: <ReadOutlined />, label: 'AI 문제 생성' },
  { key: '/writing/setup', icon: <EditOutlined />, label: '쓰기 집중 연습' },
  { key: '/writing/feedback', icon: <FileTextOutlined />, label: '쓰기 보관함' },
  { key: '/mock/results', icon: <TrophyOutlined />, label: '모의고사 결과' },
  { key: '/library', icon: <BookOutlined />, label: '내 서재' },
  { key: '/vocabulary', icon: <ReadOutlined />, label: '단어장' },
  { key: '/board', icon: <ProfileOutlined />, label: '게시판' },
  { key: '/profile', icon: <SettingOutlined />, label: '프로필 설정' },
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
  const navigate = useNavigate();
  const location = useLocation();
  const { name, plan } = useUserStore();
  const appearance = useThemeStore((state) => state.appearance);
  const { token } = theme.useToken();

  return (
    <>
      <Link
        className="app-logo"
        to="/"
        aria-label="TALKPIK AI 홈으로 이동"
        style={{ color: token.colorPrimary }}
      >
        <RobotOutlined aria-hidden />
        <span className="app-logo-text">TALKPIK AI</span>
      </Link>
      <Menu
        className="app-sidebar-menu"
        mode="inline"
        theme={appearance === 'dark' ? 'dark' : 'light'}
        selectedKeys={[selectedMenuKey(location.pathname)]}
        items={menuItems}
        onClick={({ key }) => navigate(String(key))}
      />
      <div className="app-sidebar-footer">
        <Link className="app-profile-link" to="/profile" aria-label="프로필 설정으로 이동">
          <Space>
            <Avatar style={{ backgroundColor: token.colorPrimary }}>{name.slice(0, 1)}</Avatar>
            <span>
              <Typography.Text strong>{name} 님</Typography.Text>
              <br />
              <Typography.Text type="secondary">{plan}</Typography.Text>
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
  const { token } = theme.useToken();
  const isMobile = !screens.lg;

  return (
    <Layout className="app-shell" hasSider={!isMobile} style={{ background: token.colorBgLayout }}>
      <a className="skip-link" href="#main-content">
        본문으로 바로가기
      </a>
      {!isMobile && (
        <Sider
          width={256}
          className="app-sidebar"
          theme={appearance === 'dark' ? 'dark' : 'light'}
          style={{ borderRight: `1px solid ${token.colorSplit}` }}
        >
          <div className="app-sidebar-body">
            <SidebarContent />
          </div>
        </Sider>
      )}
      <Layout>
        <Header
          className="app-header"
          style={{ background: token.colorBgContainer, borderBottom: `1px solid ${token.colorSplit}` }}
        >
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
              <Typography.Text type="secondary">오늘의 목표를 확인하고 바로 이어서 학습하세요.</Typography.Text>
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
