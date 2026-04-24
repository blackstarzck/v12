import { MoonOutlined, SettingOutlined, SunOutlined } from '@ant-design/icons';
import { Drawer, Flex, Segmented, Space, Typography } from 'antd';
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
      <Flex vertical gap={24}>
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
    </Drawer>
  );
}
