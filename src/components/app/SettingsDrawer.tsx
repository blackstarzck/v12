import { MoonOutlined, SettingOutlined, SunOutlined } from '@ant-design/icons';
import { Flex, Segmented, Space, Typography } from 'antd';
import { AppDrawer } from '../shared/AppDrawer';
import { useThemeStore } from '../../stores/useThemeStore';
import { appearanceOptions, themeOptions, type AppAppearance, type AppThemeName } from '../../theme';

interface SettingsDrawerProps {
  open: boolean;
  onClose: () => void;
}

export function SettingsDrawer({ open, onClose }: SettingsDrawerProps) {
  const appearance = useThemeStore((state) => state.appearance);
  const themeName = useThemeStore((state) => state.themeName);
  const setAppearance = useThemeStore((state) => state.setAppearance);
  const setThemeName = useThemeStore((state) => state.setThemeName);
  const activeThemeOption =
    themeOptions.find((option) => option.value === themeName) ?? themeOptions[0];

  return (
    <AppDrawer
      title={
        <Space size={8}>
          <SettingOutlined aria-hidden />
          <span>화면 설정</span>
        </Space>
      }
      placement="right"
      open={open}
      onClose={onClose}
      width={340}
    >
      <Flex vertical gap={24}>
        <section aria-labelledby="theme-setting-title">
          <Flex vertical gap={12}>
            <Typography.Text id="theme-setting-title" strong>
              테마 스타일
            </Typography.Text>
            <Segmented
              block
              value={themeName}
              options={themeOptions.map((option) => ({
                label: option.label,
                value: option.value,
              }))}
              onChange={(value) => setThemeName(value as AppThemeName)}
              aria-label="테마 스타일 선택"
            />
            <Typography.Text type="secondary">{activeThemeOption.description}</Typography.Text>
          </Flex>
        </section>
        <section aria-labelledby="appearance-setting-title">
          <Flex vertical gap={12}>
            <Typography.Text id="appearance-setting-title" strong>
              화면 모드
            </Typography.Text>
            <Segmented
              block
              value={appearance}
              options={appearanceOptions.map((option) => ({
                label: option.label,
                value: option.value,
                icon: option.value === 'light' ? <SunOutlined /> : <MoonOutlined />,
              }))}
              onChange={(value) => setAppearance(value as AppAppearance)}
              aria-label="화면 모드 선택"
            />
          </Flex>
        </section>
      </Flex>
    </AppDrawer>
  );
}
