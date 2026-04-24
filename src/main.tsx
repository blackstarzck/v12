import React from 'react';
import ReactDOM from 'react-dom/client';
import { useEffect } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { App as AntApp, ConfigProvider, theme as antdThemeApi } from 'antd';
import koKR from 'antd/locale/ko_KR';
import App from './App';
import { useThemeStore } from './stores/useThemeStore';
import { defaultThemeName, getAppTheme } from './theme';
import './styles/global.css';

function Root() {
  const appearance = useThemeStore((state) => state.appearance);
  const activeTheme = getAppTheme(defaultThemeName, appearance);

  useEffect(() => {
    const root = document.documentElement;
    const resolvedToken = antdThemeApi.getDesignToken(activeTheme.antd);

    root.dataset.theme = activeTheme.name;
    root.dataset.appearance = appearance;
    root.style.colorScheme = appearance;
    document.body.style.background = resolvedToken.colorBgLayout;
    document.body.style.color = resolvedToken.colorText;
  }, [activeTheme.antd, activeTheme.name, appearance]);

  return (
    <ConfigProvider locale={koKR} theme={activeTheme.antd}>
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
