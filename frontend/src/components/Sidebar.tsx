import React from 'react';
import { Box, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Tooltip, useTheme, alpha } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import HomeIcon from '@mui/icons-material/Home';
import VideoLibraryIcon from '@mui/icons-material/VideoLibrary';
import FolderIcon from '@mui/icons-material/Folder';
import { Link as RouterLink, useLocation } from 'react-router-dom';

interface SidebarProps {
    isOpen: boolean;
}

const navItems = [
    { text: 'Home', icon: <HomeIcon />, path: '/' },
    { text: 'Templates', icon: <VideoLibraryIcon />, path: '/templates' },
    // { text: 'Generate', icon: <AddCircleOutlineIcon />, path: '/generate' },
    // { text: 'Editor', icon: <EditIcon />, path: '/editor' },
    { text: 'My Content', icon: <FolderIcon />, path: '/content' },
];

const sidebarVariants = {
    open: { width: 240, transition: { type: 'spring', stiffness: 300, damping: 30 } },
    closed: { width: 70, transition: { type: 'spring', stiffness: 300, damping: 30 } },
} as const;

const Sidebar: React.FC<SidebarProps> = ({ isOpen }) => {
    const theme = useTheme();
    const location = useLocation();

    return (
        <Box
            component={motion.div}
            variants={sidebarVariants}
            initial={false}
            animate={isOpen ? 'open' : 'closed'}
            sx={{
                height: '100vh',
                position: 'fixed',
                top: 0,
                left: 0,
                zIndex: (theme) => theme.zIndex.drawer,
                backgroundColor: alpha(theme.palette.background.default, 0.8),
                backdropFilter: 'blur(15px)',
                borderRight: `1px solid ${theme.palette.divider}`,
            }}
        >
            <List sx={{ mt: '80px' }}>
                {navItems.map((item) => {
                    const isActive = location.pathname === item.path;
                    return (
                        <ListItem key={item.text} disablePadding sx={{ display: 'block' }}>
                            <Tooltip title={isOpen ? '' : item.text} placement="right">
                                <ListItemButton
                                    component={RouterLink}
                                    to={item.path}
                                    sx={{
                                        minHeight: 48,
                                        justifyContent: isOpen ? 'initial' : 'center',
                                        px: 2.5,
                                        mx: 1.5,
                                        my: 0.5,
                                        borderRadius: '12px',
                                        backgroundColor: isActive ? alpha(theme.palette.primary.main, 0.15) : 'transparent',
                                        color: isActive ? 'primary.main' : 'text.primary',
                                        '&:hover': {
                                            backgroundColor: alpha(theme.palette.primary.main, 0.25),
                                        }
                                    }}
                                >
                                    <ListItemIcon
                                        sx={{
                                            minWidth: 0,
                                            mr: isOpen ? 3 : 'auto',
                                            justifyContent: 'center',
                                            color: isActive ? 'primary.main' : 'inherit'
                                        }}
                                    >
                                        {item.icon}
                                    </ListItemIcon>
                                    <AnimatePresence>
                                        {isOpen && (
                                            <motion.div
                                                initial={{ opacity: 0, x: -20 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                exit={{ opacity: 0, x: -20 }}
                                                transition={{ duration: 0.2, delay: 0.1 }}
                                                style={{ width: '100%', whiteSpace: 'nowrap' }}
                                            >
                                                <ListItemText
                                                    primary={item.text}
                                                    primaryTypographyProps={{
                                                        variant: 'body2',
                                                        fontWeight: isActive ? 600 : 400
                                                    }}
                                                    sx={{ opacity: 1 }}
                                                />
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </ListItemButton>
                            </Tooltip>
                        </ListItem>
                    );
                })}
            </List>
        </Box>
    );
};

export default Sidebar;
