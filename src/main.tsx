import React from 'react';
import ReactDOM from 'react-dom/client';
import { useEffect } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { App as AntApp, ConfigProvider } from 'antd';
import koKR from 'antd/locale/ko_KR';
import App from './App';
import { useThemeStore } from './stores/useThemeStore';
import { defaultThemeName, getAppTheme } from './theme/themes';
import './styles/global.css';

function Root() {
  const appearance = useThemeStore((state) => state.appearance);
  const activeTheme = getAppTheme(defaultThemeName, appearance);

  useEffect(() => {
    const root = document.documentElement;

    root.dataset.theme = activeTheme.name;
    root.dataset.appearance = appearance;

    for (const [name, value] of Object.entries(activeTheme.cssVars)) {
      root.style.setProperty(name, value);
    }
  }, [activeTheme.cssVars, activeTheme.name, appearance]);

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
