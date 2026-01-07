import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, Grid, Card, CardContent, Container, useTheme, alpha } from '@mui/material';
import { motion } from 'framer-motion';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import HowToRegIcon from '@mui/icons-material/HowToReg';
import EditIcon from '@mui/icons-material/Edit';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import { Link as RouterLink } from 'react-router-dom';
import heroVideo from '../assets/videos/flow.mp4';
import t1 from '../assets/templates/t1.jpg';
import t2 from '../assets/templates/t2.jpg';
import t3 from '../assets/templates/t3.jpg';
import t4 from '../assets/templates/t4.jpg';
import t5 from '../assets/templates/t5.jpg';

const templateImages = [t1, t2, t3, t4, t5];

// 使用本地视频文件，更稳定
const videoURL = heroVideo;
// 如果你有 VR 少年的视频，请命名为 splash.mp4 放入 frontend/src/assets/videos/ 目录，然后在这里引用
const splashVideoURL = heroVideo; 

import apiClient from '../api/client';

// ... (existing imports)

const HomePage: React.FC = () => {
    const theme = useTheme();
    const [showSplash, setShowSplash] = useState(() => {
        return !sessionStorage.getItem('hasSeenSplash');
    });
    const [onlineTemplates, setOnlineTemplates] = useState<any[]>([]);

    useEffect(() => {
        // Splash Timer
        if (showSplash) {
            const timer = setTimeout(() => {
                setShowSplash(false);
                sessionStorage.setItem('hasSeenSplash', 'true');
            }, 2500); // 2.5s display time
            return () => clearTimeout(timer);
        }

        // Fetch templates (run once on mount, regardless of splash)
        const fetchTemplates = async () => {
            try {
                const res = await apiClient.get('/api/templates/featured');
                if (res.data && res.data.templates && res.data.templates.length > 0) {
                    setOnlineTemplates(res.data.templates);
                }
            } catch (e) {
                console.warn("Failed to fetch online templates, using fallback.");
            }
        };
        fetchTemplates();
    }, [showSplash]);

    const handleSplashClick = () => {
        setShowSplash(false);
        sessionStorage.setItem('hasSeenSplash', 'true');
    };
    
    const cardHoverEffect = {
        scale: 1.05,
        rotateX: 5,
        rotateY: -5,
        transition: { type: 'spring', stiffness: 300 },
    } as const;

    if (showSplash) {
        return (
            <Box
                sx={{
                    position: 'fixed',
                    top: 0, left: 0, right: 0, bottom: 0,
                    backgroundColor: '#000',
                    zIndex: 9999,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    overflow: 'hidden'
                }}
                onClick={handleSplashClick}
            >
                <video
                    autoPlay
                    muted
                    loop
                    playsInline
                                            style={{
                                                position: 'absolute',
                                                width: '100%',
                                                height: '100%',
                                                objectFit: 'cover',
                                                opacity: 0.8
                                            }}                >
                    <source src={splashVideoURL} type="video/mp4" />
                </video>
                
                <Box sx={{ position: 'relative', overflow: 'hidden', zIndex: 2 }}>
                    <motion.div
                        initial={{ y: 100, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ duration: 1, ease: [0.6, 0.01, -0.05, 0.9] }}
                    >
                        <Typography variant="h1" sx={{ 
                            fontWeight: 900, 
                            color: '#fff', 
                            fontSize: { xs: '4rem', md: '10rem' },
                            letterSpacing: '-0.05em',
                            lineHeight: 0.9,
                            textShadow: '0 10px 30px rgba(0,0,0,0.5)'
                        }}>
                            ORENIX
                        </Typography>
                    </motion.div>
                    <motion.div
                        initial={{ y: 100, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ duration: 1, delay: 0.1, ease: [0.6, 0.01, -0.05, 0.9] }}
                    >
                        <Typography variant="h1" sx={{ 
                            fontWeight: 900, 
                            color: 'transparent', 
                            WebkitTextStroke: '2px #fff',
                            fontSize: { xs: '4rem', md: '10rem' },
                            letterSpacing: '-0.05em',
                            lineHeight: 0.9,
                            opacity: 0.8
                        }}>
                            AI LABS
                        </Typography>
                    </motion.div>
                </Box>
            </Box>
        );
    }

        return (
            <Box sx={{ overflow: 'hidden', bgcolor: 'background.default', minHeight: '100vh' }}>
                    {/* Hero Section with Video Background */}
                    <Box                            sx={{
                                position: 'relative',
                                height: '100vh',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                textAlign: 'center',
                                color: 'common.white',
                                overflow: 'hidden',
                            }}
                            onClick={() => document.getElementById('start-btn')?.click()} // Clicking background triggers button
                        >
                <video
                    autoPlay
                    loop
                    muted
                    style={{
                        position: 'absolute',
                        width: '100%',
                        height: '100%',
                        left: '50%',
                        top: '50%',
                        objectFit: 'cover',
                        transform: 'translate(-50%, -50%)',
                    }}
                >
                    <source src={videoURL} type="video/mp4" />
                </video>
                <Box sx={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', backgroundColor: 'rgba(0, 0, 0, 0.3)' }} />
                
                <Container maxWidth="md" sx={{ position: 'relative', zIndex: 1 }}>
                    <Box>
                        <Typography
                            variant="h1"
                            component="h1"
                            sx={{
                                fontSize: { xs: '3.5rem', md: '6rem' },
                                fontWeight: 800,
                                color: '#fff', // Pure white
                                mb: 2,
                                textShadow: '0 4px 20px rgba(0,0,0,0.5)'
                            }}
                        >
                            Create Stunning Videos
                        </Typography>
                    </Box>
                    <Box>
                        <Typography variant="h5" sx={{ 
                            my: 4, 
                            color: 'rgba(255,255,255,0.9)', 
                            fontWeight: 400, 
                            maxWidth: 600, 
                            mx: 'auto',
                            textShadow: '0 2px 10px rgba(0,0,0,0.5)'
                        }}>
                            Transform your ideas into cinematic reality with our AI-powered video agent.
                        </Typography>
                    </Box>
                    <Box>
                        <Button
                            id="start-btn"
                            component={RouterLink}
                            to="/generate"
                            variant="contained"
                            size="large"
                            endIcon={<PlayArrowIcon />}
                            sx={{
                                borderRadius: '50px',
                                padding: '16px 56px',
                                fontSize: '1.25rem',
                                fontWeight: 700,
                                color: 'rgba(255, 255, 255, 0.9)', // Transparent white text
                                background: 'rgba(255, 255, 255, 0.1)', // Glass background
                                backdropFilter: 'blur(10px)', // Frost effect
                                border: '1px solid rgba(255, 255, 255, 0.3)', // Subtle border
                                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
                                transition: 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                                textTransform: 'none',
                                '&:hover': {
                                    transform: 'scale(1.05) translateY(-2px)',
                                    boxShadow: '0 12px 48px rgba(0, 0, 0, 0.4)',
                                    background: 'rgba(255, 255, 255, 0.2)', // Brighter on hover
                                    borderColor: 'rgba(255, 255, 255, 0.5)',
                                    color: '#fff', // Solid white on hover
                                },
                                '&:active': {
                                    transform: 'scale(0.98)',
                                    boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
                                }
                            }}
                        >
                            Create
                        </Button>
                    </Box>
                </Container>
            </Box>

            {/* How it Works Section */}
            <Box sx={{ py: 16, bgcolor: '#020202' }}>
                <Container>
                    <Typography variant="h2" textAlign="center" sx={{ mb: 10, fontWeight: 800, letterSpacing: '-0.02em', color: '#fff' }}>
                        How It Works
                    </Typography>
                    <Grid container spacing={6}>
                        {[
                            { icon: <HowToRegIcon sx={{ fontSize: 48 }} />, title: '1. Describe', description: 'Enter your video concept, style, and requirements.' },
                            { icon: <EditIcon sx={{ fontSize: 48 }} />, title: '2. Generate', description: 'AI agents write the script, direct shots, and render video.' },
                            { icon: <RocketLaunchIcon sx={{ fontSize: 48 }} />, title: '3. Launch', description: 'Export your masterpiece and share it with the world.' },
                        ].map((step, index) => (
                            <Grid item xs={12} md={4} key={index}>
                                <Box sx={{ height: '100%' }}>
                                    <Card sx={{ 
                                        textAlign: 'center', 
                                        p: 5, 
                                        height: '100%', 
                                        display: 'flex', 
                                        flexDirection: 'column', 
                                        alignItems: 'center',
                                        bgcolor: '#0a0a0a', // Darker card
                                        border: '1px solid #222', // Subtle border
                                        borderRadius: 8,
                                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                        '&:hover': {
                                            transform: 'translateY(-8px)',
                                            borderColor: '#444',
                                            boxShadow: '0 20px 40px -10px rgba(0,0,0,0.5)'
                                        }
                                    }}>
                                        <Box sx={{ 
                                            color: '#fff', 
                                            mb: 4,
                                            p: 2,
                                            borderRadius: '50%',
                                            background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.2)} 0%, ${alpha(theme.palette.secondary.main, 0.2)} 100%)`,
                                            display: 'flex', alignItems: 'center', justifyContent: 'center'
                                        }}>
                                            {step.icon}
                                        </Box>
                                        <CardContent sx={{ p: 0 }}>
                                            <Typography variant="h4" sx={{ mb: 2, fontWeight: 700, fontSize: '1.5rem' }}>{step.title}</Typography>
                                            <Typography variant="body1" color="#888" sx={{ lineHeight: 1.8, fontSize: '1.1rem' }}>{step.description}</Typography>
                                        </CardContent>
                                    </Card>
                                </Box>
                            </Grid>
                        ))}
                    </Grid>
                </Container>
            </Box>

            {/* Featured Templates Section */}
            <Box sx={{ py: 16, bgcolor: '#050505' }}>
                <Container>
                    <Typography variant="h2" textAlign="center" sx={{ mb: 10, fontWeight: 800, letterSpacing: '-0.02em', color: '#fff' }}>
                        Featured Templates
                    </Typography>
                    <Box sx={{ 
                        display: 'flex', 
                        overflowX: 'auto', 
                        pb: 4, 
                        gap: 4, 
                        px: 2,
                        '&::-webkit-scrollbar': { height: 8 },
                        '&::-webkit-scrollbar-thumb': { backgroundColor: '#333', borderRadius: 4 },
                        '&::-webkit-scrollbar-track': { backgroundColor: '#111' }
                    }}>
                        {(onlineTemplates.length > 0 ? onlineTemplates : [1, 2, 3, 4, 5]).map((item, index) => {
                            const isOnline = onlineTemplates.length > 0;
                            const id = isOnline ? item.id : item;
                            const bgUrl = isOnline ? item.thumbnail : templateImages[index];
                            const title = isOnline ? item.title : `Template ${id}`;
                            
                            return (
                            <motion.div key={id} whileHover={cardHoverEffect} style={{ flex: '0 0 320px' }}>
                                <Card sx={{ 
                                    background: 'transparent', 
                                    boxShadow: 'none',
                                    border: 'none',
                                    overflow: 'visible'
                                }}>
                                    <Box sx={{ 
                                        height: 450, // Taller cards
                                        background: `url(${bgUrl})`, 
                                        backgroundSize: 'cover', 
                                        backgroundPosition: 'center',
                                        borderRadius: 6,
                                        mb: 3,
                                        boxShadow: '0 20px 40px rgba(0,0,0,0.5)',
                                        position: 'relative',
                                        overflow: 'hidden',
                                        border: '1px solid #333'
                                    }}>
                                        <Box sx={{ 
                                            position: 'absolute', 
                                            bottom: 0, left: 0, right: 0, 
                                            background: 'linear-gradient(to top, rgba(0,0,0,0.95), transparent)',
                                            p: 4,
                                            pt: 12
                                        }}>
                                            <Typography variant="h4" fontWeight={700} sx={{
                                                overflow: 'hidden',
                                                textOverflow: 'ellipsis',
                                                display: '-webkit-box',
                                                WebkitLineClamp: 2,
                                                WebkitBoxOrient: 'vertical',
                                                mb: 1,
                                                fontSize: '1.5rem'
                                            }}>{title}</Typography>
                                            <Typography variant="body1" color="#aaa">Cinematic • 4K</Typography>
                                        </Box>
                                    </Box>
                                </Card>
                            </motion.div>
                        )})}
                    </Box>
                </Container>
            </Box>

            {/* Footer */}
            <Box sx={{ 
                bgcolor: '#050a14', 
                borderTop: '1px solid rgba(255,255,255,0.05)',
                pt: 8,
                pb: 4
            }}>
                <Container maxWidth="lg">
                    {/* ... (Existing Footer Content) ... */}
                    <Grid container spacing={4} justifyContent="space-between">
                        <Grid item xs={12} md={4}>
                            <Typography variant="h5" fontWeight={700} gutterBottom sx={{ 
                                background: `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.secondary.main} 90%)`,
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                                mb: 2
                            }}>
                                Orenix AI
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 300, lineHeight: 1.8 }}>
                                Next-generation AI video creation platform. Transform your ideas into cinematic reality with the power of generative AI.
                            </Typography>
                        </Grid>
                        <Grid item xs={12} md={4}>
                            <Typography variant="subtitle1" fontWeight={700} color="white" gutterBottom>
                                Contact
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                Email: xikangsong@orenixai.com
                            </Typography>
                        </Grid>
                        <Grid item xs={12} md={4}>
                            <Typography variant="subtitle1" fontWeight={700} color="white" gutterBottom>
                                Infrastructure
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                <Typography variant="body2" color="text.secondary">
                                    Building on
                                </Typography>
                                <Typography variant="body2" color="#4285F4" fontWeight={600}>
                                    Google Cloud Vertex AI
                                </Typography>
                            </Box>
                            <Typography variant="caption" color="text.secondary" display="block">
                                Enterprise-grade security and scalability.
                            </Typography>
                        </Grid>
                    </Grid>
                    
                    <Box sx={{ 
                        mt: 8, 
                        pt: 4, 
                        borderTop: '1px solid rgba(255,255,255,0.05)',
                        display: 'flex',
                        flexDirection: { xs: 'column', md: 'row' },
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        gap: 2
                    }}>
                        <Typography variant="caption" color="text.secondary">
                            © 2026 Orenix AI. All rights reserved.
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 3 }}>
                            <RouterLink to="/team" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center' }}>
                                <Typography variant="caption" color="text.secondary" sx={{ '&:hover': { color: 'white' } }}>Team</Typography>
                            </RouterLink>
                            <Typography variant="caption" color="text.secondary" sx={{ cursor: 'pointer', '&:hover': { color: 'white' } }}>Privacy Policy</Typography>
                            <Typography variant="caption" color="text.secondary" sx={{ cursor: 'pointer', '&:hover': { color: 'white' } }}>Terms of Service</Typography>
                        </Box>
                    </Box>
                </Container>
            </Box>
        </Box>
    );
};

export default HomePage;
