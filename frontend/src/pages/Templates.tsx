import React, { useState } from 'react';
import { 
    Card, 
    CardContent, 
    Typography, 
    Grid, 
    Container, 
    Box, 
    Chip, 
    Tabs, 
    Tab,
    useTheme,
    alpha,
    CardActionArea
} from '@mui/material';
import { 
    PlayArrow as PlayIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

// Mock Data
const CATEGORIES = ['All', 'Business', 'Social Media', 'Education', 'Entertainment'];

const TEMPLATES = [
    { id: 1, title: 'Product Launch', category: 'Business', duration: 60, color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', desc: 'Perfect for introducing new products.' },
    { id: 2, title: 'TikTok Viral', category: 'Social Media', duration: 30, color: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%)', desc: 'Fast-paced, engaging style.' },
    { id: 3, title: 'Course Intro', category: 'Education', duration: 120, color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', desc: 'Clean and informative.' },
    { id: 4, title: 'Company Story', category: 'Business', duration: 90, color: 'linear-gradient(135deg, #434343 0%, #000000 100%)', desc: 'Cinematic documentary style.' },
    { id: 5, title: 'Travel Vlog', category: 'Entertainment', duration: 180, color: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', desc: 'Bright colors and upbeat transitions.' },
    { id: 6, title: 'Tech Review', category: 'Social Media', duration: 300, color: 'linear-gradient(135deg, #000428 0%, #004e92 100%)', desc: 'Futuristic and detailed.' },
];

const TemplatesPage: React.FC = () => {
    const theme = useTheme();
    const navigate = useNavigate();
    const [selectedCategory, setSelectedCategory] = useState('All');

    const handleTemplateSelect = () => {
        // In a real app, pass template data via state or URL param
        navigate('/generate');
    };

    const filteredTemplates = selectedCategory === 'All' 
        ? TEMPLATES 
        : TEMPLATES.filter(t => t.category === selectedCategory);

    return (
        <Box sx={{ 
            minHeight: '100vh', 
            background: 'radial-gradient(circle at 50% 10%, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
            pt: '80px',
            pb: 8,
            px: { xs: 2, md: 4 },
            color: 'white'
        }}>
            <Container maxWidth="xl">
                {/* Hero */}
                <Box sx={{ textAlign: 'center', mb: 8 }}>
                    <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
                        <Typography variant="h2" fontWeight={800} gutterBottom sx={{ 
                             background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)',
                             WebkitBackgroundClip: 'text',
                             WebkitTextFillColor: 'transparent',
                        }}>
                            Start with a Template
                        </Typography>
                        <Typography variant="h5" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto', mb: 4 }}>
                            Jumpstart your creation process with professionally designed scripts and styles.
                        </Typography>
                    </motion.div>

                    {/* Category Tabs */}
                    <Tabs 
                        value={selectedCategory} 
                        onChange={(_, v) => setSelectedCategory(v)} 
                        centered
                        sx={{
                            '& .MuiTabs-indicator': { backgroundColor: 'primary.main' },
                            '& .MuiTab-root': { color: 'text.secondary', '&.Mui-selected': { color: 'white' } }
                        }}
                    >
                        {CATEGORIES.map(cat => (
                            <Tab key={cat} label={cat} value={cat} />
                        ))}
                    </Tabs>
                </Box>

                {/* Grid */}
                <Grid container spacing={4}>
                    {filteredTemplates.map((template) => (
                        <Grid item key={template.id} xs={12} sm={6} md={4} lg={3}>
                            <motion.div 
                                layout
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ duration: 0.2 }}
                            >
                                <Card sx={{ 
                                    height: '100%', 
                                    background: alpha(theme.palette.background.paper, 0.4),
                                    backdropFilter: 'blur(10px)',
                                    border: `1px solid ${alpha(theme.palette.common.white, 0.1)}`,
                                    borderRadius: 4,
                                    overflow: 'hidden',
                                    transition: 'all 0.3s',
                                    '&:hover': {
                                        transform: 'translateY(-8px)',
                                        boxShadow: `0 20px 40px -10px ${alpha(theme.palette.common.black, 0.5)}`
                                    }
                                }}>
                                    <CardActionArea onClick={() => handleTemplateSelect()} sx={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'stretch' }}>
                                        {/* Thumbnail / Gradient Placeholder */}
                                        <Box sx={{ 
                                            height: 180, 
                                            background: template.color,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            position: 'relative'
                                        }}>
                                            <Box sx={{ 
                                                width: 60, height: 60, borderRadius: '50%', 
                                                bgcolor: 'rgba(0,0,0,0.3)', 
                                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                backdropFilter: 'blur(5px)'
                                            }}>
                                                <PlayIcon sx={{ color: 'white', fontSize: 30 }} />
                                            </Box>
                                            <Chip 
                                                label={template.category} 
                                                size="small" 
                                                sx={{ 
                                                    position: 'absolute', 
                                                    top: 16, 
                                                    right: 16, 
                                                    bgcolor: 'rgba(0,0,0,0.6)', 
                                                    backdropFilter: 'blur(4px)',
                                                    color: 'white' 
                                                }} 
                                            />
                                        </Box>

                                        <CardContent sx={{ flexGrow: 1, p: 3 }}>
                                            <Typography variant="h6" fontWeight={700} gutterBottom>
                                                {template.title}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                                {template.desc}
                                            </Typography>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Typography variant="caption" sx={{ color: 'primary.light', fontWeight: 600 }}>
                                                    {template.duration}s
                                                </Typography>
                                                <Typography variant="caption" color="text.secondary">•</Typography>
                                                <Typography variant="caption" color="text.secondary">
                                                    Professional
                                                </Typography>
                                            </Box>
                                        </CardContent>
                                    </CardActionArea>
                                </Card>
                            </motion.div>
                        </Grid>
                    ))}
                </Grid>
            </Container>
        </Box>
    );
};

export default TemplatesPage;
