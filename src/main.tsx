import React from 'react';
import ReactDOM from 'react-dom/client';
import { useEffect } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { App as AntApp, ConfigProvider, theme as antdThemeApi } from 'antd';
import koKR from 'antd/locale/ko_KR';
import App from './App';
import { useThemeStore } from './stores/useThemeStore';
import { getAppTheme } from './theme';
import './styles/global.css';

function Root() {
  const appearance = useThemeStore((state) => state.appearance);
  const themeName = useThemeStore((state) => state.themeName);
  const activeTheme = getAppTheme(themeName, appearance);

  useEffect(() => {
    const root = document.documentElement;
    const resolvedToken = antdThemeApi.getDesignToken(activeTheme.antd);
    const isLiquidGlass = activeTheme.name === 'liquidGlass';

    root.dataset.theme = activeTheme.name;
    root.dataset.appearance = appearance;
    root.style.colorScheme = appearance;
    if (isLiquidGlass) {
      document.body.style.removeProperty('background');
    } else {
      document.body.style.background = resolvedToken.colorBgLayout;
    }
    document.body.style.color = resolvedToken.colorText;
  }, [activeTheme.antd, activeTheme.name, appearance]);

  return (
    <ConfigProvider
      locale={koKR}
      theme={activeTheme.antd}
      card={themeName === 'liquidGlass' ? { variant: 'borderless' } : undefined}
    >
      <AntApp>
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <App />
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>,
);
