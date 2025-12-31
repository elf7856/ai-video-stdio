import React, { useState } from 'react';
import {
    Button, TextField, Typography, Container, Grid, Paper, Box,
    Select, MenuItem, FormControl, InputLabel, CircularProgress,
    Alert, Card, CardMedia, CardContent, CardActions
} from '@mui/material';
import { Image as ImageIcon, Download as DownloadIcon } from '@mui/icons-material';
import { imagesApi } from '../api';
import type { ImageGenerationRequest, ImageGenerationResponse } from '../api/types';

const ImageGeneratePage: React.FC = () => {
    const [prompt, setPrompt] = useState('');
    const [provider, _setProvider] = useState<string>('google_imagen');
    const [aspectRatio, setAspectRatio] = useState<string>('16:9');
    const [resolution, setResolution] = useState<string>('medium');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ImageGenerationResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [imageUrl, setImageUrl] = useState<string | null>(null);

    const handleGenerate = async () => {
        if (!prompt.trim()) {
            setError('请输入图像描述');
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null);
        setImageUrl(null);

        try {
            const request: ImageGenerationRequest = {
                prompt: prompt.trim(),
                provider: provider as any,
                aspectRatio: aspectRatio as any,
                resolution: resolution as any
            };

            const response = await imagesApi.generateImage(request);
            setResult(response);

            if (response.success && response.imagePath) {
                const url = imagesApi.getImageUrl(response.imagePath);
                setImageUrl(url);
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || '生成失败');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
            <Box sx={{ mb: 4 }}>
                <Typography variant="h4" component="h1" gutterBottom>
                    <ImageIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    AI图像生成
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    使用Google Imagen 3生成高质量图像
                </Typography>
            </Box>

            <Grid container spacing={4}>
                <Grid item xs={12} md={5}>
                    <Paper sx={{ p: 3 }}>
                        <TextField
                            label="图像描述"
                            placeholder="例如：一个美丽的日落山景"
                            fullWidth
                            margin="normal"
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            multiline
                            rows={3}
                        />

                        <FormControl fullWidth margin="normal">
                            <InputLabel>宽高比</InputLabel>
                            <Select value={aspectRatio} label="宽高比" onChange={(e) => setAspectRatio(e.target.value)}>
                                <MenuItem value="1:1">1:1 (正方形)</MenuItem>
                                <MenuItem value="16:9">16:9 (宽屏)</MenuItem>
                                <MenuItem value="9:16">9:16 (竖屏)</MenuItem>
                                <MenuItem value="4:3">4:3 (标准)</MenuItem>
                                <MenuItem value="3:4">3:4 (竖向)</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth margin="normal">
                            <InputLabel>分辨率</InputLabel>
                            <Select value={resolution} label="分辨率" onChange={(e) => setResolution(e.target.value)}>
                                <MenuItem value="low">低</MenuItem>
                                <MenuItem value="medium">中</MenuItem>
                                <MenuItem value="high">高</MenuItem>
                            </Select>
                        </FormControl>

                        <Button
                            variant="contained"
                            fullWidth
                            size="large"
                            onClick={handleGenerate}
                            disabled={loading || !prompt.trim()}
                            sx={{ mt: 3 }}
                        >
                            {loading ? <><CircularProgress size={24} sx={{ mr: 1 }} />生成中...</> : '生成图像'}
                        </Button>

                        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
                    </Paper>
                </Grid>

                <Grid item xs={12} md={7}>
                    {!imageUrl && !loading && (
                        <Box sx={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center',
                            backgroundColor: 'grey.100', borderRadius: 2, border: '2px dashed', borderColor: 'grey.300' }}>
                            <Typography variant="h6" color="text.secondary">图像将显示在这里</Typography>
                        </Box>
                    )}

                    {loading && (
                        <Box sx={{ height: 400, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                            <CircularProgress size={60} />
                            <Typography variant="h6" sx={{ mt: 2 }}>AI正在生成图像...</Typography>
                        </Box>
                    )}

                    {imageUrl && (
                        <Card>
                            <CardMedia component="img" image={imageUrl} alt="Generated image" sx={{ maxHeight: 500, objectFit: 'contain' }} />
                            <CardContent>
                                <Typography variant="body2" color="text.secondary">
                                    提供商: {result?.provider || 'Google Imagen'}
                                </Typography>
                            </CardContent>
                            <CardActions>
                                <Button startIcon={<DownloadIcon />} onClick={() => window.open(imageUrl, '_blank')}>
                                    下载图像
                                </Button>
                            </CardActions>
                        </Card>
                    )}
                </Grid>
            </Grid>
        </Container>
    );
};

export default ImageGeneratePage;
