import React from 'react';
import { Box, Typography, Button, Grid, Card, CardContent, Container, useTheme, alpha } from '@mui/material';
import { motion } from 'framer-motion';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import HowToRegIcon from '@mui/icons-material/HowToReg';
import EditIcon from '@mui/icons-material/Edit';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import { Link as RouterLink } from 'react-router-dom';

// Video background URL (Royalty-free from Pexels)
const videoURL = "https://videos.pexels.com/video-files/3209828/3209828-hd_1920_1080_25fps.mp4";

const HomePage: React.FC = () => {
    const theme = useTheme();

    const heroVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: {
            opacity: 1,
            y: 0,
            transition: {
                staggerChildren: 0.3,
                delayChildren: 1.5, // Increased delay
            },
        },
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.8 } },
    };
    
    const cardHoverEffect = {
        scale: 1.05,
        rotateX: 5,
        rotateY: -5,
        transition: { type: 'spring', stiffness: 300 },
    } as const;

    return (
        <Box sx={{ overflow: 'hidden', bgcolor: 'background.default' }}>
            {/* Hero Section with Video Background */}
            <Box
                component={motion.div}
                variants={heroVariants}
                initial="hidden"
                animate="visible"
                sx={{
                    position: 'relative',
                    height: '100vh',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    textAlign: 'center',
                    color: 'common.white',
                    overflow: 'hidden',
                    cursor: 'pointer' // Make cursor indicate clickability
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
                        zIndex: -2,
                    }}
                >
                    <source src={videoURL} type="video/mp4" />
                </video>
                <Box sx={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', backgroundColor: 'rgba(0, 0, 0, 0.7)', zIndex: -1 }} />
                
                <Container maxWidth="md">
                    <motion.div variants={itemVariants}>
                        <Typography
                            variant="h1"
                            component="h1"
                            sx={{
                                fontSize: { xs: '3.5rem', md: '6rem' },
                                fontWeight: 800,
                                background: `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.secondary.main} 90%)`,
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                                mb: 2,
                                textShadow: '0 10px 30px rgba(0,0,0,0.3)'
                            }}
                        >
                            Create Stunning Videos
                        </Typography>
                    </motion.div>
                    <motion.div variants={itemVariants}>
                        <Typography variant="h5" sx={{ my: 4, color: 'text.secondary', fontWeight: 400, maxWidth: 600, mx: 'auto' }}>
                            Transform your ideas into cinematic reality with our AI-powered video agent.
                        </Typography>
                    </motion.div>
                    <motion.div variants={itemVariants}>
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
                                background: `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.secondary.main} 90%)`,
                                boxShadow: '0 8px 32px rgba(255, 64, 129, 0.3)',
                                transition: 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                                textTransform: 'none',
                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                '&:hover': {
                                    transform: 'scale(1.05) translateY(-2px)',
                                    boxShadow: '0 12px 48px rgba(255, 64, 129, 0.5)',
                                    background: `linear-gradient(45deg, ${theme.palette.primary.dark} 30%, ${theme.palette.secondary.dark} 90%)`,
                                },
                                '&:active': {
                                    transform: 'scale(0.98)',
                                    boxShadow: '0 4px 16px rgba(255, 64, 129, 0.3)',
                                }
                            }}
                        >
                            Create
                        </Button>
                    </motion.div>
                </Container>
            </Box>

            {/* How it Works Section */}
            <Box sx={{ py: 12, background: 'radial-gradient(circle at 50% 50%, #1e293b 0%, #0f172a 100%)' }}>
                <Container>
                    <Typography variant="h2" textAlign="center" sx={{ mb: 8, fontWeight: 700 }}>How It Works</Typography>
                    <Grid container spacing={6}>
                        {[
                            { icon: <HowToRegIcon sx={{ fontSize: 40 }} />, title: '1. Describe', description: 'Enter your video concept, style, and requirements.' },
                            { icon: <EditIcon sx={{ fontSize: 40 }} />, title: '2. Generate', description: 'AI agents write the script, direct shots, and render video.' },
                            { icon: <RocketLaunchIcon sx={{ fontSize: 40 }} />, title: '3. Launch', description: 'Export your masterpiece and share it with the world.' },
                        ].map((step, index) => (
                            <Grid item xs={12} md={4} key={index}>
                                <motion.div initial={{ opacity: 0, y: 50 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.5 }} transition={{ delay: index * 0.2 }}>
                                    <Card sx={{ 
                                        textAlign: 'center', 
                                        p: 4, 
                                        height: '100%', 
                                        display: 'flex', 
                                        flexDirection: 'column', 
                                        alignItems: 'center',
                                        background: alpha(theme.palette.background.paper, 0.5),
                                        backdropFilter: 'blur(10px)',
                                        border: `1px solid ${alpha(theme.palette.common.white, 0.05)}`
                                    }}>
                                        <Box sx={{ 
                                            color: 'primary.main', 
                                            mb: 3,
                                            p: 3,
                                            borderRadius: '50%',
                                            backgroundColor: alpha(theme.palette.primary.main, 0.1)
                                        }}>
                                            {step.icon}
                                        </Box>
                                        <CardContent>
                                            <Typography variant="h5" sx={{ mb: 2, fontWeight: 600 }}>{step.title}</Typography>
                                            <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.6 }}>{step.description}</Typography>
                                        </CardContent>
                                    </Card>
                                </motion.div>
                            </Grid>
                        ))}
                    </Grid>
                </Container>
            </Box>

            {/* Featured Templates Section */}
            <Box sx={{ py: 12, bgcolor: '#0f172a' }}>
                <Container>
                    <Typography variant="h2" textAlign="center" sx={{ mb: 8, fontWeight: 700 }}>Featured Templates</Typography>
                    <Box sx={{ 
                        display: 'flex', 
                        overflowX: 'auto', 
                        pb: 4, 
                        gap: 4, 
                        px: 2,
                        '&::-webkit-scrollbar': { height: 8 },
                        '&::-webkit-scrollbar-thumb': { backgroundColor: alpha(theme.palette.common.white, 0.1), borderRadius: 4 }
                    }}>
                        {[1, 2, 3, 4, 5].map((id) => (
                            <motion.div key={id} whileHover={cardHoverEffect} style={{ flex: '0 0 320px' }}>
                                <Card sx={{ 
                                    background: 'transparent', 
                                    boxShadow: 'none',
                                    border: 'none',
                                    overflow: 'visible'
                                }}>
                                    <Box sx={{ 
                                        height: 400, 
                                        background: `url(https://picsum.photos/600/800?random=${id})`, 
                                        backgroundSize: 'cover', 
                                        backgroundPosition: 'center',
                                        borderRadius: 4,
                                        mb: 2,
                                        boxShadow: '0 20px 40px rgba(0,0,0,0.5)',
                                        position: 'relative',
                                        overflow: 'hidden'
                                    }}>
                                        <Box sx={{ 
                                            position: 'absolute', 
                                            bottom: 0, left: 0, right: 0, 
                                            background: 'linear-gradient(to top, rgba(0,0,0,0.9), transparent)',
                                            p: 3
                                        }}>
                                            <Typography variant="h5" fontWeight={700}>Template {id}</Typography>
                                            <Typography variant="body2" color="rgba(255,255,255,0.7)">Cinematic • 60s</Typography>
                                        </Box>
                                    </Box>
                                </Card>
                            </motion.div>
                        ))}
                    </Box>
                </Container>
            </Box>
        </Box>
    );
};

export default HomePage;
