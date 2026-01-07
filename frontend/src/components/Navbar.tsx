import React from 'react';
import { AppBar, Toolbar, Typography, IconButton, Box } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import MenuIcon from '@mui/icons-material/Menu';
import HomeIcon from '@mui/icons-material/Home';
import FolderIcon from '@mui/icons-material/Folder';

interface NavbarProps {
    onMenuClick: () => void;
    minimal?: boolean;
}

const Navbar: React.FC<NavbarProps> = ({ onMenuClick, minimal = false }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const isGeneratePage = location.pathname === '/generate';
    const isHomePage = location.pathname === '/';

    return (
        <AppBar
            position={minimal ? "relative" : "fixed"}
            sx={{
                zIndex: (theme) => theme.zIndex.drawer + 1,
                bgcolor: minimal ? '#111' : undefined,
                borderBottom: minimal ? '1px solid #222' : undefined
            }}
        >
            <Toolbar sx={{ minHeight: minimal ? 48 : 64 }}>
                {!minimal && (
                    <IconButton
                        color="inherit"
                        aria-label="open drawer"
                        onClick={onMenuClick}
                        edge="start"
                        sx={{ mr: 2 }}
                    >
                        <MenuIcon />
                    </IconButton>
                )}
                {minimal && (
                    <IconButton
                        color="inherit"
                        onClick={() => navigate('/')}
                        edge="start"
                        sx={{ mr: 2 }}
                    >
                        <HomeIcon />
                    </IconButton>
                )}
                <Typography
                    variant={minimal ? "subtitle1" : "h6"}
                    noWrap
                    component="div"
                    sx={{
                        cursor: 'pointer',
                        fontWeight: minimal ? 700 : 600, // 略微加粗品牌名
                        letterSpacing: '0.5px',
                        flexGrow: 1
                    }}
                    onClick={() => navigate('/')}
                >
                    Orenix AI
                </Typography>
                
                {minimal && isGeneratePage && (
                    <IconButton
                        color="inherit"
                        onClick={() => navigate('/content')}
                        title="My Content"
                        sx={{ ml: 1 }}
                    >
                        <FolderIcon />
                    </IconButton>
                )}

                {minimal && !isGeneratePage && !isHomePage && (
                    <Box sx={{
                        ml: 2,
                        px: 1.5,
                        py: 0.5,
                        bgcolor: 'rgba(255,64,129,0.2)',
                        borderRadius: 1
                    }}>
                        <Typography variant="caption" sx={{ color: '#FF4081', fontWeight: 600 }}>
                            Studio
                        </Typography>
                    </Box>
                )}
            </Toolbar>
        </AppBar>
    );
};

export default Navbar;
