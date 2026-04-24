import { MoonOutlined, SettingOutlined, SunOutlined } from '@ant-design/icons';
import { Drawer, Segmented, Space, Typography } from 'antd';
import { useThemeStore } from '../../stores/useThemeStore';
import { appearanceOptions, type AppAppearance } from '../../theme';

interface SettingsDrawerProps {
  open: boolean;
  onClose: () => void;
}

export function SettingsDrawer({ open, onClose }: SettingsDrawerProps) {
  const appearance = useThemeStore((state) => state.appearance);
  const setAppearance = useThemeStore((state) => state.setAppearance);

  return (
    <Drawer
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
      <Space direction="vertical" size={24} className="settings-drawer-content">
        <section aria-labelledby="appearance-setting-title">
          <Space direction="vertical" size={12} className="settings-section">
            <Typography.Title id="appearance-setting-title" level={5} className="settings-title">
              화면 모드
            </Typography.Title>
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
          </Space>
        </section>
      </Space>
    </Drawer>
  );
}
