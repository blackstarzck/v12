import { Drawer } from 'antd';
import type { DrawerProps } from 'antd';

function joinClassNames(...values: Array<string | undefined>) {
  return values.filter(Boolean).join(' ');
}

export function AppDrawer({ rootClassName, ...props }: DrawerProps) {
  return (
    <Drawer
      rootClassName={joinClassNames('app-drawer', rootClassName)}
      {...props}
    />
  );
}
