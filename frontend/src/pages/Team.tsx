import React from 'react';
import { Box, Container, Typography, Grid, Card, CardContent, Avatar, Chip, Stack, IconButton, useTheme, alpha } from '@mui/material';
import { motion } from 'framer-motion';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import GitHubIcon from '@mui/icons-material/GitHub';
import EmailIcon from '@mui/icons-material/Email';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import WorkIcon from '@mui/icons-material/Work';
import avatarImage from '../assets/team/avatar.jpg';

const TeamPage: React.FC = () => {
    const theme = useTheme();

    const teamMembers = [
        {
            name: "Xikang Song",
            role: "Founder & Lead Algorithm Expert",
            bio: "A visionary AI architect bridging the gap between cutting-edge algorithms and human creativity. Formerly a core Algorithm Expert at Mobvoi, Xikang has spearheaded developments in multimodal interaction and generative AI. His passion lies in democratizing AIGC technologies, building intelligent systems that understand intent, and empowering creators to bring their wildest ideas to life.",
            tags: ["AIGC", "LLM", "Computer Vision", "Multimodal AI"],
            avatar: avatarImage,
            links: {
                github: "https://github.com",
                linkedin: "https://linkedin.com",
                email: "mailto:xikangsong@orenixai.com"
            }
        }
    ];

    return (
        <Box sx={{ 
            minHeight: '100vh', 
            bgcolor: '#050a14',
            pt: '80px',
            pb: 8,
            color: 'white',
            overflow: 'hidden'
        }}>
            {/* Background Elements */}
            <Box sx={{
                position: 'fixed',
                top: 0, left: 0, right: 0, bottom: 0,
                zIndex: 0,
                background: 'radial-gradient(circle at 80% 20%, rgba(79, 172, 254, 0.1) 0%, transparent 40%), radial-gradient(circle at 20% 80%, rgba(255, 64, 129, 0.05) 0%, transparent 40%)',
                pointerEvents: 'none'
            }} />

            <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
                {/* Header */}
                <Box sx={{ textAlign: 'center', mb: 10 }}>
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8 }}
                    >
                        <Typography variant="overline" sx={{ color: theme.palette.primary.main, letterSpacing: 2, fontWeight: 700 }}>
                            THE MINDS BEHIND ORENIX
                        </Typography>
                        <Typography variant="h2" fontWeight={800} sx={{ 
                            mt: 2,
                            background: 'linear-gradient(to right, #fff, #999)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                        }}>
                            Meet Our Team
                        </Typography>
                        <Typography variant="h6" color="text.secondary" sx={{ mt: 3, maxWidth: 600, mx: 'auto', fontWeight: 300 }}>
                            We are a collective of researchers, engineers, and dreamers dedicated to redefining the future of video creation with Artificial Intelligence.
                        </Typography>
                    </motion.div>
                </Box>

                {/* Team Grid */}
                <Grid container spacing={4} justifyContent="center">
                    {teamMembers.map((member, index) => (
                        <Grid item xs={12} md={8} lg={6} key={index}>
                            <motion.div
                                initial={{ opacity: 0, y: 30 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.2, duration: 0.8 }}
                            >
                                <Card sx={{ 
                                    bgcolor: alpha(theme.palette.background.paper, 0.05),
                                    backdropFilter: 'blur(20px)',
                                    border: `1px solid ${alpha(theme.palette.common.white, 0.1)}`,
                                    borderRadius: 4,
                                    overflow: 'visible',
                                    position: 'relative',
                                    transition: 'all 0.3s ease',
                                    '&:hover': {
                                        transform: 'translateY(-5px)',
                                        boxShadow: `0 20px 40px -10px ${alpha(theme.palette.primary.main, 0.2)}`,
                                        borderColor: alpha(theme.palette.primary.main, 0.3)
                                    }
                                }}>
                                    <CardContent sx={{ p: 4 }}>
                                        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, alignItems: 'flex-start', gap: 3 }}>
                                            {/* Avatar */}
                                            <Box sx={{ position: 'relative' }}>
                                                <Box sx={{
                                                    position: 'absolute',
                                                    inset: -3,
                                                    borderRadius: '50%',
                                                    background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                                                    opacity: 0.5,
                                                    filter: 'blur(8px)'
                                                }} />
                                                <Avatar 
                                                    src={member.avatar} 
                                                    alt={member.name}
                                                    sx={{ 
                                                        width: 100, 
                                                        height: 100, 
                                                        border: '2px solid rgba(255,255,255,0.2)',
                                                        bgcolor: '#1a1a1a'
                                                    }}
                                                />
                                            </Box>

                                            {/* Info */}
                                            <Box sx={{ flex: 1 }}>
                                                <Typography variant="h4" fontWeight={700} gutterBottom>
                                                    {member.name}
                                                </Typography>
                                                <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
                                                    <WorkIcon fontSize="small" sx={{ color: theme.palette.primary.main }} />
                                                    <Typography variant="subtitle1" color="primary.light" fontWeight={600}>
                                                        {member.role}
                                                    </Typography>
                                                </Stack>
                                                
                                                <Typography variant="body1" color="text.secondary" sx={{ mb: 3, lineHeight: 1.7 }}>
                                                    {member.bio}
                                                </Typography>

                                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3 }}>
                                                    {member.tags.map(tag => (
                                                        <Chip 
                                                            key={tag} 
                                                            icon={<AutoAwesomeIcon sx={{ fontSize: 14 }} />}
                                                            label={tag} 
                                                            size="small" 
                                                            sx={{ 
                                                                bgcolor: alpha(theme.palette.common.white, 0.05), 
                                                                color: '#ccc',
                                                                border: '1px solid rgba(255,255,255,0.1)'
                                                            }} 
                                                        />
                                                    ))}
                                                </Box>

                                                <Stack direction="row" spacing={1}>
                                                    <IconButton 
                                                        href={member.links.email} 
                                                        sx={{ 
                                                            color: 'white', 
                                                            bgcolor: alpha(theme.palette.primary.main, 0.1),
                                                            '&:hover': { 
                                                                color: 'white', 
                                                                bgcolor: theme.palette.primary.main,
                                                                transform: 'scale(1.1)'
                                                            },
                                                            transition: 'all 0.2s'
                                                        }}
                                                    >
                                                        <EmailIcon />
                                                    </IconButton>
                                                    <Typography variant="body2" color="text.secondary" sx={{ alignSelf: 'center', ml: 1 }}>
                                                        xikangsong@orenixai.com
                                                    </Typography>
                                                </Stack>
                                            </Box>
                                        </Box>
                                    </CardContent>
                                </Card>
                            </motion.div>
                        </Grid>
                    ))}
                </Grid>

                {/* Join Us Section */}
                <Box sx={{ mt: 10, textAlign: 'center' }}>
                    <Typography variant="h6" color="text.secondary" gutterBottom>
                        Inspired by our vision?
                    </Typography>
                    <Typography variant="h4" fontWeight={700} sx={{ mb: 3 }}>
                        Join us in shaping the future.
                    </Typography>
                </Box>
            </Container>
        </Box>
    );
};

export default TeamPage;
