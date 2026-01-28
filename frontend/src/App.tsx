import React, { useState } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { Box } from '@mui/material';
import { motion } from 'framer-motion';

import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import HomePage from './pages/Home';
import TemplatesPage from './pages/Templates';
import ContentPage from './pages/Content';
import GeneratePage from './pages/Generate';
import TeamPage from './pages/Team';
import ProjectPage from './pages/Project';
import ImageGeneratePage from './pages/ImageGenerate';

const App: React.FC = () => {
    const [isSidebarOpen, setSidebarOpen] = useState(true);
    const location = useLocation();

    console.log('[App] Current location:', location.pathname);

    // 全屏页面（无侧边栏）
    const isFullScreenPage = location.pathname.startsWith('/generate') ||
                             location.pathname.startsWith('/project') ||
                             location.pathname === '/' ||
                             location.pathname === '/team';

    const toggleSidebar = () => {
        setSidebarOpen(!isSidebarOpen);
    };

    const contentVariants = {
        open: { marginLeft: 240, transition: { type: 'spring', stiffness: 300, damping: 30 } },
        closed: { marginLeft: 70, transition: { type: 'spring', stiffness: 300, damping: 30 } },
    } as const;

    // 全屏页面布局
    if (isFullScreenPage) {
        const isHomePage = location.pathname === '/';
        return (
            <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
                <Navbar onMenuClick={toggleSidebar} minimal />
                <Box sx={{ flex: 1, overflow: isHomePage ? 'auto' : 'hidden' }}>
                    <Routes>
                        <Route path="/" element={<HomePage />} />
                        <Route path="/generate" element={<GeneratePage />} />
                        <Route path="/project" element={<ProjectPage />} />
                        <Route path="/project/:projectId" element={<ProjectPage />} />
                        <Route path="/team" element={<TeamPage />} />
                    </Routes>
                </Box>
            </Box>
        );
    }

    return (
        <Box sx={{ display: 'flex' }}>
            <Navbar onMenuClick={toggleSidebar} />
            <Sidebar isOpen={isSidebarOpen} />
            <Box
                component={motion.main}
                variants={contentVariants}
                initial={false}
                animate={isSidebarOpen ? 'open' : 'closed'}
                sx={{ flexGrow: 1, paddingTop: '64px' }}
            >
                <Routes>
                    <Route path="/templates" element={<TemplatesPage />} />
                    <Route path="/content" element={<ContentPage />} />
                    <Route path="/images" element={<ImageGeneratePage />} />
                </Routes>
            </Box>
        </Box>
    );
};

export default App;